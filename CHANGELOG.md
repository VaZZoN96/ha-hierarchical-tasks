# Changelog

## 0.2.0

- dodano ACL per lista i per użytkownik Home Assistant,
- trzy poziomy dostępu w UI: brak / tylko odczyt / edycja,
- backend filtruje niewidoczne listy i egzekwuje prawa zapisu,
- administratorzy zawsze mają pełny dostęp,
- dodano menu `Udostępnianie...` z listą użytkowników HA,
- karta jest automatycznie rejestrowana przez integrację; ręczny Lovelace Resource nie jest wymagany,
- zachowano tworzenie nowych list przez `+ Lista` w karcie bez stałego `list_id`,
- format danych podniesiono do schema v2; v1 migruje bez utraty list,
- migracja v1 zachowawczo ustawia stare listy jako nieudostępnione zwykłym użytkownikom,
- API karty podniesiono do v2,
- dodano testy ACL oraz scenariusz przeglądarkowy tworzenia i udostępniania listy.

## 0.1.2

- poprawki HACS/hassfest i metadanych repozytorium.

## 0.1.1

- przygotowanie projektu do dystrybucji przez HACS.

## 0.1.0

- pierwsza wersja testowa.
