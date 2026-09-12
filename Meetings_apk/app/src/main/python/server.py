import asyncio
import os
import sys
import shutil
import traceback
import uvicorn

DATABASE_PATH = None


def log_message(log_path, message):
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(message + "\n")


def prepare_database(log_path):
    global DATABASE_PATH

    base_dir = os.path.dirname(os.path.abspath(__file__))

    bundled_db = os.path.join(base_dir, "meetings.db")

    writable_dir = os.path.dirname(log_path)
    writable_db = os.path.join(writable_dir, "meetings.db")

    log_message(log_path, "=== PREPARE DATABASE ===")
    log_message(log_path, f"base_dir={base_dir}")
    log_message(log_path, f"bundled_db={bundled_db}")
    log_message(log_path, f"writable_dir={writable_dir}")
    log_message(log_path, f"writable_db={writable_db}")

    if not os.path.exists(bundled_db):
        log_message(log_path, "BLAD: brak bundled meetings.db")
        raise FileNotFoundError(bundled_db)

    if not os.path.exists(writable_db):
        shutil.copy2(bundled_db, writable_db)
        log_message(log_path, "Skopiowano meetings.db do katalogu zapisywalnego")
    else:
        log_message(log_path, "Writable meetings.db juz istnieje")

    DATABASE_PATH = writable_db

    # KLUCZOWE:
    # db.py korzysta z os.getenv("DATABASE_PATH")
    os.environ["DATABASE_PATH"] = DATABASE_PATH

    log_message(log_path, f"DATABASE_PATH ustawiony: {DATABASE_PATH}")
    log_message(log_path, f"DB istnieje: {os.path.exists(DATABASE_PATH)}")


async def run_server(log_path):

    log_message(log_path, "=== START SERVER ===")
    log_message(log_path, f"sys.executable={sys.executable}")
    log_message(log_path, f"cwd={os.getcwd()}")
    log_message(log_path, f"__file__={__file__}")
    log_message(log_path, f"sys.path={sys.path}")

    try:
        prepare_database(log_path)

        import importlib.util

        spec = importlib.util.find_spec("main")
        log_message(log_path, f"find_spec('main') = {spec}")

        import main

        log_message(log_path, "main import OK")
        log_message(log_path, f"main.__file__={main.__file__}")

        # Zachowujemy również DB_PATH z main.py,
        # jeśli gdzieś w kodzie jest używany.
        main.DB_PATH = DATABASE_PATH

        log_message(log_path, f"main.DB_PATH={main.DB_PATH}")
        log_message(log_path, f"os.environ DATABASE_PATH={os.getenv('DATABASE_PATH')}")

        app = main.app

        log_message(log_path, "FASTAPI APP ZAIMPORTOWANA")
        log_message(log_path, "START UVICORN")

        config = uvicorn.Config(
            app,
            host="127.0.0.1",
            port=8000,
            log_level="info",
            access_log=True,
            log_config=None,
        )

        server = uvicorn.Server(config)

        await server.serve()

    except Exception as e:
        log_message(log_path, "=== SERVER ERROR ===")
        log_message(log_path, repr(e))
        log_message(log_path, traceback.format_exc())

        raise


def start_server(log_path):
    asyncio.run(run_server(log_path))
