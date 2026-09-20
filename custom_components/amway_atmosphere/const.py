"""Constants for the Amway Atmosphere integration."""

DOMAIN = "amway_atmosphere"

# Configuration keys
CONF_USERNAME = "username"
CONF_PASSWORD = "password"
CONF_COUNTRY = "country"
CONF_PARTY_ID = "party_id"
CONF_AUTH_CODE = "auth_code"
CONF_ACCESS_TOKEN = "access_token"
CONF_REFRESH_TOKEN = "refresh_token"
CONF_EXPIRES_AT = "expires_at"
CONF_SCAN_INTERVAL = "scan_interval"

DEFAULT_COUNTRY = "TW"
DEFAULT_SCAN_INTERVAL = 30  # seconds

# Amway Account2 Direct Auth Endpoints & Secrets
ACCOUNT2_TOKEN_URL = "https://account2.amwayglobal.com/v1/token"
AMWAY_API_KEY = "aa-MG5GsAkYzwh3m4QyYvST"
AMWAY_PASSWORD_SALT = "d07c86c4d1b3978a860efe817f60eda7"

# OAuth2 & Amway Cloud Endpoints
# ⚠️ 錯誤端點警告 (DO NOT USE)：
# gluu-prod01-prod.amstack-amwayidv2-prod.amwayglobal.com/oxauth/restv1/authorize 是錯誤的！
# 該端點會導向綠色的內部 LDAP 維護頁面，台灣一般消費者帳號密碼在該處必定驗證失敗。
# 正確的官方消費者入口為：https://account2.amwayglobal.com/{lang}/?clientapp={clientapp}&redirect={redirect}
OFFICIAL_AUTH_PORTAL = "https://account2.amwayglobal.com"
AUTH_ENDPOINT = OFFICIAL_AUTH_PORTAL
GLUU_AUTH_ENDPOINT = AUTH_ENDPOINT  # Deprecated alias for compatibility

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
