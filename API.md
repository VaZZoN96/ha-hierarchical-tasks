# Hierarchical Tasks API - 0.2.0

Integracja udostępnia akcje w domenie `hierarchical_tasks` oraz prywatne komendy
WebSocket używane przez dołączoną kartę.

## Model dostępu

Każda lista ma mapę `access`:

```json
{
  "user-id": "read",
  "other-user-id": "write"
}
```

Administrator HA ma zawsze pełny dostęp. Dla zwykłego użytkownika backend zwraca
tylko listy z rolą `read` lub `write`; mapa `access` jest usuwana z odpowiedzi.

`set_list_access`, tworzenie/zmiana nazwy/usuwanie list i import wymagają administratora
przy wywołaniu w kontekście użytkownika. Automatyzacje HA bez kontekstu użytkownika są
traktowane jako zaufane operacje systemowe.

## Najważniejsze akcje

- `hierarchical_tasks.create_list`
- `hierarchical_tasks.rename_list`
- `hierarchical_tasks.delete_list`
- `hierarchical_tasks.set_list_access`
- `hierarchical_tasks.add_item`
- `hierarchical_tasks.rename_item`
- `hierarchical_tasks.delete_item`
- `hierarchical_tasks.move_item`
- `hierarchical_tasks.set_completed`
- `hierarchical_tasks.clear_completed`
- `hierarchical_tasks.import_data`
- `hierarchical_tasks.undo`
- `hierarchical_tasks.get_data`

Przykład udostępnienia po identyfikatorach użytkowników HA:

```yaml
action: hierarchical_tasks.set_list_access
data:
  list_id: zakupy
  access:
    USER_ID_1: read
    USER_ID_2: write
```

Do codziennej konfiguracji udostępniania zalecane jest menu w karcie, bo pobiera ono
listę użytkowników HA i nie wymaga ręcznego kopiowania ID.

Wszystkie mutacje karty używają `expected_revision`, aby nie nadpisać nowszej zmiany
z innego klienta.
