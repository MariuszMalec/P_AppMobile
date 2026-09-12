import asyncio
import os
import shutil
import traceback
from pathlib import Path

import uvicorn


def log_file(path, text):
    try:
        with open(path, "a", encoding="utf-8") as f:
            f.write(text + "\n")
            f.flush()
    except Exception:
        pass


def prepare_database(log_path):
    """
    Przygotowuje zapisywalną bazę SQLite w katalogu
    prywatnych danych aplikacji Android.

    activity.db znajdujący się obok kodu Python jest
    bazą startową wbudowaną w APK.
    """

    log_dir = Path(log_path).resolve().parent
    writable_db = log_dir / "activity.db"

    bundled_db = (
        Path(__file__).resolve().parent / "activity.db"
    )

    log_file(log_path, "========================================")
    log_file(log_path, "PRZYGOTOWANIE BAZY SQLITE")
    log_file(log_path, f"Baza w APK: {bundled_db}")
    log_file(log_path, f"Baza robocza: {writable_db}")

    if not writable_db.exists():

        log_file(
            log_path,
            "Baza robocza nie istnieje."
        )

        log_file(
            log_path,
            "Kopiuję bazę startową z APK..."
        )

        shutil.copy2(
            bundled_db,
            writable_db
        )

        log_file(
            log_path,
            "Baza została skopiowana."
        )

    else:

        log_file(
            log_path,
            "Baza robocza już istnieje."
        )

    os.environ["DATABASE_PATH"] = str(
        writable_db
    )

    log_file(
        log_path,
        f"DATABASE_PATH = {writable_db}"
    )

    log_file(
        log_path,
        "========================================"
    )

    return writable_db


async def run_server(log_path):

    log_file(log_path, "")
    log_file(
        log_path,
        "========================================"
    )
    log_file(
        log_path,
        "ACTIVITY APK - START FASTAPI"
    )
    log_file(
        log_path,
        f"PID: {os.getpid()}"
    )
    log_file(
        log_path,
        "========================================"
    )

    try:

        # -----------------------------------------
        # BAZA
        # -----------------------------------------

        writable_db = prepare_database(
            log_path
        )

        # -----------------------------------------
        # IMPORT APLIKACJI FASTAPI
        # -----------------------------------------

        log_file(
            log_path,
            "Importuję main:app..."
        )

        import main

        # main.py ma własne:
        #
        # DB_PATH = Path(__file__).parent / "activity.db"
        #
        # Podmieniamy je na bazę zapisywalną
        # w pamięci aplikacji Android.

        main.DB_PATH = writable_db

        log_file(
            log_path,
            "main:app zaimportowane."
        )

        log_file(
            log_path,
            f"main.DB_PATH = {main.DB_PATH}"
        )

        app = main.app

        # -----------------------------------------
        # UVICORN
        # -----------------------------------------

        config = uvicorn.Config(
            app,
            host="127.0.0.1",
            port=8000,
            log_level="info",
            loop="asyncio",
            log_config=None,
            access_log=True,
        )

        log_file(
            log_path,
            "Konfiguracja Uvicorn utworzona."
        )

        server = uvicorn.Server(config)

        log_file(
            log_path,
            "Uvicorn Server utworzony."
        )

        log_file(
            log_path,
            "Uruchamiam server.serve()..."
        )

        log_file(
            log_path,
            "========================================"
        )

        await server.serve()

        log_file(
            log_path,
            "server.serve() zakończone."
        )

    except BaseException as e:

        log_file(
            log_path,
            "!!! BŁĄD STARTU ACTIVITY !!!"
        )

        log_file(
            log_path,
            repr(e)
        )

        log_file(
            log_path,
            traceback.format_exc()
        )

        raise


def start_server(log_path):

    log_file(
        log_path,
        "start_server()"
    )

    log_file(
        log_path,
        f"log_path = {log_path}"
    )

    try:

        asyncio.run(
            run_server(log_path)
        )

    except BaseException as e:

        log_file(
            log_path,
            "!!! start_server BŁĄD !!!"
        )

        log_file(
            log_path,
            repr(e)
        )

        log_file(
            log_path,
            traceback.format_exc()
        )

        return f"START ERROR: {repr(e)}"

    return "SERVER STOPPED"
