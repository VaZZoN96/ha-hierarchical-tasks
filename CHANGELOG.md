# Changelog

## 0.1.1 - 2026-09-08

Wydanie przygotowujące dystrybucję przez HACS; nadal do testów instalacyjnych.

- Dodano `hacs.json`; integracja wraz z kartą instalowana jako jeden pakiet.
- Dodano pola `documentation`, `issue_tracker` i niepusty `codeowners` w manifeście.
  Rzeczywiste wartości ustawia jednorazowo skrypt lub workflow na GitHub.
- Dodano lokalne ikony `brand/icon.png` i `brand/icon@2x.png` pod licencją MIT.
- Dodano workflow **Prepare repository**, walidację HACS i hassfest oraz Dependabot.
- Dodano lokalny walidator paczki i testy konfiguracji repozytorium.
- Zaktualizowano wersję backendu/karty i URL przykładowego zasobu do 0.1.1.
- Dodano instrukcję publikacji, instalacji w HACS i aktualizacji z 0.1.0.

**Nie zmieniono logiki list, formatu danych, domeny integracji ani API.**
Nie dodano automatycznej rejestracji zasobu karty ani encji `todo.*`.

## 0.1.0 - 2026-09-08

Pierwsze testowe wydanie: backend HA, karta, kategorie, podkategorie,
trójstanowe checkboxy, lokalny zapis, współdzielenie, automatyzacje,
przenoszenie, cofanie i eksport/import. Instalacja ręczna.
