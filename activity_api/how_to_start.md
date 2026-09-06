venv/bin/activate   
uvicorn main:app --host 0.0.0.0 --port 8001 --reload 

oraz testy
pytest -v tests/test_add_validators.py