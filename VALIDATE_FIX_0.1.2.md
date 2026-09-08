# Hierarchical Tasks 0.1.2 - poprawki Validate

## Co zostało naprawione

1. Hassfest `CONFIG_SCHEMA`:
   integracja korzysta tylko z Config Entries, więc `__init__.py` definiuje teraz
   `CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)`.
2. `manifest.json` jest skonfigurowany dla `VaZZoN96/ha-hierarchical-tasks` i wersji 0.1.2.
3. `hacs.json` został uproszczony do obsługiwanych pól potrzebnych temu projektowi.
4. GitHub Actions korzystają z `actions/checkout@v6`, `actions/setup-python@v6`
   i `actions/setup-node@v6`.
5. Workflow Validate sprawdza jawnie, czy pliki są w prawidłowej lokalizacji:
   `hacs.json` oraz `custom_components/hierarchical_tasks/manifest.json`.

## Ustawienia repozytorium GitHub wymagane przez HACS

Na stronie repozytorium ustaw:

- Visibility: **Public**
- Description: `Hierarchical task lists for Home Assistant with nested categories and a Lovelace card.`
- Topics: `home-assistant`, `hacs`, `custom-integration`, `tasks`, `todo`, `lovelace`
- Issues: włączone

HACS wymaga publicznego repozytorium, opisu i topics do oficjalnej walidacji publikacji.

## Struktura w root repozytorium

Po wgraniu paczki na GitHub root powinien wyglądać m.in. tak:

```
.github/
custom_components/
  hierarchical_tasks/
    manifest.json
    __init__.py
hacs.json
README.md
```

Nie może być dodatkowego poziomu typu:

```
ha-hierarchical-tasks/custom_components/...
```

wewnątrz repozytorium.

## Co uruchomić

Po commit/push całej zawartości 0.1.2:

1. GitHub -> Actions -> Validate -> Run workflow.
2. Nie uruchamiaj starego `Re-run jobs`, bo użyje starego commita.
3. Workflow `Prepare repository` nie jest potrzebny w 0.1.2 dla repozytorium
   `VaZZoN96/ha-hierarchical-tasks` - metadane są już wpisane.

## Jeśli HACS nadal zgłasza `expected a dictionary. Got None`

Najpierw sprawdź, czy repo jest publiczne i czy etap `Check HACS repository layout`
przechodzi. W HACS istnieje obecnie otwarte zgłoszenie dotyczące dokładnie takiego
fałszywego błędu walidatora `hacs/action` dla repozytorium z poprawnym manifestem,
w szczególności reprodukowane na prywatnym repozytorium. Sam HACS może mimo tego
instalować integrację poprawnie.
