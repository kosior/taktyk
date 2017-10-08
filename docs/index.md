<p align="center">
-- <a href="#wymagania">WYMAGANIA</a>
-- <a href="#instalacja">INSTALACJA</a>
-- <a href="#uruchamianie">URUCHAMIANIE</a>
-- <a href="#parametry">PARAMETRY</a> --
<br>
-- <a href="#konfiguracja">KONFIGURACJA</a>
-- <a href="#dokument-html">DOKUMENT HTML</a>
-- <a href="#inne">INNE</a> --
</p> 

# Wymagania:
* minimum **Python 3.5.2** (do ściągnięcia [tutaj](https://www.python.org/downloads/) (przy instalacji zaznaczyć "Add Python to PATH"))
* **requests**, **selenium**, **jinja2**, **beautifulsoup4** - moduły zostaną zainstalowane automatycznie przy pierwszym uruchomieniu po uzyskaniu zgody od użytkownika

# Instalacja:
Wystarczy pobrać (klikając na samej górze Download .zip) i rozpakować archiwum*.

*archiwum może się rozpakować do folderu o dziwnej nazwie, ale można ją sobie zmienić w celu łatwiejszej nawigacji. 

# Uruchamianie:
W wierszu poleceń/terminalu przejśc do folderu, w którym znajduje się katalog `taktyk` oraz plik `taktyk.py` i wpisać:

    python taktyk
   
#### W systemie Windows za pomocą Python Launchera można uruchomić program otwierając plik: `taktyk.py`.

Uruchomienie programu bez żadnych parametrów:

- do pobrania wpisów zostanie wykorzystane WykopAPI
- użytkownik zostanie poproszony o podanie loginu i hasła
- zostanie wygenerowany plik .html
- zostaną pobrane pilki, które znajdują się we wpisach i komentarzach

# Parametry
Dodatkowo można uruchomić program z następującymi parametrami:

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Parametr&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; | Opis
------------|------------
-h, -\-help | wyświetla pomoc i zamyka program
-f, -\-file | po uruchomieniu będzie można podać ścieżkę do pliku (tekstowego, html) lub folderu, w którym znajdują się adresy URL wpisów lub ich numery id
-i, -\-ids | po uruchomieniu będzie można podać bezpośrednio numery wpisów
-s, -\-selenium {firefox, chrome} | do zalogowania i pobrania wpisów zostanie użyta wybrana przeglądarka i moduł selenium. Do uruchomienia przeglądarki potrzebny jest sterownik, który zostanie pobrany po udzieleniu zgody przez użytkownika
-S, -\-session | pobieranie numerów id wpisów za pomocą requests.Session
-d, -\-delete {db, wykop, all} | po uruchomieniu będzie można podać numery wpisów i usunąć je z wybranego zasięgu:<br> **db** - tylko z bazy danych,<br> **wykop** - tylko z ulubionych na Wykopie,<br> **all** - z ulubionych na Wykopie i z bazdy danych
-\-skip [{com}] | pobieranie plików zostanie wyłączone, opcjonalny parametr **com** wyłączy pobieranie plików tylko z komentarzy
-\-html [TAG] | utworzy ponownie plik .html, opcjonalnie można sprecyzować tag, do którego zostaną ograniczone wpisy
-\-new | utworzy nową bazę danych
-u, -\-update | aktualizacja programu
-n, -\-nsfw | zostanie włączony filtr NSFW, wpisy NSFW będą ignorowane
-\-scrape | program zostanie przełączony w tryb scrapowania
-\-save | program pobierze pliki z wpisów, które są w bazie danych
-c, -\-comments | program zaktualizuje komentarze we wpisach
-p, -\-pdk | po uruchomieniu będzie można podać wygenerowany przez siebie userkey

Poniższy zestaw parametrów uruchomi przeglądarkę Chrome w celu zalogowania i pominie pobieranie plików:

    python taktyk -s chrome --skip
    
Poniższy zestaw parametrów utworzy plik .html tylko z wpisami zawierającymi tag #programowanie:
    
    python taktyk --html programowanie

\* **-s, -i, -f, -S, -u, -d, -c, -\-html, -\-save** -  wszelkie kombinacje tych parametrów są niemożliwe

# Konfiguracja

W celu konfiguracji programu można edytować plik `config.ini` w folderze `taktyk`. Przy każdym uruchomieniu następujące ustawienia mogą zostać wczytane:
- username (login)
- password (hasło)
- appkey
- secretkey
- accountkey
- userkey
- static_args (parametry z którymi zostanie uruchomiony program np. -\-skip -n)
- exts (rozszerzenia plików, które mają być pobierane)

# Dokument HTML

![](https://github.com/kosior/taktyk/raw/master/docs/screenshot.png)

W wygenerowanym pliku .html użytkownik ma następujące możliwości:
- filtrowanie wpisów po tagach
- zaznaczanie wpisów i kopiowanie ich numerów do schowka (co ułatwia np. usuwanie wpisów z ulubionych)
- sortowanie tagów według kolejności alfabetycznej lub ilości wpisów
- zaznaczanie wszystkich widocznych wpisów
- rozwijanie komentarzy dla jednego wpisu lub dla wszystkich
- przechodzenie kolejno po każdym widocznym wpisie

# Inne
- wszystkie adresy URL, na które wykonywane są jakiekolwiek requesty są w pliku `settings.py`
- funkcje logowania itd. znajdują się w pliku `auth.py`
- w przypadku problemów z WykopAPI program przełączy się automatycznie na scrapowanie
- jeśli dostępna będzie aktualizacja użytkownik zostanie powiadomiony
