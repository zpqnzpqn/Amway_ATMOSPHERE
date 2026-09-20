"""Amway Atmosphere API Client with OAuth2 and AWS IoT Shadow dispatch."""

from __future__ import annotations

import base64
import datetime
from dataclasses import dataclass, field
import hashlib
import hmac
import json
import logging
import secrets
from typing import Any, Dict, List, Optional, Tuple
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
    GLUU_OXAUTH_ENDPOINT,
    GLUU_TOKEN_ENDPOINT,
    MODEL_MINI,
    MODEL_SKY,
    OFFICIAL_AUTH_PORTAL,
    REDIRECT_URI,
)

_LOGGER = logging.getLogger(__name__)


def generate_pkce() -> Tuple[str, str]:
    """Generate PKCE code_verifier and code_challenge according to RFC 7636."""
    verifier = (
        secrets.token_urlsafe(64)[:64]
        .replace("-", "_")
        .replace("~", "")
        .replace(".", "")
    )
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    challenge = base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")
    return verifier, challenge


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
        """Perform full 5-step Android OAuth2 PKCE + JansKey authentication.

        Replicates the official Amway Healthy Home mobile app flow:
        1. Initiates PKCE OAuth authorization to receive jansKey from Amway Proxy.
        2. Submits credentials to Account2 token endpoint with jnsKey.
        3. Calls oxauth authorization endpoint with jansKey to receive OAuth Authorization Code.
        4. Exchanges authorization code with PKCE code_verifier to receive Conex access_token and refresh_token.
        """
        norm_username = normalize_username(username, country)
        country_code = country.upper()
        market = country.lower()
        if market == "tw":
            lang = "zh-tw"
            client_app = "healthyhomeTW"
        elif market == "jp":
            lang = "ja-jp"
            client_app = "healthyhomeJP"
        else:
            lang = "en-us"
            client_app = f"healthyhome{country_code}"

        # 1. Generate PKCE verifier, challenge, state and nonce
        code_verifier, code_challenge = generate_pkce()
        state = secrets.token_urlsafe(16)
        nonce = secrets.token_urlsafe(16)

        auth_params = {
            "redirect_uri": REDIRECT_URI,
            "client_id": CLIENT_ID,
            "response_type": "code",
            "prompt": "login",
            "state": state,
            "nonce": nonce,
            "scope": DEFAULT_SCOPES,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
            "amw_clientapp": client_app,
            "cancelRedirect": "amwayhealthyhome://cancelLogin",
            "clientapp": client_app,
            "amw_lng": lang,
        }

        # Step 1: Follow redirects to get jansKey
        curr_url = OFFICIAL_AUTH_PORTAL
        curr_params: Optional[Dict[str, str]] = auth_params
        jans_key = ""
        exp_at = ""
        last_loc = ""
        mobile_ua = (
            "Mozilla/5.0 (Linux; Android 13; sdk_gphone64_arm64 Build/TE1A.220922.034) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.5060.71 Mobile Safari/537.36"
        )
        base_headers = {
            "accept-encoding": "gzip, deflate",
            "user-agent": mobile_ua,
        }

        for _ in range(5):
            async with session.get(
                curr_url, params=curr_params, headers=base_headers, allow_redirects=False
            ) as resp:
                loc = resp.headers.get("Location", "")
                last_loc = loc
                if "jansKey=" in loc:
                    parsed_loc = urllib.parse.urlparse(loc)
                    q_params = urllib.parse.parse_qs(parsed_loc.query)
                    jans_key = q_params.get("jansKey", [""])[0]
                    exp_at = q_params.get("exp_at", [""])[0]
                    break
                if not loc:
                    break
                curr_url = loc
                curr_params = None

        if not jans_key:
            _LOGGER.error("Failed to obtain jansKey from Amway OAuth portal. Last location: %s", last_loc)
            raise ValueError("Failed to obtain jansKey from Amway OAuth portal")

        # Step 2: POST /v1/token with credentials and jnsKey
        session_id = str(uuid.uuid4())
        j_hash = hashlib.md5(
            (norm_username.lower() + AMWAY_PASSWORD_SALT).encode("utf-8")
        ).hexdigest()

        token_headers = {
            "x-amw-clientapp": client_app,
            "x-amw-country-app": country_code,
            "content-type": "application/json",
            "accept-encoding": "gzip, deflate",
            "x-session-id": session_id,
            "j": j_hash,
            "x-api-key": AMWAY_API_KEY,
            "origin": "https://account2.amwayglobal.com",
            "referer": last_loc,
            "user-agent": mobile_ua,
        }
        token_body = {
            "username": norm_username,
            "iso_country_code": country_code,
            "password": password,
            "jnsKey": jans_key,
        }

        async with session.post(ACCOUNT2_TOKEN_URL, headers=token_headers, json=token_body) as resp:
            if resp.status != 200:
                text = await resp.text()
                _LOGGER.error("Amway credentials submission failed (%s): %s", resp.status, text)
                resp.raise_for_status()
            account_data = await resp.json()

        gluu_user = account_data.get("gluuUser", {})
        profile = gluu_user.get("profile", {})
        party_id = profile.get("partyId") or gluu_user.get("partyId")

        # Step 3: Call oxauth/restv1/authorize with jansKey to receive OAuth Code
        # CRITICAL: MUST NOT include prompt=login here!
        authorize_params = dict(auth_params)
        authorize_params.pop("prompt", None)
        authorize_params["jansKey"] = jans_key
        authorize_params["exp_at"] = exp_at

        curr_url = GLUU_OXAUTH_ENDPOINT
        curr_params = authorize_params
        auth_code = None

        for _ in range(5):
            async with session.get(
                curr_url, params=curr_params, headers=base_headers, allow_redirects=False
            ) as resp:
                loc = resp.headers.get("Location", "")
                if "code=" in loc:
                    parsed_code = urllib.parse.urlparse(loc)
                    q_code = urllib.parse.parse_qs(parsed_code.query)
                    code_list = q_code.get("code")
                    if code_list:
                        auth_code = code_list[0]
                    else:
                        auth_code = loc.split("code=")[1].split("&")[0]
                    break
                if not loc:
                    break
                curr_url = loc
                curr_params = None

        if not auth_code:
            _LOGGER.error("Failed to receive OAuth authorization code after credential verification")
            raise ValueError("Failed to receive OAuth authorization code")

        # Step 4: Exchange authorization code for tokens via PKCE code_verifier
        exchange_data = {
            "code": auth_code,
            "grant_type": "authorization_code",
            "scope": DEFAULT_SCOPES,
            "redirect_uri": REDIRECT_URI,
            "client_secret": CLIENT_SECRET,
            "code_verifier": code_verifier,
            "client_id": CLIENT_ID,
        }
        exchange_headers = {
            "accept-encoding": "gzip, deflate",
            "user-agent": mobile_ua,
        }

        async with session.post(GLUU_TOKEN_ENDPOINT, data=exchange_data, headers=exchange_headers) as resp:
            if resp.status != 200:
                text = await resp.text()
                _LOGGER.error("Amway token exchange failed (%s): %s", resp.status, text)
                resp.raise_for_status()
            token_res = await resp.json()

        access_token = token_res.get("access_token")
        refresh_token = token_res.get("refresh_token")
        expires_in = token_res.get("expires_in", 3600)

        if not access_token:
            raise ValueError("Token exchange missing access_token")

        _LOGGER.info("Successfully authenticated Amway mobile account for %s", norm_username)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "expires_in": expires_in,
            "scope": token_res.get("scope", DEFAULT_SCOPES),
            "username": norm_username,
            "party_id": party_id,
            "raw_response": token_res,
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
        headers = {"accept-encoding": "gzip, deflate"}
        async with session.post(GLUU_TOKEN_ENDPOINT, data=data, headers=headers) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def async_refresh_token(self) -> Dict[str, Any]:
        """Refresh the access token using saved refresh_token or fall back to stored credentials."""
        if self.refresh_token:
            try:
                data = {
                    "grant_type": "refresh_token",
                    "refresh_token": self.refresh_token,
                    "client_id": CLIENT_ID,
                    "client_secret": CLIENT_SECRET,
                    "scope": DEFAULT_SCOPES,
                }
                headers = {"accept-encoding": "gzip, deflate"}
                async with self._session.post(GLUU_TOKEN_ENDPOINT, data=data, headers=headers) as resp:
                    if resp.status == 200:
                        tokens = await resp.json()
                        self.access_token = tokens["access_token"]
                        if "refresh_token" in tokens:
                            self.refresh_token = tokens["refresh_token"]
                        if self._on_token_refreshed:
                            await self._on_token_refreshed(tokens)
                        _LOGGER.info("Successfully refreshed Amway token via refresh_token")
                        return tokens
                    _LOGGER.warning("Refresh token exchange returned status %s; falling back to re-login", resp.status)
            except Exception as err:
                _LOGGER.warning("Error refreshing token with refresh_token: %s; falling back to re-login", err)

        if self.username and self.password:
            _LOGGER.info("Re-authenticating Amway session via stored credentials...")
            login_res = await self.async_login_with_password(
                self._session, self.username, self.password, self.country
            )
            self.access_token = login_res["access_token"]
            if login_res.get("refresh_token"):
                self.refresh_token = login_res["refresh_token"]
            if self._on_token_refreshed:
                await self._on_token_refreshed({
                    "access_token": self.access_token,
                    "refresh_token": self.refresh_token,
                    "expires_in": login_res.get("expires_in", 3600),
                })
            return login_res

        raise ValueError("No valid refresh_token or stored credentials available for token refresh")

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
