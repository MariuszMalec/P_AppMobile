import asyncio
import os
import traceback
import logging

import uvicorn
from fastapi import FastAPI


app = FastAPI()


@app.get("/")
def home():
    return {
        "message": "FASTAPI DZIAŁA W APK! 🎉"
    }


def log_file(path, text):
    try:
        with open(path, "a", encoding="utf-8") as f:
            f.write(text + "\n")
            f.flush()
    except Exception:
        pass


async def run_uvicorn(log_path):

    log_file(log_path, "")
    log_file(log_path, "========================================")
    log_file(log_path, "UVICORN SERVE TEST")
    log_file(log_path, f"PID: {os.getpid()}")
    log_file(log_path, "========================================")

    config = uvicorn.Config(
        app,
        host="127.0.0.1",
        port=8000,
        log_level="debug",
        loop="asyncio",
        lifespan="off",
        log_config=None,
        access_log=True,
    )

    log_file(log_path, "Config utworzony.")

    server = uvicorn.Server(config)

    log_file(log_path, "Server utworzony.")
    log_file(log_path, f"should_exit = {server.should_exit}")

    try:
        log_file(log_path, "Wywołuję server.serve()...")

        await server.serve()

        log_file(log_path, "server.serve() zakończone normalnie.")
        log_file(log_path, f"should_exit = {server.should_exit}")

        return "UVICORN SERVE OK"

    except SystemExit as e:

        log_file(log_path, "!!! UVICORN SYSTEMEXIT !!!")
        log_file(log_path, f"CODE = {e.code}")
        log_file(log_path, traceback.format_exc())

        return f"UVICORN SYSTEMEXIT: {e.code}"

    except BaseException as e:

        log_file(log_path, "!!! UVICORN BŁĄD !!!")
        log_file(log_path, repr(e))
        log_file(log_path, traceback.format_exc())

        return f"UVICORN ERROR: {repr(e)}"


def start_server(log_path):

    log_file(log_path, "start_server()")
    log_file(log_path, f"log_path = {log_path}")

    try:

        result = asyncio.run(
            run_uvicorn(log_path)
        )

        log_file(log_path, f"WYNIK: {result}")

        return result

    except BaseException as e:

        log_file(log_path, "!!! start_server BŁĄD !!!")
        log_file(log_path, repr(e))
        log_file(log_path, traceback.format_exc())

        return f"START ERROR: {repr(e)}"
