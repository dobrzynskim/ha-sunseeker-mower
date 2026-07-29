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
KEY_STATUS = "workStatusName"
KEY_FAULT = "faultStatusName"
KEY_ONLINE = "onlineFlag"
KEY_LAT = "lat"
KEY_LNG = "lng"
