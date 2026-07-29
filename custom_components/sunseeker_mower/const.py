"""Stale dla integracji Sunseeker / Bugull Mower."""

DOMAIN = "sunseeker_mower"

CONF_EMAIL = "email"
CONF_PASSWORD = "password"

BASE_URL = "http://server.sk-robot.com/api/"
BASIC_AUTH_HEADER = "Basic YXBwOmFwcA=="  # base64("app:app") - stale dla apki

UPDATE_INTERVAL_MINUTES = 15

# Klucze danych zwracanych przez getRecord, ktore mapujemy na sensory
KEY_AREA = "area"
KEY_ON_MIN = "onMin"
KEY_BATTERY = "electricity"
KEY_STATUS_NAME = "workStatusName"  # tekst z serwera (zalezny od Accept-Language)
KEY_STATUS_CODE = "workStatusCode"  # stabilny kod, niezalezny od jezyka
KEY_FAULT_NAME = "faultStatusName"
KEY_FAULT_CODE = "faultStatusCode"
KEY_ONLINE = "onlineFlag"
KEY_LAT = "lat"
KEY_LNG = "lng"

# Mapowanie kodow statusu na stabilne klucze tlumaczen (translation_key "state").
# UWAGA: potwierdzony w praktyce jest tylko kod "1" (praca/koszenie).
# Pozostale kody nie zostaly jeszcze zaobserwowane - nieznane kody spadaja
# na "unknown", a surowy kod/nazwa trafia do atrybutu diagnostycznego encji,
# zeby mozna bylo je zglosic i dopisac tlumaczenie.
STATUS_CODE_TO_KEY: dict[str, str] = {
    "1": "working",
}

FAULT_CODE_TO_KEY: dict[str, str] = {
    "normal": "ok",
}

STATUS_UNKNOWN_KEY = "unknown"
FAULT_UNKNOWN_KEY = "unknown"
