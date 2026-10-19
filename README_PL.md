# SeasonLens

Porównaj dwa cenniki, przeanalizuj historyczne ceny surowców i kursy walut, a następnie zapisz raport — w przeglądarce.

**Wersja 0.1.3, eksperymentalna.** Projekt open source dla osób pracujących z cennikami, zakupami i analizą rynku w Excelu. Typowy problem: dostajesz nową wersję skoroszytu i chcesz sprawdzić zmiany przed użyciem jej do analizy.

[Otwórz aplikację](https://eluyz.github.io/SeasonLens/?lang=pl) · [Demonstracja na 3 minuty](https://eluyz.github.io/SeasonLens/demo/pl.html) · [English](README.md) · [Pobierz wersję 0.1.3](https://github.com/eluyz/SeasonLens/releases/tag/v0.1.3)

## Co można zrobić?

| Pytanie | Wynik w SeasonLens |
| --- | --- |
| Co zmieniło się w nowym XLSX? | Nowe daty, korekty cen, wpisy nieobecne w nowszym pliku i niezmienione obserwacje, wraz z wartościami różnic. |
| Jak cena wypada na tle historii? | Średnie miesięczne, porównania sezonowe i historyczne miary ryzyka, z datami i liczbą obserwacji. |
| Co mogę zachować? | Raport HTML z wybranych sekcji lub wydruk/zapis PDF przez przeglądarkę. Przed udostępnieniem sprawdź jego treść. |

## Zacznij od jednego przykładu

W [krótkiej demonstracji](https://eluyz.github.io/SeasonLens/demo/pl.html) pobierzesz dwa niewielkie, wymyślone cenniki pszenicy. Oczekiwany wynik to **1 nowa data, 1 korekta, 1 nieobecny wpis i 208 niezmienionych obserwacji**. Korekta wynosi **213,29 → 218,29 EUR/t, czyli +5**. Po porównaniu możesz osobno dodać nowszy plik i zobaczyć jego historię.

Scenariusz jest rozpisany na około trzy minuty prezentacji po pobraniu plików. Pierwsze samodzielne przejście może potrwać dłużej. Nie potrzebujesz konta, Pythona, klucza API ani abonamentu na dane.

## Dane i prywatność

- Sześć wbudowanych instrumentów: pszenica, kukurydza, rzepak, EUR/PLN, EUR/USD i wyliczony USD/PLN. **Wszystkie obserwacje wbudowane i demonstracyjne są wymyślone**; aplikacja nie pobiera bieżących notowań.
- Własne XLSX/CSV są przetwarzane w pamięci bieżącej karty, bez wysyłania danych do serwera. Odświeżenie usuwa importy. Preferencja języka może zostać zapamiętana. Samo wejście na stronę korzysta z hostingu GitHub Pages.
- Raporty i eksporty mogą zawierać prywatne ceny i wyniki. Ich pobranie nie publikuje danych; udostępnienie pliku ujawnia jego zawartość.
- Import wymaga jawnego wskazania kolumn, jednostek i daty granicznej. Nieprawidłowe wartości oraz powtórzone daty odrzucają import. Braki pozostają widoczne; kreska nie oznacza zera.
- Porównanie pokazuje różnice, bez automatycznego scalania lub dodawania danych. Nieobecność wpisu nie dowodzi usunięcia notowania ani kompletności sesji giełdowych.

## Dalsze instrukcje

[Przewodnik: pszenica i EUR/PLN](https://eluyz.github.io/SeasonLens/walkthrough-pl.html) prowadzi przez import dwóch instrumentów, przeliczenie ceny na PLN/t i zapis raportu. [Pilotaż PL/EN](https://eluyz.github.io/SeasonLens/pilot/) zawiera trzy dłuższe zadania i formularze opinii.

Interfejs obsługuje polski i angielski. Nazwy własnych instrumentów zachowują wpisaną treść. Raport pozostaje w języku, w którym został utworzony. Na małych ekranach szerokie tabele i wykresy przewijają się we własnych ramkach.

Opcjonalna aplikacja lokalna w Pythonie zapewnia prywatną historię SQLite i aktualizację kursów referencyjnych ECB. Jest to odrębny tryb: import w publicznej przeglądarce nie aktualizuje bazy. Nie ma automatycznego źródła cen zamknięcia kontraktów. [Instalacja i ograniczenia](docs/INSTALLATION.md), [metody](docs/METHODS.md) i [pełna dokumentacja techniczna](README.md) są po angielsku.

## Rozwój projektu

Kod i wymyślone przykłady mają licencję MIT; dołączony SheetJS ma licencję Apache-2.0. W implementacji pomagają agenci kodujący. Definicje, ręcznie policzone przykłady i testy służą weryfikacji; wykonane sprawdzenia opisuje [STATUS.md](STATUS.md). Statystyki opisują dostarczoną historię i nie gwarantują skuteczności prognoz.

Zgłoszenia błędów i propozycje ulepszeń przyjmujemy przez [GitHub Issues](https://github.com/eluyz/SeasonLens/issues). Dołącz kroki odtworzenia na wymyślonych danych, oczekiwany i rzeczywisty wynik oraz przeglądarkę. Zgłoszenia są publiczne — nie załączaj danych firmowych, klientów ani licencjonowanych notowań. Zasady współpracy: [CONTRIBUTING.md](CONTRIBUTING.md).
