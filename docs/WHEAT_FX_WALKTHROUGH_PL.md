# Pszenica i EUR/PLN: od skoroszytu do raportu

[English](WHEAT_FX_WALKTHROUGH.md) · **Polski**

Skorzystaj z [publicznego demo po polsku](https://eluyz.github.io/SeasonLens/?lang=pl) oraz [szablonu XLSX z wymyślonymi danymi](https://eluyz.github.io/SeasonLens/seasonlens-import-template.xlsx). Ten przewodnik jest również dostępny jako [strona dostosowana do telefonu](https://eluyz.github.io/SeasonLens/walkthrough-pl.html). Na komputerze przejście całości zajmuje około 5–10 minut; przypisanie kolumn na telefonie może potrwać dłużej.

Celem jest import **wyłącznie pszenicy i EUR/PLN z tego samego skoroszytu**, sprawdzenie przeliczenia na PLN za tonę, zrozumienie ograniczeń krótkiej historii i zapisanie raportu. Wszystkie obserwacje w skoroszycie są wymyślone. Nie są cenami zamknięcia MATIF, kursami banku centralnego ani prognozą.

## 1. Otwórz przykładowy plik

Zacznij w nowej karcie demo, aby mieć dokładnie sześć wbudowanych instrumentów przykładowych. Rozwiń **Zacznij tutaj — przeglądaj, importuj lub utwórz raport**, a następnie wybierz **Pobierz przykładowy szablon XLSX**. Możesz też użyć linku do szablonu powyżej.

Wybierz **Otwórz import prywatny**, wskaż `seasonlens-import-template.xlsx` w polu **Skoroszyt Excel lub plik CSV**, ustaw **Datę graniczną analizy** na **2026-10-06**, a następnie wybierz **Otwórz i podejrzyj plik**. Otwarcie skoroszytu nie oznacza jego zaimportowania.

## 2. Wskaż wiersze i dwa instrumenty

Sprawdź te ustawienia, nawet jeśli mają już właściwe wartości:

| Pole | Wartość |
| --- | --- |
| Arkusz | Prices |
| Wiersz nagłówków | 1 |
| Pierwszy wiersz danych | 4 |
| Kolumna daty | A · Date |
| Data graniczna analizy | 2026-10-06 |
| Format dat zapisanych jako tekst | YYYY-MM-DD |
| Separator dziesiętny cen zapisanych jako tekst | . |

Wiersz 2 określa jednostki. Wiersz 3 zawiera celowo wymyślone wartości przykładu bieżących notowań z datą 2026-10-07; musi pozostać poza wybraną historią. Podgląd nadal pokazuje ten rzeczywisty wiersz arkusza, aby można było go sprawdzić. Komórki liczbowe i daty w tym szablonie nie wymagają parsowania tekstu ani zgody na użycie wyników formuł. Pozostaw niezaznaczone **Jawnie pomijaj puste komórki cen, z liczbą wierszy** oraz **Użyj zapisanych wyników formuł Excela (mogą być nieaktualne)**.

W sekcji **Wybierz instrumenty z kolumn cen** zaznacz **tylko B i E**. Pozostaw C, D, F i G niezaznaczone. Wprowadź:

| Kolumna | Nazwa instrumentu | Jednostki | Rola |
| --- | --- | --- | --- |
| B | Wheat sample | EUR/t | Pszenica |
| E | EUR/PLN sample | PLN per EUR | EUR/PLN |

Nazwy instrumentów i jednostki w tabeli są dokładnymi wartościami tego przykładu. `PLN per EUR` oznacza PLN za EUR. Nazwy kolumn nie przypisują ról. Wybranie roli EUR/PLN ustawia sugerowane jednostki; sprawdź jawnie **PLN per EUR**.

## 3. Sprawdź dane, przejrzyj wynik i dopiero potem dodaj

Wybierz **Sprawdź wybrane instrumenty**. Podsumowanie powinno pokazać **dwa instrumenty**, każdy z:

- **210 obserwacjami**, od **2025-12-17** do **2026-10-06**;
- **0 pominiętych pustych wartości** i **0 wykluczonych przyszłych wierszy**;
- brakiem obserwacji z wiersza 3. Wiersz ten znajduje się poza wybranym zakresem rzeczywistych wierszy danych, dlatego nie jest liczony jako pominięty przyszły wiersz.

Nic nie zostało jeszcze dodane. Wybierz raz **Dodaj sprawdzone instrumenty do tej karty**. Lista instrumentów ma teraz **osiem pozycji**: sześć początkowych przykładów i dwa prywatne importy. Import ma oznaczenie **USER_FILE**, mimo że zawiera wymyślone dane przykładowe. Oznaczenie opisuje sposób dodania danych do aplikacji, a nie oficjalnego dostawcę.

Zmiana dowolnego ustawienia importu unieważnia sprawdzenie i wymaga ponownej walidacji.

## 4. Sprawdź pszenicę w PLN za tonę

Otwórz **Opcje analizy**. W polu **Instrument** wybierz **Wheat sample · prywatny Excel**, a nie wbudowaną pszenicę. W polu **Jednostki wyświetlania** wybierz **PLN/t**.

Sprawdź **Datę graniczną analizy: 2026-10-06**, **Obserwacje: 210**, **Ostatnią obserwację: 2026-10-06** i informację o przeliczeniu: **210 dodatnich par z dokładnie tą samą datą**, bez nieprzeliczonych obserwacji surowca. Wykorzystywana jest wyłącznie zadeklarowana seria EUR/PLN z tego samego importu; aplikacja nie podstawia przykładowych kursów i nie przenosi kursu z wcześniejszego dnia.

Ostatni historyczny wiersz skoroszytu, **213**, pozwala niezależnie sprawdzić rachunek:

```text
213,29 EUR/t × 4,2051 PLN za EUR = 896,905779 PLN/t
```

To około **896,91 PLN/t**, czyli **89 690,58 PLN** za 100 ton. Zaokrąglona do pełnej jednostki cena odniesienia przy **Średnich cenach miesięcznych** pokazuje **897**; dotyczy to wyświetlania, a nie utraty dokładności obliczeń. Aby sprawdzić pełną precyzję, wybierz **Eksportuj wybrane obserwacje (CSV)** i sprawdź ostatnie `date` i `value`: data **2026-10-06**, wartość około **896.905779** (eksport binarnej liczby zmiennoprzecinkowej może pokazać `896.9057789999999`). CSV zawiera też kolumny wskaźników technicznych.

## 5. Czytaj wykresy bez uzupełniania luk

W sekcji Zacznij tutaj wybierz **Pokaż średnie miesięczne** i **Pokaż ceny z pięciu lat**.

**Średnie ceny miesięczne** są średnimi zaobserwowanych cen dziennych w danym miesiącu. W PLN/t uśredniane są ceny przeliczone osobno dla każdego dnia; aplikacja nie mnoży średniej miesięcznej pszenicy przez średni miesięczny kurs walutowy. Ceny surowców w tabelach są wyświetlane bez miejsc po przecinku, a obliczenia zachowują pełną dokładność. Kolory porównują każdą niezaokrągloną średnią miesięczną z ostatnią ceną dzienną; nie są sygnałami kupna ani sprzedaży.

**Średnie ceny miesięczne — ostatnie pięć lat z bieżącym rokiem** zachowują zakres **2022–2026**, mimo że szablon zaczyna się w grudniu 2025. Dla lat 2022–2024 i stycznia–listopada 2025 nie ma obserwacji. Listopad–grudzień 2026 przypadają po dacie granicznej. Kreski i luki na wykresie są oczekiwane; nie oznaczają zera. Przerywana średnia z okresu nadaje jednakową wagę każdej dostępnej średniej miesięcznej z poszczególnych lat. Październik 2026 jest niepełny i obejmuje cztery obserwacje. Krótka historia nie pozwala ustalić wiarygodnego wzorca sezonowego.

W **Analizie technicznej — ostatnie 12 miesięcy** pozostaw **Zakres wykresu dziennego: Ostatnie 12 miesięcy** oraz wszystkie sześć pól wyboru linii. Wykres zawiera cenę, SMA20, SMA100, SMA200 i dwie wstęgi Bollingera. Wyświetlana jest tylko dostarczona historia; jest ona krótsza niż 12 miesięcy. Wskaźniki wymagają pełnych okien: pierwsze 19 obserwacji nie ma SMA20 ani wstęg Bollingera, pierwsze 99 nie ma SMA100, a pierwsze 199 nie ma SMA200. Dostępnych jest tylko **11 wartości SMA200**. Są to okna obserwacji, a nie gwarancja liczby dni kalendarzowych lub sesji giełdowych. Wcześniejsza dostarczona historia służy do wyliczenia wskaźników przed wyświetlanym zakresem; brakująca historia nigdy nie jest dopisywana.

## 6. Sprawdź ryzyko historyczne i pokrycie danych

W sekcji **Ryzyko historyczne i analiza statystyczna** otwórz **Ryzyko historyczne i epizody stresowe**. Pozostaw:

| Ustawienie | Wartość |
| --- | --- |
| Okres oceny ryzyka, walut i prognoz | Ostatnie 5 lat kalendarzowych |
| Perspektywa | Kupujący — wzrost cen jest niekorzystny |
| Horyzont obserwowanych przedziałów | 1 obserwowany przedział |
| Poziom ufności ogona | 95% |
| Ilość w tonach | 100 |

Przykład ma **209 zmian między kolejnymi obserwacjami**. Przy 95% równoważna liczebność ogona wynosi **10,45 obserwacji**, co przekracza wymagane przez aplikację minimum pięciu. Zmiana **Poziomu ufności ogona** na **99%** pozostawia tylko **2,09**, dlatego VaR i Expected Shortfall (oczekiwana strata w ogonie) są niedostępne. To zabezpieczenie dotyczące pokrycia danych, a nie błąd. Przed utworzeniem domyślnego raportu wróć do **95%**.

Kupujący traktuje wzrost cen jako niekorzystny, sprzedający — spadek. Wyświetlany scenariusz budżetowy stosuje historyczne zmiany procentowe do bieżącej ceny odniesienia i ilości. Nie jest zyskiem lub stratą z transakcji ani prognozą. Pięć lat kalendarzowych oznacza wybrany zakres, a nie stwierdzenie, że skoroszyt zawiera pięć lat obserwacji.

Opcjonalnie otwórz **Udział surowca i waluty w ryzyku ceny w PLN**. Te dwie zaimportowane serie mają **209 dokładnie dopasowanych przedziałów**. Podział wariancji uwzględnia kowariancję i opisuje ten przykład; udziały nie są dowodem przyczynowości ani skuteczności zabezpieczenia. Sezonowość pełnych lat wymaga dłuższej historii: ten szablon nie pozwala wyznaczyć przedziałów niepewności średniej historycznej.

## 7. Utwórz i zapisz raport

Sprawdź, czy wybrano prywatną pszenicę w **PLN/t**, datę graniczną **2026-10-06** i powyższe ustawienia ryzyka. W sekcji Zacznij tutaj wybierz **Otwórz kreator raportu**. Pozostaw cztery początkowo zaznaczone sekcje:

- **Przegląd rynku i pokrycie danych**;
- **Średnie ceny miesięczne i porównanie pięciu lat**;
- **Wykres techniczny z wybranymi liniami**;
- **Ryzyko historyczne i epizody stresowe**.

Wybierz **Utwórz podgląd raportu**. Sprawdź **Wheat sample**, **PLN/t**, **2026-10-06** i **USER_FILE** w metadanych. **Pobierz HTML** zapisuje samodzielny raport z wybranymi wynikami i wykresami. **Drukuj / Zapisz PDF** otwiera okno drukowania przeglądarki; wybierz zapis jako PDF, jeśli jest dostępny. Zapisywanie PDF, podział na strony i obsługa telefonu zależą od przeglądarki. Alternatywą jest pobrany HTML. Raport pozostaje niezmienną kopią; po zmianie ustawień wybierz **Powrót do analizy** i utwórz go ponownie.

Raporty nie zawierają oryginalnych tablic obserwacji ani kodu aplikacji, ale widoczne tabele, ceny i zadeklarowane źródła nadal mogą być prywatne. Udostępnienie raportu oznacza udostępnienie tych wyników.

## Zakończenie i znane ograniczenia

Przed odświeżeniem zapisz wszystko, co chcesz zachować. Odświeżenie usuwa oba zaimportowane instrumenty i przywraca sześć wbudowanych przykładów; żaden import w przeglądarce nie jest zapisywany w SQLite. Preferencje wyświetlania mogą zostać zachowane, ale zaimportowane obserwacje nie. Do trwałego przechowywania prywatnej historii użyj aplikacji lokalnej opisanej w [przewodniku rozpoczęcia pracy](GETTING_STARTED.md) i [README](../README.md).

Ćwiczenie nie pobiera danych na żywo ani nie aktualizuje ich automatycznie. Jego 210 dat to wymyślone obserwacje w dni robocze, a nie sprawdzony kalendarz giełdowy. Nie dowodzi zdolności prognostycznej, pięcioletniego pokrycia ani przydatności do analizy rzeczywistego rynku. Na małych ekranach szerokie tabele i wykresy przewijają się we własnych ramkach; przypisanie kolumn jest łatwiejsze na większym ekranie. Zachowanie na fizycznym telefonie, w Safari i w systemowym oknie zapisu PDF nadal wymaga sprawdzenia.
