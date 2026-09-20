"""Constants for the Amway Atmosphere integration."""

DOMAIN = "amway_atmosphere"

# Configuration keys
CONF_AUTH_CODE = "auth_code"
CONF_ACCESS_TOKEN = "access_token"
CONF_REFRESH_TOKEN = "refresh_token"
CONF_EXPIRES_AT = "expires_at"
CONF_SCAN_INTERVAL = "scan_interval"

DEFAULT_SCAN_INTERVAL = 30  # seconds

# OAuth2 & Amway Cloud Endpoints
AUTH_ENDPOINT = (
    "https://account2.amwayglobal.com/v1/proxy/oauth2/aus2ddwj0luvaUo641t7/v1/authorize"
)
GLUU_AUTH_ENDPOINT = AUTH_ENDPOINT
GLUU_TOKEN_ENDPOINT = (
    "https://gluu-prod01-prod.amstack-amwayidv2-prod.amwayglobal.com/oxauth/restv1/token"
)
CONEX_BASE_URL = "https://conex-api.amwayglobal.com/rest"
AWS_IOT_ENDPOINT = "axnk9oqlqxcqh-ats.iot.us-east-1.amazonaws.com"
AWS_REGION = "us-east-1"

CLIENT_ID = "7b90a30d-b404-4da7-a72b-449db798387c"
CLIENT_SECRET = "BtHRdjSwezvNyIGsYbhWakLAnJpxVFcQCmXrUKfZ"
REDIRECT_URI = "amwayhealthyhome://loginRedirect"
DEFAULT_SCOPES = (
    "openid profile email address phone offline_access "
    "bonus:all:read mdms:uberprofile:read partyID durables:parties:read "
    "durables:products:read durables:registration:create given_name middle_name family_name abo"
)

# Supported Models
MODEL_SKY = "Sky"
MODEL_MINI = "Mini"

# Fan Preset Modes
PRESET_MODE_AUTO = "auto"
PRESET_MODE_NIGHT = "night"
PRESET_MODE_TURBO = "turbo"
PRESET_MODE_MANUAL = "manual"

SKY_PRESET_MODES = [PRESET_MODE_AUTO, PRESET_MODE_NIGHT, PRESET_MODE_TURBO]
MINI_PRESET_MODES = [PRESET_MODE_AUTO, PRESET_MODE_NIGHT]

# Air Quality Ratings (Matching HomeKit 5-tier standard)
AIR_QUALITY_LEVELS = {
    1: "excellent",
    2: "good",
    3: "fair",
    4: "inferior",
    5: "poor",
}
