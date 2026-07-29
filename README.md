# Sunseeker / Bugull Robotic Mower – integracja Home Assistant

Niezależna integracja Home Assistant dla robotów koszących zbudowanych na
platformie chmurowej **Bugull** (`server.sk-robot.com`) — używanej m.in. przez
apki "Robotic Mower" i modele takie jak `RMA2002L20V-DLSUHS` (m.in. rebrandy
AMA/RBA2000).

> ⚠️ **To jest nieoficjalna integracja.** Nie jest tworzona ani wspierana
> przez producenta kosiarki. Powstała na podstawie analizy ruchu sieciowego
> własnej aplikacji mobilnej, wyłącznie do użytku prywatnego/interoperacyjności
> z własnym sprzętem. Używasz na własną odpowiedzialność.

## Co udostępnia

Dla każdej kosiarki powiązanej z Twoim kontem tworzy encje:

| Sensor | Opis | Jednostka |
|---|---|---|
| Powierzchnia koszenia | Łączna skoszona powierzchnia | m² |
| Czas pracy | Łączny czas pracy silnika | h |
| Bateria | Aktualny poziom naładowania | % |
| Status | Bieżący status roboczy (np. praca, ładowanie) | – |
| Usterka | Status usterki / błędu | – |

Dane odświeżane są cyklicznie co 15 minut (`cloud_polling`).

## Instalacja

### Przez HACS (custom repository)

1. HACS → trzy kropki w prawym górnym rogu → **Custom repositories**
2. URL: `https://github.com/dobrzynskim/ha-sunseeker-mower`, kategoria: **Integration**
3. Znajdź "Sunseeker / Bugull Robotic Mower" na liście HACS i zainstaluj
4. Zrestartuj Home Assistant

### Ręcznie

1. Skopiuj folder `custom_components/sunseeker_mower/` do `<config>/custom_components/`
2. Zrestartuj Home Assistant

## Konfiguracja

Ustawienia → Urządzenia i usługi → Dodaj integrację → **Sunseeker / Bugull Robotic Mower**

Podaj e-mail i hasło używane w oficjalnej aplikacji mobilnej. Integracja
loguje się do tego samego API co apka i cyklicznie pobiera dane statusu.

## Jak to działa / disclaimer techniczny

Producent nie udostępnia publicznego, udokumentowanego API. Endpointy i
protokół zostały odtworzone poprzez dekompilację własnej kopii aplikacji
mobilnej (analiza kodu źródłowego wygenerowanego przez jadx) w celu
zapewnienia interoperacyjności z zakupionym sprzętem. Adres serwera i
struktura zapytań mogą się zmienić bez ostrzeżenia po stronie producenta —
w takim wypadku integracja przestanie działać do czasu aktualizacji.

## Licencja

MIT — zobacz [LICENSE](LICENSE).
