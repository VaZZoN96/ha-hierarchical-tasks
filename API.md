# Hierarchical Tasks API v1

Implementacja w tym repozytorium. API jest rozszerzeniem uwierzytelnionego
WebSocket Home Assistanta; nie jest osobnym, publicznym serwerem HTTP.
Podstawowa autoryzacja połączenia jest taka jak w HA.
Dodatkowa polityka integracji jest opisana w README.

## Odczyt

```json
{"id": 1, "type": "hierarchical_tasks/get"}
```

Wynik `result`:

```json
{
  "api_version": 1,
  "available": true,
  "data": {
    "schema": 1,
    "revision": 0,
    "lists": {
      "zakupy": {"id": "zakupy", "name": "Zakupy", "nodes": {}}
    }
  },
  "permissions": {"write": true, "import": true, "undo": false}
}
```

`permissions` dotyczy bieżącego użytkownika. `undo` może zmieniać się
po każdym zapisie, nawet gdy prawa dostępu pozostają takie same.

## Subskrypcja

```json
{"id": 2, "type": "hierarchical_tasks/subscribe"}
```

Po odpowiedzi sukcesu przychodzi zdarzenie `event` z pełnym stanem w tej samej
strukturze co odczyt. Kolejne aktualizacje wysyłają pełny aktualny stan.
Do zwolnienia subskrypcji użyj standardowego mechanizmu HA:

```json
{"id": 3, "type": "unsubscribe_events", "subscription": 2}
```

W karcie robi to funkcja zwrócona przez `connection.subscribeMessage()`.
Po ponownym połączeniu należy otrzymać nowy pełny stan; nie odtwarzać
utraconych mutacji automatycznie. Biblioteka połączenia frontendu HA obsługuje
odnawianie subskrypcji. Integracja po każdej subskrypcji wysyła stan początkowy.

Po wyłączeniu integracji lub cofnięciu dostępu istnieąca subskrypcja
może dostać zamiast danych:

```json
{"available": false, "error": {"code": "forbidden", "message": "Access denied."}}
```

Klient powinien wtedy usunąć dane z widoku i zablokować edycję.

## Zapis

```json
{
  "id": 4,
  "type": "hierarchical_tasks/mutate",
  "operation": "add_item",
  "expected_revision": 0,
  "data": {
    "list_id": "zakupy",
    "node_id": "warzywniak",
    "name": "WARZYWNIAK",
    "kind": "category"
  }
}
```

Wynik zawiera co najmniej `revision` i `changed`, a zależnie od operacji również
`list_id`, `node_id`, `target_list_id`, `affected` lub `imported_lists`.
Nowy stan odczytaj/subskrybuj oddzielnie. `revision` jest monotoniczna dla
aktualnej bazy i jest zapisywana na dysku. Import nie przyjmuje numeru rewizji
z importowanego pliku, tylko tworzy następną rewizję bieżącej bazy.
Operacja, która nic nie zmienia, nie zwiększa rewizji.

`expected_revision` jest obowiązkowa dla KAŻDEGO zapisu WebSocket.
Stara rewizja daje błąd `conflict`, bez częściowego zastosowania operacji.
Nie ma operacji `toggle`: klient wysyła jawne `completed: true/false`.

## Operacje / akcje HA

Nazwa operacji jest również nazwą akcji `hierarchical_tasks.<nazwa>`.
W akcjach HA `expected_revision` jest polem obok pozostałych pól `data` akcji;
w WebSocket jest obok `operation` i `data`. Akcje mają odpowiedź opcjonalną,
z wyjątkiem `get_data` (odpowiedź obowiązkowa).

| Operacja | Wymagane pola danych | Opcjonalne pola danych |
|---|---|---|
| `create_list` | `name` | `list_id` |
| `rename_list` | `list_id`, `name` | brak |
| `delete_list` | `list_id` | brak |
| `add_item` | `list_id`, `name` | `kind`, `parent_id`, `node_id` |
| `rename_item` | `list_id`, `node_id`, `name` | brak |
| `delete_item` | `list_id`, `node_id` | brak |
| `move_item` | `list_id`, `node_id`, `parent_id` | `position`, `target_list_id` |
| `set_completed` | `list_id`, `completed` | `node_id` |
| `clear_completed` | `list_id` | `node_id` |
| `import_data` | `document` | brak |
| `undo` | brak | brak |

`get_data` jest oddzielną akcją HA bez pól, nie operacją mutacji WebSocket.
Zwraca dokument `schema/revision/lists`, bez opakowania `available/permissions`.

Każda akcja mutująca może dodatkowo zawierać `expected_revision`;
dla `undo` i `import_data` jest to wymóg. Brak rewizji w pozostałych akcjach
HA oznacza pracę na najnowszym stanie w kolejce serwera.

Semantyka:

- `kind`: `task` (domyślnie) albo `category`; tylko kategorie są rodzicami.
- `parent_id: null`: poziom główny. Rodzic musi istnieć w liście docelowej.
- `move_item`: przenosi całe poddrzewo; `position` to końcowy indeks od zera
  wśród rodzeństwa po wyjęciu przenoszonego elementu. Bez niego: koniec.
- `delete_item` kategorii usuwa całe poddrzewo.
- `set_completed`: zadanie, wszystkie zadania pod kategorią albo cała lista,
  gdy brak `node_id`. Kategorie nie dostają niezależnego stanu wykonania.
- `clear_completed`: usuwa wykonane zadania, nigdy samych kategorii;
  zakres można ograniczyć przez `node_id`.
- `import_data`: **zastępuje wszystkie listy**, nie łączy dokumentów.
  Pole `document` to zawartość eksportu/get_data. Wymagany administrator.
- `undo`: jeden krok, tylko ostatnia zmiana tego samego użytkownika.

## Format elementu

```json
{
  "id": "kapusta",
  "name": "Kapusta",
  "kind": "task",
  "parent_id": "warzywniak",
  "completed": false,
  "position": 0
}
```

ID: 1-64 znaki, małe litery ASCII, cyfry, podkreślenia i myślniki;
pierwszy znak musi być literą lub cyfrą. ID listy jest unikalne globalnie,
ID elementu w ramach listy. Przenoszenie między listami odrzuca kolizje ID.
Nazwy mogą się powtarzać. Sortowanie: `position`, następnie ID.

Stan kategorii oblicza się tylko z zadań w jej poddrzewie:
`checked = total > 0 and done == total`, `indeterminate = 0 < done < total`.
Pole `completed` kategorii jest zawsze `false` i nie stanowi jej agregatu.

## Błędy

Typowe kody: `invalid_input`, `not_found`, `already_exists`, `cycle`,
`conflict`, `cannot_undo`, `forbidden`, `not_ready`, `storage_error`,
`invalid_storage`, `unknown_error`.
Walidacja zewnętrznej ramki WebSocket może też zwrócić błąd formatu HA.
Akcje HA zgłaszają wyjątki walidacji zamiast słowników błędów.
Po błędzie połączenia wynik zapisu może być nieznany klientowi:
odczytaj stan przed ponowieniem. Nie ma trwałych kluczy idempotencji.

## Przyszły klient mobilny

Może korzystać z tego samego get/subscribe/mutate po zalogowaniu do HA.
Aktualne API nie zawiera mechanizmu scalania zmian offline. Nie traktuj
pełnego importu jako sposobu synchronizacji telefonów.
