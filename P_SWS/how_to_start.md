## Win
0. cd P_FastApi
1. python -m venv venv (opcjonalnie jesli nie ma katalogu)
2. venv\Scripts\activate   # Windows
3. pip install -r requirements.txt (jesli brak bibliotek!)
4. uvicorn app:app --reload

API:

http://127.0.0.1:8000/teams

http://127.0.0.1:8000/trophies

UI:

http://127.0.0.1:8000/ui/teams

http://127.0.0.1:8000/ui/trophies

Swagger:

http://127.0.0.1:8000/docs
 🔥


## Linux
 
 ## mobile
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app:app