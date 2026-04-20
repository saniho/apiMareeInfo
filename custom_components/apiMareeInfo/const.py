"""Constants"""

import datetime

ISSUE_URL = "https://github.com/saniho/apiMareeInfo/issues"

DOMAIN = "apiMareeInfo"
PLATFORMS = ["sensor"]

# delai pour l'update http, toutes les 3 heures
CONF_SCAN_INTERVAL_HTTP = datetime.timedelta(seconds=60 * 60 * 3)
CONF_MAXHOURS = "MAX_HOURS"
CONF_PROVIDER = "provider"

PROVIDER_MAREEINFO = "Maree Info"
PROVIDER_STORMGLASS = "Stormglass.io"
DEFAULT_PROVIDER = PROVIDER_MAREEINFO
PROVIDERS = [PROVIDER_MAREEINFO]

__VERSION__ = "1.5.2"

__name__ = "apiMareeInfo"
