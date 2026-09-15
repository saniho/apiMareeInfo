"""Constants"""

import datetime

ISSUE_URL = "https://github.com/saniho/apiMareeInfo/issues"

DOMAIN = "apiMareeInfo"
PLATFORMS = ["sensor", "weather"]

CONF_SCAN_INTERVAL_HTTP = datetime.timedelta(seconds=60 * 5)
DEFAULT_SCAN_INTERVAL = datetime.timedelta(minutes=5)
CONF_MAXHOURS = "MAX_HOURS"
CONF_STORM_KEY = "stormio_key"
DEFAULT_MAX_HOURS = 6
CONF_PROVIDER = "provider"
CONF_ID = "id"

PROVIDER_MAREEINFO = "Maree Info"
PROVIDER_STORMGLASS = "Stormglass.io"
DEFAULT_PROVIDER = PROVIDER_MAREEINFO
PROVIDERS = [PROVIDER_MAREEINFO]

__VERSION__ = "2.1.10-beta1"

__name__ = "apiMareeInfo"
