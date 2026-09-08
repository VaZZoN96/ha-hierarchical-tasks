# Instalacja i aktualizacja - Hierarchical Tasks 0.1.1

**Wymagana wersja zadeklarowana w HACS: Home Assistant 2026.9.0 lub nowszy.**
To konserwatywny punkt odniesienia adapterów, nie gwarancja zgodności z każdą
późniejszą wersją HA. Nadal jest to wydanie do testów.
Przed instalacją wykonaj kopię zapasową konfiguracji HA.

## 1. Pobranie przez HACS

Jeśli masz tylko ZIP, najpierw opublikuj jego zawartość na GitHub według
[PUBLISHING_HACS.md](PUBLISHING_HACS.md). To jednorazowe przygotowanie
repozytorium. HACS nie instaluje bezpośrednio lokalnego ZIP-a.

W HACS otwórz **menu > Custom repositories / Repozytoria niestandardowe**.
Dodaj adres publicznego repozytorium, wybierając **Integration**.
Otwórz pozycję **Hierarchical Tasks**, pobierz, następnie wykonaj **pełny
restart Home Assistanta**.

HACS instaluje integrację razem z kartą. Nie dodawaj osobnego repozytorium
Dashboard. Pobranie plików przez HACS nie konfiguruje automatycznie integracji.

## 2. Dodanie integracji

**Ustawienia > Urządzenia i usługi > Dodaj integrację > Hierarchical Tasks**.
Przy pierwszej próbie pozostaw tworzenie przykładowych danych włączone.
Powstanie lista `zakupy`, kategorie `warzywniak`, `piekarnia` oraz produkty.

**0 encji jest prawidłowe**: ta integracja ma własny model hierarchiczny,
własną kartę i akcje `hierarchical_tasks.*`. Nie tworzy encji `todo.*`.
Nie wymaga wpisu w `configuration.yaml`.

Domyślny dostęp mają administratorzy. Udostępnianie normalnym użytkownikom
włączysz w opcjach integracji; obejmuje wszystkie listy.

## 3. Jednorazowe dodanie zasobu karty

**Ustawienia > Panele / Dashboards > menu > Zasoby / Resources**.
Gdy nie widać tej pozycji, sprawdź tryb zaawansowany profilu administratora.
Dodaj:

```text
URL: /hierarchical_tasks/hierarchical-tasks-card.js?v=0.1.1
Typ: Moduł JavaScript / JavaScript Module
```

Dodaj tylko jeden taki zasób. Przy aktualizacji **edytuj istniejący wpis**,
nie dodawaj drugiego obok `?v=0.1.0`.
Integracja sama serwuje plik; nie kopiujesz go do `www` i nie używasz
adresu `/hacsfiles/`. HACS pobrał go jako część integracji, nie osobną kartę.
Odśwież stronę HA po zapisaniu zasobu.

Dla dashboardów z zasobami zarządzanymi w YAML zobacz `README.md`.
Nie zmieniaj sposobu zarządzania zasobami bez zachowania innych swoich kart.

## 4. Karta na dashboardzie

Dodaj kartę ręczną i wklej:

```yaml
type: custom:hierarchical-tasks-card
title: Moje zadania
hide_completed: false
confirm_bulk: true
```

To karta z przełącznikiem list i możliwością tworzenia kolejnych.
Dla widoku tylko przykładowej listy zakupów dodaj:

```yaml
list_id: zakupy
```

`list_id` to ID listy, nie nazwa ani encja HA.

## Aktualizacja z 0.1.0 bez utraty list

Wydanie 0.1.1 zachowuje domenę `hierarchical_tasks`, format danych,
identyfikatory, API i ścieżkę zapisu z 0.1.0.
Nie jest wymagana migracja bazy.

1. Zrób kopię zapasową HA i eksport list z karty.
2. Dodaj opublikowane repozytorium w HACS jako Integration i pobierz 0.1.1.
   Jeśli HACS zgłosi istniejący folder z instalacji ręcznej, zachowaj kopię
   plików i usuń/zmień nazwę wyłącznie katalogu kodu
   `custom_components/hierarchical_tasks`, po zatrzymaniu HA. Przenieś kopię
   poza `custom_components`. Uruchom HA (może tymczasowo pokazać brak
   integracji), pobierz pakiet w działającym HACS, a następnie jeszcze raz
   zrestartuj HA.
3. **Nie usuwaj wpisu integracji** w Urządzeniach i usługach.
   Nie usuwaj ani nie zmieniaj pliku danych:

   ```text
   /config/.storage/hierarchical_tasks.json
   ```

4. Zrestartuj HA, zmień parametr istniejącego zasobu na `?v=0.1.1`
   i przeładuj frontend. Dotychczasowy YAML karty pozostaje poprawny.

Plik z danymi leży poza katalogiem kodu aktualizowanym przez HACS.
Zasób karty nadal rejestrujesz ręcznie; ta wersja nie modyfikuje
konfiguracji dashboardu bez Twojej zgody.

## Awaryjnie: instalacja ręczna

Pełny kod pozostaje w ZIP-ie. Po jednorazowym uzupełnieniu metadanych
repozytorium możesz skopiować sam folder
`custom_components/hierarchical_tasks` do
`/config/custom_components/hierarchical_tasks`, zrestartować HA i wykonać
kroki 2-4. Nie trzeba instalować zależności `pip` lub `npm` w HA.

## Test odbiorczy

Otwórz kartę w dwóch oknach. Zaznacz Kapustę: w obu oknach WARZYWNIAK
powinien pokazać częściowe wykonanie. Zaznacz kategorię, sprawdź
potwierdzenie zbiorczej zmiany, dodawanie, usuwanie i cofanie.
Następnie przeładuj stronę i zrestartuj HA, aby sprawdzić zachowanie danych.

Przy błędzie zachowaj wersję HA/HACS, fragment logów integracji oraz
komunikat z konsoli przeglądarki. Nie publikuj tokenów ani prywatnych list.
Więcej diagnostyki i wszystkie opcje karty: `README.md`.
