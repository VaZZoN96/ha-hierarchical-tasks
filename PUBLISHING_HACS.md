# Publikacja w HACS - Hierarchical Tasks 0.2.0

> **0.2.0:** karta jest ładowana automatycznie przez integrację. Nie publikuj jej jako osobnego repozytorium Dashboard i nie wymagaj ręcznego wpisu Resources.

Ta paczka zawiera **jedną integrację HA z dołączoną kartą**.
HACS instaluje cały katalog `custom_components/hierarchical_tasks`, w tym kartę.
Nie zakładaj drugiego repozytorium typu Dashboard.

**Przed dodaniem do HACS potrzebne jest publiczne repozytorium GitHub i jego
rzeczywiste metadane. Samego ZIP-a nie da się wkleić do HACS.**
Archiwum nie zostało opublikowane na GitHub przez autora tej paczki.
Nie podano jeszcze konta docelowego, więc `YOUR_GITHUB_USERNAME` jest wyraźnym
znacznikiem do jednorazowej konfiguracji, nie adresem gotowego projektu.

## A. Wariant bez Pythona na komputerze: GitHub w przeglądarce

### 1. Utwórz repozytorium

Utwórz na swoim koncie GitHub nowe repozytorium:

```text
Nazwa: ha-hierarchical-tasks
Widoczność: Public
Opis: Local hierarchical task lists and a bundled dashboard card for Home Assistant
Topics: home-assistant, hacs, custom-integration, todo
```

Nazwa może być inna; automat wykryje faktyczną nazwę.
W ustawieniach repozytorium pozostaw włączone **Issues**.
Opis i topics ustawisz w sekcji **About**. Nie dodawaj drugiej integracji
jako osobnego podkatalogu w `custom_components`.

### 2. Wgraj zawartość rozpakowanej paczki

Rozpakuj ZIP i otwórz katalog `ha-hierarchical-tasks`.
Na GitHub użyj **Add file > Upload files** i wgraj jego **zawartość**,
nie cały folder nadrzędny i nie archiwum ZIP.
Uwzględnij ukryty folder `.github` (w niektórych menedżerach plików
trzeba włączyć pokazywanie ukrytych plików).
Można także użyć GitHub Desktop lub zwykłego gita.

Na głównej stronie repozytorium muszą być od razu widoczne:

```text
.github/
  workflows/
    prepare-repository.yml
    validate.yml
custom_components/
  hierarchical_tasks/
    manifest.json
    brand/icon.png
    frontend/hierarchical-tasks-card.js
hacs.json
README.md
tools/
```

Plik `hacs.json` musi być w korzeniu repozytorium.
Zatwierdź pliki na gałęzi domyślnej, zwykle `main`.

### 3. Jednym przyciskiem uzupełnij metadane

Przejdź do **Actions > Prepare repository > Run workflow**.
Pole `codeowner` może zostać puste: zostanie wpisany login osoby
uruchamiającej workflow. Dla repozytorium organizacji wpisz osobisty login
opiekuna projektu, nie nazwę zespołu.

Workflow zapisze w repozytorium:

```text
documentation -> prawdziwy adres tego repozytorium
issue_tracker -> ten sam adres zakończony /issues
codeowners -> rzeczywisty login GitHub
```

Uzupełni też `.github/CODEOWNERS` i `REPOSITORY.md`.
Wykonuje commit na gałęzi domyślnej; nie publikuje Release.
Nie potrzebuje tokenu Home Assistanta ani dostępu do Twoich list.
Korzysta ze standardowego `GITHUB_TOKEN` danej akcji, nie prosi o osobisty PAT.

Jeśli nie widać **Run workflow**, sprawdź, czy plik workflow trafił na
gałąź domyślną i czy GitHub Actions jest włączony.
Jeśli zapis kończy się `403` albo blokuje go ochrona gałęzi,
sprawdź politykę uprawnień Actions w swoim repozytorium/organizacji.
Nie trzeba wyłączać ochrony: alternatywnie wykonaj wariant B i zatwierdź
zmiany normalnie przez commit lub pull request.

### 4. Uruchom walidację po konfiguracji

Przejdź do **Actions > Validate > Run workflow** na gałęzi domyślnej.
Workflow zawiera lokalne sprawdzenie paczki, testy jednostkowe oraz
oficjalne walidatory **HACS** i **Home Assistant hassfest**.
Nie wyłączono sprawdzania ikon, metadanych ani innych wymagań HACS.

