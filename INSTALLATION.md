# Instalacja i aktualizacja - Hierarchical Tasks 0.2.1

## HACS

1. Dodaj publiczne repozytorium jako **HACS -> Custom repositories -> Integration**.
2. Pobierz Hierarchical Tasks.
3. Wykonaj pełny restart Home Assistant.
4. Dodaj integrację w **Ustawienia -> Urządzenia i usługi -> Dodaj integrację**.
5. Dodaj kartę ręczną do dashboardu:

```yaml
type: custom:hierarchical-tasks-card
title: Zadania
hide_completed: false
confirm_bulk: true
```

Od 0.2.0 **nie dodawaj zasobu JS ręcznie**. Integracja rejestruje i ładuje dołączoną
kartę podczas startu HA.

## Aktualizacja z 0.1.x i błąd "Custom element doesn't exist"

Po zainstalowaniu 0.2.1:

1. Wejdź w **Ustawienia -> Dashboardy -> Zasoby / Resources**.
2. Usuń ręczny wpis zaczynający się od
   `/hierarchical_tasks/hierarchical-tasks-card.js`.
3. Wykonaj **pełny restart Home Assistant** - samo przeładowanie YAML nie wystarczy.
4. W przeglądarce użyj twardego odświeżenia. W aplikacji HA zamknij i otwórz
   frontend ponownie.
5. Użyj karty `type: custom:hierarchical-tasks-card`.

Jeśli błąd pozostaje, otwórz w przeglądarce:
`/hierarchical_tasks/hierarchical-tasks-card.js?v=0.2.1`. Powinien pojawić się kod JS,
a nie 404. Sprawdź też log Home Assistant podczas startu integracji.

## Tworzenie list

Użyj karty **bez** `list_id`:

```yaml
type: custom:hierarchical-tasks-card
title: Wszystkie listy
```

Administrator zobaczy `+ Lista`. Karta z `list_id: zakupy` jest widokiem jednej
konkretnej listy i celowo nie pokazuje przycisku tworzenia kolejnej.

## Udostępnianie użytkownikom

Administrator:

1. wybiera listę,
2. otwiera `...` obok nazwy listy,
3. wybiera **Udostępnianie...**,
4. ustawia dla każdego użytkownika `Brak dostępu`, `Tylko odczyt` lub `Edycja`,
5. zapisuje.

Administratorzy HA są zawsze administratorami również w Hierarchical Tasks.
Użytkownicy z dostępem `Edycja` mogą zmieniać zawartość listy, ale nie mogą tworzyć,
usuwać ani udostępniać całych list.

## Dane

Dane pozostają w:

```text
/config/.storage/hierarchical_tasks.json
```

Przed aktualizacją testową warto wykonać kopię zapasową. Nie edytuj tego pliku przy
działającym Home Assistant.
