venv/bin/activate   
uvicorn main:app --host 0.0.0.0 --port 8001 --reload 

oraz testy

pytest -v tests/test_validators.py

na komorce testy dzialaja tylko tak:

python -m pytest -q

## BUDOWANIE APKI NA TELEFON (Termux)

Jedna komenda (z dowolnego katalogu):

    ~/projects/P_AppMobile/build_meetings_apk.sh

Co robi skrypt:
1. npm run build w Meetings_react (tworzy dist)
2. podnosi versionCode w Meetings_apk/app/build.gradle o 1
3. gradlew assembleRelease --rerun-tasks
   (gradle sam kopiuje API z Meetings_api i React z dist do apki)
4. kopiuje APK do ~/storage/downloads/Meetings.apk

Potem: otworz Meetings.apk z Pobranych i kliknij Aktualizuj
(NIE odinstalowuj, bo skasujesz baze).

Zasady:
- Kod API zmieniaj w Meetings_api, React w Meetings_react.
  Nie edytuj kopii w Meetings_apk/app/src/main/python
  (gradle ja nadpisuje). Wyjatki: main.py i server.py, tylko tam.
- versionCode musi rosnac, inaczej telefon nie zaktualizuje apki.
- Gdy zmian nie widac po instalacji: Ustawienia > Aplikacje > apka >
  Pamiec > Wyczysc pamiec podreczna (NIE dane).