Pierwsza walidacja po wgraniu plików może być czerwona, bo celowo
odrzuca `YOUR_GITHUB_USERNAME`. Po wykonaniu **Prepare repository** uruchom
**Validate** ponownie ręcznie, zamiast ponawiać stary przebieg na starym commicie.
Commit utworzony przez `GITHUB_TOKEN` sam nie uruchamia workflow typu `push`.

**Do HACS dodawaj repozytorium po pozytywnym wyniku walidacji.**
Błąd `description`, `topics` lub `issues` popraw w ustawieniach GitHub.
Błąd `brands` może oznaczać brak wgranego `brand/icon.png` lub starszy
walidator HACS bez obsługi lokalnych ikon. Nie maskuj błędu przez `ignore`;
zachowaj log walidacji do analizy.

### 5. Opcjonalnie opublikuj wersję

W **Releases > Draft a new release** utwórz tag `v0.2.0` wskazujący
commit z prawdziwymi metadanymi. Opis skopiuj z `CHANGELOG.md`.
Nie wystarczy sam tag: do wyboru wersji w HACS potrzebny jest Release.
Bez Release HACS może pobrać zawartość gałęzi domyślnej.

`zip_release` jest wyłączone: nie musisz załączać osobnego archiwum
integracji jako zasobu Release. HACS pobiera pliki z repozytorium.
Numer w `manifest.json`, `const.py` i karcie pozostaje `0.2.0`; tag może
mieć prefiks `v`. Nie twórz Release wskazującego commit sprzed konfiguracji.

## B. Alternatywa: jednorazowa konfiguracja na komputerze

W katalogu rozpakowanego projektu, w osobnym środowisku komputerowym,
**nie w produkcyjnym środowisku Pythona HA**, wykonaj:

```bash
python tools/configure_repository.py TWOJ_LOGIN/ha-hierarchical-tasks
python tools/validate_package.py
```

Na systemach, które używają polecenia `python3`, zastąp nim `python`.
Skrypty wymagają Pythona 3.10 lub nowszego; korzystają wyłącznie z biblioteki
standardowej. Nie instalujesz nic przez `pip` na potrzeby konfiguracji.

Dla repozytorium organizacji:

```bash
python tools/configure_repository.py ORGANIZACJA/ha-hierarchical-tasks --codeowner TWOJ_LOGIN
```

Możesz też podać cały adres HTTPS repozytorium zamiast `OWNER/REPO`.
Skrypt nie wysyła plików na GitHub i nie sprawdza, czy repozytorium istnieje.
Następnie wgraj pliki i uruchom **Validate** zgodnie z wariantem A.

Bez skryptu można ręcznie zmienić `documentation`, `issue_tracker` i
`codeowners` w `custom_components/hierarchical_tasks/manifest.json`
oraz zgodnie z nimi `.github/CODEOWNERS`. Skrypt jest wygodniejszy,
ponieważ dodatkowo zapisuje adres repozytorium w `REPOSITORY.md`.

## C. Dodanie do HACS i konfiguracja HA

W Home Assistant: **HACS > menu > Custom repositories / Repozytoria
niestandardowe**. Wklej adres publicznego repozytorium i wybierz
**Integration**, nie Dashboard. Dodaj i pobierz **Hierarchical Tasks**.

Następnie pełny restart HA, dodanie integracji w **Ustawienia > Urządzenia
i usługi** oraz zasobu JavaScript i karty. Dokładna instrukcja:
[INSTALLATION.md](INSTALLATION.md).

## Co jest lokalnie sprawdzone, a czego nie potwierdzono

Skrypt `validate_package.py` sprawdza strukturę, składnię metadanych,
spójność wersji i obecność zasobów. To **nie jest** oficjalny walidator
HACS ani test instalacji w działającym HA. Nie sprawdza przez sieć istnienia
konta, adresów, opisu repozytorium, topics ani włączonego Issues.
Do tego służy workflow po publikacji. Wyniki lokalnych testów: `TESTING.md`.

## Źródła wymagań

Sprawdzono 8 września 2026 r.:

- https://hacs.xyz/docs/publish/integration/
- https://hacs.xyz/docs/publish/start/
- https://hacs.xyz/docs/publish/action/
- https://hacs.xyz/docs/faq/custom_repositories/
- https://developers.home-assistant.io/docs/core/integration/brand_images/
- https://docs.github.com/en/actions/how-tos/manage-workflow-runs/manually-run-a-workflow
- https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/trigger-a-workflow
