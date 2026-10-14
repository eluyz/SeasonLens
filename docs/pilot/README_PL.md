# SeasonLens — pilotaż w 15–25 minut

[English](README_EN.md) · **Polski** · [Instrukcja w przeglądarce](index.html#pl)

Cel: sprawdzić, czy bez pomocy potrafisz wczytać skoroszyt, odczytać porównanie miesięczne i zapisać raport. Nie musisz znać programowania ani zakładać konta. Udział i przekazanie opinii są dobrowolne. Nie testujemy prognoz ani wyników inwestycyjnych.

Przygotuj przeglądarkę, około 15–25 minut i [szablon XLSX](../seasonlens-import-template.xlsx). Wszystkie jego ceny i kursy są **wymyślone**; nie używaj plików firmowych, danych klientów ani rzeczywistych notowań w tym pilotażu. Wybierz [publiczne demo po polsku](https://eluyz.github.io/SeasonLens/?lang=pl) lub, w pobranym pakiecie, otwórz [lokalny index.html](../index.html?lang=pl) w przeglądarce. Jeżeli czytasz plik na GitHubie, użyj publicznego demo. Wersja przeglądarkowa nie wymaga Pythona. W archiwum najpierw rozpakuj cały katalog.

Otwórz instrukcję i aplikację w osobnych kartach. Zacznij od odświeżenia aplikacji: mają pozostać **sześć wbudowanych instrumentów przykładowych**. Wybierz kafelek **Polski**. Nie odświeżaj karty aplikacji przed zapisaniem raportu: import jest przechowywany tylko w pamięci tej karty. Preferencja języka może przetrwać odświeżenie. Na telefonie szerokie tabele przewijają się we własnych ramkach; przypisanie kolumn może potrwać dłużej. Zachowanie na Twoim urządzeniu jest częścią testu.

Zapisz czas rozpoczęcia każdego zadania i odnotuj pierwszą przeszkodę. **Samodzielnie** oznacza wykonanie zadania przy korzystaniu z tych trzech instrukcji. **Z pomocą** oznacza dodatkowe skorzystanie z pełnego przewodnika lub pomocy innej osoby. Jeśli potrzebujesz pomocy, możesz skorzystać z [pełnego przewodnika](../walkthrough-pl.html); zaznacz to w opinii. Nie musisz walczyć z blokadą: wynik „nie ukończono” też jest przydatny.

## Zadanie 1 — import i sprawdzenie przeliczenia (6–10 minut)

1. Rozwiń **Zacznij tutaj — przeglądaj, importuj lub utwórz raport**. Wybierz **Otwórz import prywatny**. W polu **Skoroszyt Excel lub plik CSV** wskaż `seasonlens-import-template.xlsx`, ustaw **Datę graniczną analizy** na `2026-10-06`, a następnie wybierz **Otwórz i podejrzyj plik**.
2. Sprawdź poniższe ustawienia. Wiersz 2 opisuje jednostki, a wiersz 3 zawiera wymyślony przykład bieżących notowań z datą 2026-10-07. Import historii zaczyna się od wiersza 4.

| Pole | Wartość |
| --- | --- |
| Arkusz | Prices |
| Wiersz nagłówków | 1 |
| Pierwszy wiersz danych | 4 |
| Kolumna daty | A · Date |
| Data graniczna analizy | 2026-10-06 |
| Format dat zapisanych jako tekst | YYYY-MM-DD |
| Separator dziesiętny cen zapisanych jako tekst | . |

3. W **Wybierz instrumenty z kolumn cen** zaznacz **tylko B i E**; wyłącz C, D, F i G. Jawnie zadeklaruj nazwy, jednostki i role:

| Kolumna | Nazwa instrumentu | Jednostki | Rola |
| --- | --- | --- | --- |
| B | Wheat sample | EUR/t | Pszenica |
| E | EUR/PLN sample | PLN za EUR | EUR/PLN |

W polskim polu jednostek wybierz **PLN za EUR**; wewnętrzna wartość tego wyboru to `PLN per EUR`. Nazwy są dokładnymi wartościami przykładu i pozostają po angielsku. Pozostaw niezaznaczone **Jawnie pomijaj puste komórki cen, z liczbą wierszy** oraz **Użyj zapisanych wyników formuł Excela (mogą być nieaktualne)**.

4. Wybierz **Sprawdź wybrane instrumenty**. Oczekiwany wynik: dwa instrumenty, każdy z **210 obserwacjami**, od **2025-12-17** do **2026-10-06**, **0 pominiętych pustych wartości** i **0 wykluczonych przyszłych wierszy**. Wiersz 3 jest poza wybranym zakresem wierszy, więc nie jest liczony jako pominięty przyszły wiersz. Sam podgląd i sprawdzenie jeszcze nie dodają danych.
5. Wybierz raz **Dodaj sprawdzone instrumenty do tej karty**. Oczekiwane **osiem instrumentów**: sześć przykładów i dwa importy. Zmiana ustawień importu wymaga ponownego sprawdzenia.
6. W **Opcjach analizy** wybierz **Wheat sample · prywatny Excel** i **Jednostki wyświetlania: PLN/t**. Sprawdź 210 par z dokładnie tą samą datą oraz ostatnią obserwację `2026-10-06`. Cena odniesienia przy **Średnich cenach miesięcznych** powinna wynosić **897 PLN/t** po zaokrągleniu.

Kontrola rachunku: `213,29 EUR/t × 4,2051 PLN za EUR = 896,905779 PLN/t`. Używane są kursy z tego samego importu i tych samych dni, bez uzupełniania braków. **USER_FILE** określa sposób importu, nie oficjalne źródło rynku. Ten import przykładowych danych nie zapisuje niczego w SQLite.

**Ukończenie:** oba instrumenty dodane, wybrana prywatna pszenica w PLN/t, 210 obserwacji i cena odniesienia 897. Zanotuj, czy potrzebna była pomoc.

## Zadanie 2 — porównanie miesięczne i pokrycie (4–6 minut)

1. W sekcji Zacznij tutaj wybierz **Pokaż średnie miesięczne**, a następnie **Pokaż ceny z pięciu lat**. Pozostań przy prywatnej pszenicy w PLN/t i dacie granicznej `2026-10-06`.
2. Znajdź zakres **2022–2026**. Odpowiedz własnymi słowami: dlaczego lata 2022–2024 mają luki, co oznaczają kreski i czy ta tabela dowodzi pięcioletniej historii danych?
3. Sprawdź grudzień 2025 i październik 2026. Szablon zaczyna się dopiero **2025-12-17**. Styczeń–listopad 2025 nie mają danych, a listopad–grudzień 2026 są po dacie granicznej. Październik 2026 jest **niepełny, z czterema obserwacjami**.
4. Otwórz **Analizę techniczną — ostatnie 12 miesięcy**. Przy wszystkich sześciu liniach sprawdź, dlaczego SMA200 pojawia się dopiero na końcu. Z 210 obserwacji dostępnych jest **11 wartości SMA200**: pierwsze 199 nie mają pełnego okna. Okno obejmuje obserwacje, a nie gwarantowane dni kalendarzowe.

Średnia miesięczna uśrednia obserwowane ceny dzienne, a przerywana średnia okresu nadaje jednakową wagę dostępnym średnim miesięcznym z poszczególnych lat. W PLN/t uśredniane są dzienne iloczyny ceny i kursu. **Kreska oznacza brak wartości, nie zero.** Wybrany zakres pięciu lat nie tworzy brakującej historii. Ten krótki szablon nie wystarcza do ustalenia wiarygodnej sezonowości. Kolory i średnie nie są sygnałami transakcyjnymi.

**Ukończenie:** potrafisz wyjaśnić luki, niepełny październik i 11 dostępnych wartości SMA200. Zapisz swoją odpowiedź w formularzu opinii, nawet jeśli była potrzebna pomoc.

## Zadanie 3 — zapis wybranego raportu (4–6 minut)

1. Zachowaj prywatną pszenicę, PLN/t, `2026-10-06` i wybrany język. W sekcji Zacznij tutaj wybierz **Otwórz kreator raportu**.
2. Zaznacz tylko trzy sekcje: **Przegląd rynku i dostępność danych**, **Średnie ceny miesięczne i porównanie pięcioletnie**, **Wykres techniczny z wybranymi liniami**. Wyłącz pozostałe; w tym zadaniu nie potrzebujemy sekcji ryzyka.
3. Wybierz **Utwórz podgląd raportu**. Sprawdź trzy sekcje oraz metadane **Wheat sample**, **PLN/t**, **2026-10-06**, **USER_FILE**. Etykiety i opis raportu mają być po polsku; nazwa instrumentu i kody pozostają takie, jak zadeklarowano.
4. Wybierz **Pobierz HTML**, znajdź pobrany plik i otwórz go w przeglądarce. Sprawdź, czy działa jako samodzielny raport, ma te same dane i język. Techniczna kontrola, jeśli umiesz wyświetlić źródło strony: dokument ma `<html lang="pl">` (przy teście angielskim: `en`). Nie trzeba jej wykonywać, aby ukończyć pilotaż.
5. Raport jest stałą kopią: późniejsza zmiana języka lub ustawień aplikacji nie zmienia pobranego pliku. Nowy raport wymaga ponownego utworzenia podglądu. Zapis PDF jest opcjonalny i zależy od systemowego okna drukowania; testujemy pobranie HTML.
6. Dopiero po zapisaniu raportu odśwież kartę aplikacji. Oba importy powinny zniknąć i powinno pozostać **sześć wbudowanych przykładów**. Język może zostać zapamiętany.

**Ukończenie:** pobrany HTML otwiera się, ma trzy wybrane sekcje i prawidłowe metadane/język; odświeżenie usuwa importy. Raport pomija oryginalne tablice obserwacji, ale zawiera widoczne ceny i wyniki. Nie wysyłaj raportów z rzeczywistymi danymi do publicznych zgłoszeń.

## Przekazanie opinii (2–3 minuty)

Wypełnij [FEEDBACK_PL.md](FEEDBACK_PL.md), kopiując treść do wiadomości. Możesz przekazać ją w prywatnej wiadomości osobie, która zaprosiła Cię do testu, bez publikowania na GitHubie. Nie musisz podawać nazwiska, firmy, adresu e-mail ani nazw własnych plików.

Opcjonalnie [utwórz zgłoszenie na GitHubie](https://github.com/eluyz/SeasonLens/issues/new/choose). **Zgłoszenie, konto GitHub i załączniki są publiczne.** Publikuj tylko, jeśli świadomie chcesz udostępnić tę opinię. Opisz kroki na wymyślonym szablonie; nie załączaj rzeczywistych notowań, zrzutów z danymi klientów, prywatnych raportów ani nazw firmowych plików. To ręczne przekazanie opinii: instrukcja nie zawiera formularza, telemetrii ani automatycznego wysyłania wyników.

## Jak odczytamy wyniki pilotażu

Każde zadanie zapisujemy jako: **samodzielnie / z pomocą / nie ukończono / nie podjęto**, wraz z czasem i przeszkodą. Osobno pytamy, do jakiej konkretnej czynności aplikacja mogłaby się przydać i czy chcesz użyć jej ponownie. Ukończenie przykładu nie dowodzi przydatności do rzeczywistego rynku ani niezależnej adopcji. Najpierw poprawimy przeszkody w imporcie, rozumieniu pokrycia i zapisie raportu.
