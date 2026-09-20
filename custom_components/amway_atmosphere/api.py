"""Amway Atmosphere API Client with OAuth2 and AWS IoT Shadow dispatch."""

from __future__ import annotations

import datetime
from dataclasses import dataclass, field
import hashlib
import hmac
import json
import logging
from typing import Any, Dict, List, Optional
import urllib.parse
import uuid

import aiohttp

from .const import (
    ACCOUNT2_TOKEN_URL,
    AMWAY_API_KEY,
    AMWAY_PASSWORD_SALT,
    AWS_IOT_ENDPOINT,
    AWS_REGION,
    CLIENT_ID,
    CLIENT_SECRET,
    CONEX_BASE_URL,
    DEFAULT_COUNTRY,
    DEFAULT_NAME_MINI,
    DEFAULT_NAME_SKY,
    DEFAULT_SCOPES,
    AUTH_ENDPOINT,
    GLUU_AUTH_ENDPOINT,
    GLUU_TOKEN_ENDPOINT,
    MODEL_MINI,
    MODEL_SKY,
    REDIRECT_URI,
)

_LOGGER = logging.getLogger(__name__)


def normalize_username(username: str, country: str = "TW") -> str:
    """Normalize phone numbers or usernames to international format."""
    cleaned = username.strip().replace(" ", "").replace("-", "")
    if country.upper() == "TW":
        if cleaned.startswith("09") and len(cleaned) == 10:
            return f"+886{cleaned[1:]}"
        if cleaned.startswith("9") and len(cleaned) == 9:
            return f"+886{cleaned}"
        if cleaned.startswith("886") and not cleaned.startswith("+"):
            return f"+{cleaned}"
    return cleaned


def _sign(key: bytes, msg: str) -> bytes:
    return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()


def sign_aws_v4(
    method: str,
    url: str,
    region: str,
    service: str,
    access_key: str,
    secret_key: str,
    session_token: Optional[str],
    payload: bytes,
    headers: Dict[str, str],
    now: Optional[datetime.datetime] = None,
) -> Dict[str, str]:
    """Calculate AWS Signature Version 4 headers."""
    if now is None:
        now = datetime.datetime.now(datetime.timezone.utc)
    amz_date = now.strftime("%Y%m%dT%H%M%SZ")
    date_stamp = now.strftime("%Y%m%d")

    parsed_url = urllib.parse.urlparse(url)
    canonical_uri = parsed_url.path or "/"
    canonical_querystring = parsed_url.query

    signed_headers_map = {k.lower(): v.strip() for k, v in headers.items()}
    signed_headers_map["host"] = parsed_url.netloc
    signed_headers_map["x-amz-date"] = amz_date
    if session_token:
        signed_headers_map["x-amz-security-token"] = session_token

    payload_hash = hashlib.sha256(payload).hexdigest()
    signed_headers_map["x-amz-content-sha256"] = payload_hash

    # Sorted canonical headers
    sorted_header_keys = sorted(signed_headers_map.keys())
    canonical_headers = (
        "".join(f"{k}:{signed_headers_map[k]}\n" for k in sorted_header_keys)
    )
    signed_headers = ";".join(sorted_header_keys)

    canonical_request = (
        f"{method}\n"
        f"{canonical_uri}\n"
        f"{canonical_querystring}\n"
        f"{canonical_headers}\n"
        f"{signed_headers}\n"
        f"{payload_hash}"
    )

    credential_scope = f"{date_stamp}/{region}/{service}/aws4_request"
    string_to_sign = (
        f"AWS4-HMAC-SHA256\n"
        f"{amz_date}\n"
        f"{credential_scope}\n"
        f"{hashlib.sha256(canonical_request.encode('utf-8')).hexdigest()}"
    )

    k_date = _sign(f"AWS4{secret_key}".encode("utf-8"), date_stamp)
    k_region = _sign(k_date, region)
    k_service = _sign(k_region, service)
    k_signing = _sign(k_service, "aws4_request")
    signature = hmac.new(
        k_signing, string_to_sign.encode("utf-8"), hashlib.sha256
    ).hexdigest()

    auth_header = (
        f"AWS4-HMAC-SHA256 Credential={access_key}/{credential_scope}, "
        f"SignedHeaders={signed_headers}, Signature={signature}"
    )

    final_headers = dict(signed_headers_map)
    final_headers["authorization"] = auth_header
    return final_headers


