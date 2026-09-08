# Walidacja wydania 0.2.0

Data: 2026-09-08.

## Wykonane

- **77/77 testów jednostkowych**: model, zapis, migracja schema v1 -> v2,
  ACL per lista, ograniczenia użytkowników oraz pakowanie HACS.
- **15/15 scenariuszy przeglądarkowych** na prawdziwym pliku karty i prawdziwym
  `TaskManager`; połączenie Home Assistant było symulowane.
- Nowy scenariusz tworzy listę z karty, otwiera `Udostępnianie...`, pobiera
  symulowaną odpowiedź własnego admin-only endpointu użytkowników, daje użytkownikowi prawo `write` i weryfikuje
  zapis ACL w modelu.
- `node --check` dla karty.
- offline `tools/validate_package.py --repository VaZZoN96/ha-hierarchical-tasks`.
- kontrola spójności wersji 0.2.0 w `manifest.json`, `const.py` i karcie.

Środowisko testu przeglądarkowego: Chromium 144.0.7559.96, Linux.

## Co jest symulowane

Testy nie uruchamiają pełnego Home Assistant. Stubowane są obiekty uprawnień HA,
a test karty symuluje transport WebSocket oraz odpowiedź własnego `hierarchical_tasks/users`.
Logika hierarchii, mutacje i sam JavaScript karty są rzeczywiste.

## Czego jeszcze nie potwierdzono

- instalacji/aktualizacji 0.2.0 w rzeczywistej instancji HA przez HACS,
- oficjalnego hassfest/HACS po opublikowaniu tego commita,
- rzeczywistego pobierania użytkowników przez `hass.auth.async_get_users()` w Twojej instancji,
- Safari/iOS i aplikacji mobilnej HA.

Kod automatycznego ładowania karty używa aktualnego API Home Assistant
`homeassistant.components.frontend.add_extra_js_url` oraz
`async_register_static_paths`; finalny test w prawdziwym HA jest nadal potrzebny.

## Ponowne uruchomienie

```bash
PYTHONPATH=tests python -m unittest discover -s tests -p 'test_*.py' -v
PYTHONPATH=tests python tests/browser_smoke.py
node --check custom_components/hierarchical_tasks/frontend/hierarchical-tasks-card.js
python tools/validate_package.py --repository VaZZoN96/ha-hierarchical-tasks
```

Po publikacji uruchom także **Actions -> Validate -> Run workflow**.
