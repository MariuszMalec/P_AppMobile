## Win
0. cd P_Activity
1.py -3.12 -m venv venv
2..\venv\Scripts\Activate.ps1
3.pip install -r requirements.txt
4.uvicorn activity_api:app --reload

👉 http://127.0.0.1:8000/

👉 http://127.0.0.1:8000/status

👉 http://127.0.0.1:8000/week

👉 http://127.0.0.1:8000/api/activities

👉 http://127.0.0.1:8000/docs
 (Swagger 🔥)


## Linux
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn activity_api:app

## Mobile
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn activity_api:app
