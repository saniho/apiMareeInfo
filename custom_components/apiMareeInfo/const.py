"""Constants"""

import datetime

ISSUE_URL = "https://github.com/saniho/apiMareeInfo/issues"

DOMAIN = "apiMareeInfo"
PLATFORMS = ["sensor", "weather"]

# delai pour l'update http, toutes les 5 minutes
CONF_SCAN_INTERVAL_HTTP = datetime.timedelta(seconds=60 * 5)
CONF_MAXHOURS = "MAX_HOURS"
CONF_PROVIDER = "provider"
CONF_ID = "id"

PROVIDER_MAREEINFO = "Maree Info"
PROVIDER_STORMGLASS = "Stormglass.io"
DEFAULT_PROVIDER = PROVIDER_MAREEINFO
PROVIDERS = [PROVIDER_MAREEINFO]

__VERSION__ = "2.1.1-beta.1"

__name__ = "apiMareeInfo"