@dataclass
class AtmosphereDeviceState:
    """Represents normalized state of an Atmosphere purifier."""

    thing_id: str
    thing_type: str  # "Sky" or "Mini"
    device_name: str = ""
    connected: bool = True
    speed: int = 0  # 0 = Off, 1..5 for Sky, 1..3 for Mini
    dust_level: int = 1  # 1..5
    mode: Optional[int] = None
    clean_air_val: Optional[int] = None
    prefilter_life_left: Optional[int] = None  # 0..100%
    hepa_life_left: Optional[int] = None  # 0..100%
    carbon_life_left: Optional[int] = None  # 0..100% (Sky only)
    child_lock: Optional[bool] = None
    raw_shadow: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Ensure device_name is the official full model name."""
        if not self.device_name:
            self.device_name = DEFAULT_NAME_MINI if self.is_mini else DEFAULT_NAME_SKY

    @property
    def is_sky(self) -> bool:
        t = (self.thing_type or "").lower()
        return t == "sky" or t == "neptune"

    @property
    def is_mini(self) -> bool:
        return "mini" in (self.thing_type or "").lower()

    @property
    def max_speed(self) -> int:
        return 5 if self.is_sky else 3


class AmwayApiClient:
    """API client for Conex API and AWS IoT Device Shadow updates."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        access_token: str,
        refresh_token: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        country: str = DEFAULT_COUNTRY,
        on_token_refreshed: Optional[Any] = None,
    ) -> None:
        self._session = session
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.username = username
        self.password = password
        self.country = country
        self._on_token_refreshed = on_token_refreshed
        self._aws_credentials: Optional[Dict[str, Any]] = None
        self._aws_credentials_expires_at: Optional[datetime.datetime] = None

    @classmethod
    def get_authorization_url(
        cls, state: str = "amway_ha", country: str = "TW"
    ) -> str:
        """Generate the official Amway consumer login portal URL.

        ⚠️ NOTE: Never use gluu-prod01-prod.../oxauth/restv1/authorize.
        That is the internal green LDAP page. The real consumer portal is account2.amwayglobal.com.
        """
        market = country.lower()
        if market == "tw":
            lang = "zh-tw"
            clientapp = "healthyhomeTW"
        elif market == "jp":
            lang = "ja-jp"
            clientapp = "healthyhomeJP"
        else:
            lang = "en-us"
            clientapp = f"healthyhome{country.upper()}"

        params = {
            "client_id": CLIENT_ID,
            "response_type": "code",
            "redirect_uri": REDIRECT_URI,
            "scope": DEFAULT_SCOPES,
            "prompt": "login",
            "clientapp": clientapp,
            "amw_clientapp": clientapp,
            "amw_lng": "zh_tw" if market == "tw" else ("ja_jp" if market == "jp" else "en_us"),
            "cancelRedirect": "amwayhealthyhome://cancelLogin",
            "state": state,
        }
        return f"{AUTH_ENDPOINT}?{urllib.parse.urlencode(params)}"

    @classmethod
    async def async_login_with_password(
        cls,
        session: aiohttp.ClientSession,
        username: str,
        password: str,
        country: str = DEFAULT_COUNTRY,
    ) -> Dict[str, Any]:
        """Perform direct mobile API authentication using username/phone and password."""
        norm_username = normalize_username(username, country)
        session_id = str(uuid.uuid4())
        j_hash = hashlib.md5(
            (norm_username.lower() + AMWAY_PASSWORD_SALT).encode("utf-8")
        ).hexdigest()

        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "x-amw-clientapp": f"healthyhome{country.upper()}",
            "x-amw-country-app": country.upper(),
            "x-api-key": AMWAY_API_KEY,
            "x-session-id": session_id,
            "j": j_hash,
            "user-agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
            ),
        }
        body = {
            "username": norm_username,
            "iso_country_code": country.upper(),
            "password": password,
        }

        async with session.post(ACCOUNT2_TOKEN_URL, headers=headers, json=body) as resp:
            if resp.status != 200:
                text = await resp.text()
                _LOGGER.error("Amway direct login failed (%s): %s", resp.status, text)
                resp.raise_for_status()
            data = await resp.json()
            session_token = data.get("session_token")
            if not session_token:
                raise ValueError("Response missing session_token")

            gluu_user = data.get("gluuUser", {})
            profile = gluu_user.get("profile", {})
            party_id = profile.get("partyId") or gluu_user.get("partyId")

            return {
                "access_token": session_token,
                "username": norm_username,
                "party_id": party_id,
                "raw_response": data,
            }

    @classmethod
    async def async_exchange_code(
        cls, session: aiohttp.ClientSession, auth_code: str
    ) -> Dict[str, Any]:
        """Exchange the code extracted from loginRedirect callback for tokens."""
        data = {
            "grant_type": "authorization_code",
            "code": auth_code,
            "redirect_uri": REDIRECT_URI,
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "scope": DEFAULT_SCOPES,
        }
        async with session.post(GLUU_TOKEN_ENDPOINT, data=data) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def async_refresh_token(self) -> Dict[str, Any]:
        """Refresh the access token using saved credentials or refresh_token."""
        if self.username and self.password:
            _LOGGER.info("Re-authenticating Amway session via stored credentials...")
            login_res = await self.async_login_with_password(
                self._session, self.username, self.password, self.country
            )
            self.access_token = login_res["access_token"]
            if self._on_token_refreshed:
                await self._on_token_refreshed({
                    "access_token": self.access_token,
                    "refresh_token": self.refresh_token,
                })
            return login_res

        if not self.refresh_token:
            raise ValueError("No refresh_token or credentials available")
        data = {
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token,
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "scope": DEFAULT_SCOPES,
        }
        async with self._session.post(GLUU_TOKEN_ENDPOINT, data=data) as resp:
            resp.raise_for_status()
            tokens = await resp.json()
            self.access_token = tokens["access_token"]
            if "refresh_token" in tokens:
                self.refresh_token = tokens["refresh_token"]
            if self._on_token_refreshed:
                await self._on_token_refreshed(tokens)
            return tokens

    async def _async_conex_request(
        self, method: str, endpoint: str, **kwargs: Any
    ) -> Any:
        """Make an authenticated request to Conex REST API with auto token refresh."""
        url = f"{CONEX_BASE_URL}/{endpoint.lstrip('/')}"
        headers = kwargs.pop("headers", {})
        headers["Authorization"] = f"Bearer {self.access_token}"
        headers["Content-Type"] = "application/json"
        headers["User-Agent"] = "AmwayHealthyHome/20.0.0 (Android)"

        async with self._session.request(method, url, headers=headers, **kwargs) as resp:
            if resp.status == 401 and (self.refresh_token or (self.username and self.password)):
                _LOGGER.info("Conex API 401 Unauthorized; attempting token refresh...")
                await self.async_refresh_token()
                headers["Authorization"] = f"Bearer {self.access_token}"
                async with self._session.request(method, url, headers=headers, **kwargs) as retry_resp:
                    retry_resp.raise_for_status()
                    return await retry_resp.json()
            resp.raise_for_status()
            return await resp.json()

    async def async_get_devices(self) -> List[AtmosphereDeviceState]:
        """Query all things and their shadows from Conex REST API."""
        params = {
            "thingType": "sky,neptune,sky-mini",
            "info": "true",
            "thing": "true",
            "shadow": "true",
        }
        data = await self._async_conex_request("GET", "v1/things", params=params)
        devices: List[AtmosphereDeviceState] = []

        for item in data:
            thing_id = item.get("thingId", "")
            thing_type = item.get("thingType", MODEL_SKY)

            # Do NOT use app names; determine official full device name by model type (Sky vs Mini)
            type_lower = str(thing_type).lower()
            if "mini" in type_lower:
                device_name = DEFAULT_NAME_MINI
            else:
                device_name = DEFAULT_NAME_SKY


            # Parse Shadow
            shadow_obj = item.get("shadow", {}) or {}
            payload_str = shadow_obj.get("payload")
            if isinstance(payload_str, str):
                try:
                    shadow_dict = json.loads(payload_str)
                except Exception:
                    shadow_dict = {}
            elif isinstance(shadow_obj, dict):
                shadow_dict = shadow_obj
            else:
                shadow_dict = {}

            state = shadow_dict.get("state", {})
            reported = state.get("reported", {})

            display = reported.get("display", {}) or {}
            system = reported.get("system", {}) or {}
            custom = system.get("custom", {}) or {}

            # Connected status is stored in reported.system.connected
            connected = system.get("connected")
            if connected is None:
                connected = item.get("connected", True)

            prefilter = reported.get("prefilter", {}) or {}
            hepa = reported.get("hepa", {}) or {}
            carbon = reported.get("carbon", {}) or {}

            device = AtmosphereDeviceState(
                thing_id=thing_id,
                thing_type=thing_type,
                device_name=device_name,
                connected=bool(connected),
                speed=display.get("speed", 0),
                dust_level=display.get("dust", 1),
                mode=custom.get("mode"),
                clean_air_val=custom.get("cleanAirVal"),
                prefilter_life_left=prefilter.get("lifeLeft"),
                hepa_life_left=hepa.get("lifeLeft"),
                carbon_life_left=carbon.get("lifeLeft"),
                child_lock=system.get("childLock"),
                raw_shadow=shadow_dict,
            )
            devices.append(device)

        return devices

    async def async_get_aws_credentials(self) -> Dict[str, Any]:
        """Retrieve STS temporary credentials from Conex API."""
        now = datetime.datetime.now(datetime.timezone.utc)
        if (
            self._aws_credentials
            and self._aws_credentials_expires_at
            and now < self._aws_credentials_expires_at - datetime.timedelta(minutes=5)
        ):
            return self._aws_credentials

        data = await self._async_conex_request("GET", "v1/users/credentials")
        creds = data.get("Credentials", {})
        self._aws_credentials = creds
        expiration_str = creds.get("Expiration")
        if expiration_str:
            try:
                self._aws_credentials_expires_at = datetime.datetime.fromisoformat(
                    expiration_str.replace("Z", "+00:00")
                )
            except Exception:
                self._aws_credentials_expires_at = now + datetime.timedelta(minutes=50)
        else:
            self._aws_credentials_expires_at = now + datetime.timedelta(minutes=50)

        return creds

    async def async_send_remote_button(self, thing_id: str, button_name: str) -> None:
        """Send a RemoteButton command via AWS IoT Data Plane REST API."""
        creds = await self.async_get_aws_credentials()
        access_key = creds["AccessKeyId"]
        secret_key = creds.get("SecretAccessKey") or creds.get("SecretKey")
        session_token = creds.get("SessionToken")

        url = f"https://{AWS_IOT_ENDPOINT}/things/{thing_id}/shadow"
        payload_dict = {"state": {"desired": {"RemoteButton": button_name}}}
        payload_bytes = json.dumps(payload_dict).encode("utf-8")

        initial_headers = {
            "Content-Type": "application/x-amz-json-1.0",
        }

        signed_headers = sign_aws_v4(
            method="POST",
            url=url,
            region=AWS_REGION,
            service="iotdata",
            access_key=access_key,
            secret_key=secret_key,
            session_token=session_token,
            payload=payload_bytes,
            headers=initial_headers,
        )

        _LOGGER.debug(
            "Sending RemoteButton %s to thing %s", button_name, thing_id
        )
        async with self._session.post(
            url, data=payload_bytes, headers=signed_headers
        ) as resp:
            if resp.status >= 400:
                text = await resp.text()
                _LOGGER.error(
                    "AWS IoT Shadow update failed (%s): %s", resp.status, text
                )
                resp.raise_for_status()
