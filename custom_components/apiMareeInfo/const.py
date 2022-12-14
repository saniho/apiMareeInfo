""" Constants """
import datetime

ISSUE_URL = "https://github.com/saniho/apiMareeInfo/issues"

DOMAIN = "apiMareeInfo"

# delai pour l'update http, toutes les 3 heures
CONF_SCAN_INTERVAL_HTTP = datetime.timedelta(seconds=60 * 60 * 3)

__VERSION__ = "1.1.0"

__name__ = "apiMareeInfo"
