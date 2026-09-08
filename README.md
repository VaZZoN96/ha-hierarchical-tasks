# Hierarchical Tasks 0.2.1

Hierarchiczne listy zadań dla Home Assistant: listy, kategorie, podkategorie,
pojedyncze zadania, trójstanowe checkboxy kategorii i współdzielenie per lista.

## Najważniejsze funkcje

- wiele niezależnych list,
- kategorie i podkategorie do 16 poziomów,
- osobne odhaczanie zadań,
- trójstanowy checkbox kategorii,
- tworzenie, zmiana nazw, usuwanie i przenoszenie,
- drag & drop na komputerze oraz menu przenoszenia na telefonie,
- lokalny zapis w `/config/.storage/hierarchical_tasks.json`,
- eksport/import JSON i jednokrokowe cofanie,
- akcje Home Assistant do automatyzacji,
- karta Lovelace dołączona do integracji,
- udostępnianie każdej listy osobno użytkownikom HA: **Brak / Tylko odczyt / Edycja**.

Administratorzy Home Assistant zawsze mają pełny dostęp. Użytkownik bez dostępu do
listy nie dostaje jej danych przez API integracji; nie jest to tylko ukrywanie w UI.

## Instalacja przez HACS

Dodaj to repozytorium w HACS jako niestandardowe repozytorium typu **Integration**,
zainstaluj integrację i wykonaj pełny restart Home Assistant. Następnie:

**Ustawienia -> Urządzenia i usługi -> Dodaj integrację -> Hierarchical Tasks**.

Od wersji 0.2.0 karta jest ładowana przez integrację automatycznie. Nie trzeba już
dodawać jej ręcznie w `Dashboard -> Resources`.

Jeśli aktualizujesz 0.1.x, usuń stary ręczny zasób
`/hierarchical_tasks/hierarchical-tasks-card.js?...`, zrestartuj HA i wykonaj twarde
odświeżenie przeglądarki / przeładuj aplikację mobilną.

## Karta

Widok zarządzający wszystkimi dostępnymi listami:

```yaml
type: custom:hierarchical-tasks-card
title: Zadania
hide_completed: false
confirm_bulk: true
```

Administrator zobaczy tutaj przycisk **+ Lista**.

Widok przypięty do jednej listy:

```yaml
type: custom:hierarchical-tasks-card
title: Zakupy
list_id: zakupy
hide_completed: false
confirm_bulk: true
```

W widoku z `list_id` celowo nie ma przycisku `+ Lista`.

## Tworzenie list

Jako administrator otwórz kartę bez `list_id` i kliknij **+ Lista**. Podaj nazwę;
ID możesz zostawić puste albo ustawić trwałe ID, np. `dom`, jeśli chcesz używać go
w automatyzacjach.

Alternatywnie użyj akcji:

```yaml
action: hierarchical_tasks.create_list
data:
  list_id: dom
  name: Dom
```

## Udostępnianie list

Jako administrator wybierz listę, kliknij menu `...` obok jej nazwy, a następnie
**Udostępnianie...**. Dla każdego zwykłego użytkownika HA wybierz:

- **Brak dostępu** - lista nie jest mu zwracana,
- **Tylko odczyt** - widzi listę i stan zadań, ale nie może nic zmieniać,
- **Edycja** - może dodawać, odhaczać, przenosić i usuwać elementy tej listy.

Tworzenie/usuwanie list, zmiana nazwy listy, import i zarządzanie udostępnianiem
pozostają operacjami administratora.

## Migracja z 0.1.x

Format danych v1 jest odczytywany automatycznie i migrowany do v2. Ze względów
bezpieczeństwa stare listy po migracji są domyślnie dostępne tylko administratorom,
dopóki administrator jawnie nie ustawi udostępniania dla każdej listy.

## Automatyzacje

```yaml
action: hierarchical_tasks.add_item
data:
  list_id: zakupy
  parent_id: warzywniak
  name: Pomidory
  kind: task
```

```yaml
action: hierarchical_tasks.set_completed
data:
  list_id: zakupy
  node_id: warzywniak
  completed: true
```

Więcej informacji: `INSTALLATION.md`, `API.md`, `TESTING.md`.
