# Konfiguracja repozytorium

Archiwum nie jest opublikowanym repozytorium GitHub.
Nie podano jeszcze nazwy konta ani repozytorium, dlatego manifest ma jawny
znacznik `YOUR_GITHUB_USERNAME`. Nie wskazuje on prawdziwego opiekuna projektu.

Przed dodaniem do HACS wykonaj jeden z wariantów:

- GitHub: **Actions > Prepare repository > Run workflow**.
- Na komputerze: `python tools/configure_repository.py TWOJ_LOGIN/ha-hierarchical-tasks`.

Skrypt zastąpi ten plik konkretnymi adresami oraz uzupełni manifest i CODEOWNERS.
Instrukcja krok po kroku: [PUBLISHING_HACS.md](PUBLISHING_HACS.md).
