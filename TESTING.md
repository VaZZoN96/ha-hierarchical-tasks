# Walidacja wydania 0.1.1

Data: 2026-09-08. Wydanie poprawia pakowanie i dystrybucję przez HACS.

## Wykonane na tej paczce

- **75/75 testów jednostkowych**: 44 istniejące testy modelu/zapisu/dostępu
  oraz 31 nowych testów pakowania i ustawiania metadanych repozytorium.
- **14/14 scenariuszy przeglądarkowych**, ponownie uruchomionych z kartą 0.1.1
  i rzeczywistym modelem danych. Połączenie HA w tej próbie jest symulowane.
- Kontrola składni Python i JavaScript oraz parsowania plików JSON/YAML.
- Lokalna kontrola struktury: jedna integracja, pliki karty i brand assets wewnątrz
  jej katalogu, zgodność wersji backendu/karty/przykładowego zasobu.
- Konfiguracja metadanych w tymczasowej kopii i walidacja tej kopii w trybie
  bez szablonów. To kontrola składni i spójności, nie istnienia adresów.
- Potwierdzenie, że domyślny walidator odrzuca nieuzupełnione metadane.
- Porównanie z ZIP-em 0.1.0: model, zapis, kontrola dostępu, config flow,
  adaptery WebSocket i akcje pozostały bez zmian. W starej karcie i `const.py`
  zmienił się tylko numer wersji. Wynik: `test-results/runtime-diff.json`.

Środowisko: Python 3.13.5, Node.js v22.16.0,
Playwright 1.57.0, Chromium 144.0.7559.96, Linux.

## Nowe testy pakowania

Sprawdzają m.in. rzeczywisty format OWNER/REPO, dopuszczalne loginy,
odrzucanie nieprawidłowych URL-i i wejść, wypełnianie wszystkich trzech
plików metadanych, brak zmian w plikach wykonawczych, idempotencję,
rozbieżne repozytoria i wersje, brakującą kartę, brak/niewłaściwe ikony,
nieprawidłowy format instalacji, ścieżkę danych poza kodem, działanie CLI
oraz blokowanie publikacji z `YOUR_GITHUB_USERNAME`.

## Co dokładnie było symulowane

Testy modelu i storage nie importują Home Assistanta. Testy uprawnień
używają małych stubów typów HA. Testy przeglądarkowe uruchamiają
prawdziwy plik karty oraz prawdziwy `TaskManager`, ale obiekt połączenia HA
i opakowanie `ha-card` są symulowane.
Zrzuty w `test-results` przedstawiają render karty w tym środowisku,
nie dashboard uruchomionej instalacji HA.

## Czego NIE potwierdzono

**Nie uruchomiono pełnej instancji Home Assistant ani instalacji przez HACS.**
Nie wykonano prawdziwego config flow, akcji w działającym HA, autoryzacji
WebSocket HA ani serwowania statycznego pliku przez HA.
Nie wykonano testów na fizycznym iPhonie/Androidzie ani testów Safari.
Punktem odniesienia adapterów z 0.1.0 było HA 2026.9.0; ta paczka zachowuje
je bez zmian. Zadeklarowano konserwatywne minimum HA 2026.9.0 w HACS.

**Nie uruchomiono tu oficjalnych walidatorów HACS ani hassfest.**
Dołączono workflow, który je uruchomi na Twoim publicznym repozytorium.
Samo dołączenie workflow nie oznacza, że przeszedł on sprawdzenie na GitHub.
Nie istnieje opublikowane przez tę paczkę repozytorium ani zdalny raport CI.
Nie sprawdzono przez sieć opisu, topics, Issues i uprawnień do Twojego GitHub.

## Ponowne uruchomienie

Na komputerze programistycznym, nie w produkcyjnym środowisku Pythona HA:

```bash
python -m unittest discover -s tests -p 'test_*.py' -v
python -m compileall -q custom_components/hierarchical_tasks tools
node --check custom_components/hierarchical_tasks/frontend/hierarchical-tasks-card.js
```

Przed ustawieniem repozytorium, tylko do sprawdzenia archiwum:

```bash
python tools/validate_package.py --allow-template
```

Ten tryb jawnie zaznacza, że metadane wymagają konfiguracji. Nie wolno
traktować jego wyniku jako zgody na publikację w HACS.
Po ustawieniu repozytorium:

```bash
python tools/configure_repository.py TWOJ_LOGIN/ha-hierarchical-tasks
python tools/validate_package.py
```

Do testów przeglądarkowych:

```bash
python -m pip install -r requirements-dev.txt
python -m playwright install chromium
python tests/browser_smoke.py
```

Skrypt obsługuje systemowy `chromium` lub zmienną `CHROMIUM_EXECUTABLE`.
Oficjalne sprawdzenia po publikacji: **Actions > Validate > Run workflow**.

Logi: `test-results/unit-tests.txt`, `browser-tests.txt`, `browser-results.json`,
`packaging-template.txt`, `packaging-configured.txt`, `syntax-and-yaml.txt`.
Szczegółowa instrukcja: `PUBLISHING_HACS.md` i `INSTALLATION.md`.
