import os
import sqlite3
import tempfile
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask

router = APIRouter(tags=["backup"])


def _remove_temp_file(path: Path):
    try:
        path.unlink(missing_ok=True)
    except OSError:
        pass


@router.get("/api/backup/export")
def export_database():
    db_path = Path(os.environ.get(
        "DATABASE_PATH",
        str(Path(__file__).resolve().parents[1] / "meetings.db")
    ))

    if not db_path.is_file():
        raise HTTPException(status_code=404, detail="Nie znaleziono bazy danych.")

    temp_file = tempfile.NamedTemporaryFile(
        prefix="meetings-export-",
        suffix=".db",
        delete=False
    )
    temp_path = Path(temp_file.name)
    temp_file.close()

    try:
        with sqlite3.connect(str(db_path), timeout=10) as source:
            with sqlite3.connect(str(temp_path), timeout=10) as destination:
                source.backup(destination)
                check = destination.execute("PRAGMA integrity_check").fetchone()

        if not check or check[0] != "ok":
            raise RuntimeError("Kontrola spójności kopii bazy nie powiodła się.")

        return FileResponse(
            path=str(temp_path),
            media_type="application/octet-stream",
            filename="meetings.db",
            background=BackgroundTask(_remove_temp_file, temp_path)
        )

    except Exception as exc:
        temp_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=500,
            detail=f"Nie udało się wyeksportować bazy: {exc}"
        ) from exc


@router.post("/api/backup/import")
async def import_database(file: UploadFile = File(...)):
    """Sprawdza bazę, tworzy kopię bezpieczeństwa i importuje dane."""
    db_path = Path(os.environ.get(
        "DATABASE_PATH",
        str(Path(__file__).resolve().parents[1] / "meetings.db")
    ))
    if not db_path.is_file():
        raise HTTPException(status_code=404, detail="Nie znaleziono aktualnej bazy.")

    if not (file.filename or "").lower().endswith(".db"):
        raise HTTPException(status_code=400, detail="Wybierz plik z rozszerzeniem .db.")

    temp_path = None
    backup_path = None
    backup_created = False
    try:
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as temp:
            temp_path = Path(temp.name)
            total = 0
            while True:
                chunk = await file.read(1024 * 1024)
                if not chunk:
                    break
                total += len(chunk)
                if total > 100 * 1024 * 1024:
                    raise HTTPException(status_code=413, detail="Maksymalny rozmiar pliku to 100 MB.")
                temp.write(chunk)

        if total == 0:
            raise HTTPException(status_code=400, detail="Plik jest pusty.")

        try:
            with sqlite3.connect(temp_path.resolve().as_uri() + "?mode=ro", uri=True) as incoming:
                check = incoming.execute("PRAGMA integrity_check").fetchone()
                tables = {r[0] for r in incoming.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                )}
                if not check or check[0] != "ok":
                    raise HTTPException(status_code=400, detail="Baza SQLite jest uszkodzona.")
                if not {"Client", "Session"}.issubset(tables):
                    raise HTTPException(status_code=400, detail="Brakuje tabel Client lub Session.")

                required = {
                    "Client": {"Id", "FirstName", "LastName", "Age", "Description", "Phone", "Gender", "IsActive"},
                    "Session": {"Id", "ClientId", "StartTime", "EndTime", "Description", "DayOfWeek", "SessionDate", "RecurringGroupId", "RepeatEveryWeeks", "IsActive"}
                }
                for table, columns in required.items():
                    actual = {r[1] for r in incoming.execute(f'PRAGMA table_info("{table}")')}
                    if not columns.issubset(actual):
                        raise HTTPException(
                            status_code=400,
                            detail=f"Niezgodny schemat tabeli {table}. Wybierz bazę z aktualnej wersji aplikacji."
                        )
                if incoming.execute("PRAGMA foreign_key_check").fetchall():
                    raise HTTPException(status_code=400, detail="Baza zawiera nieprawidłowe powiązania.")
        except HTTPException:
            raise
        except sqlite3.Error as exc:
            raise HTTPException(status_code=400, detail="Wybrany plik nie jest poprawną bazą SQLite.") from exc

        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup_path = db_path.parent / f"meetings-before-import-{stamp}.db"
        with sqlite3.connect(str(db_path), timeout=30) as current:
            with sqlite3.connect(str(backup_path), timeout=30) as backup:
                current.backup(backup)
                if backup.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                    raise RuntimeError("Nie udało się sprawdzić kopii bezpieczeństwa.")
        backup_created = True

        try:
            with sqlite3.connect(str(temp_path), timeout=30) as incoming:
                with sqlite3.connect(str(db_path), timeout=30) as target:
                    incoming.backup(target)
                    if target.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                        raise RuntimeError("Kontrola zaimportowanej bazy nie powiodła się.")
        except Exception:
            with sqlite3.connect(str(backup_path), timeout=30) as backup:
                with sqlite3.connect(str(db_path), timeout=30) as target:
                    backup.backup(target)
            raise

        return {"ok": True, "message": "Import zakończony.", "backup": backup_path.name}
    except HTTPException:
        raise
    except Exception as exc:
        detail = "Nie udało się zaimportować bazy."
        if backup_created and backup_path:
            detail += f" Kopia bezpieczeństwa: {backup_path.name}"
        raise HTTPException(status_code=500, detail=detail) from exc
    finally:
        await file.close()
        if temp_path:
            try:
                temp_path.unlink(missing_ok=True)
            except OSError:
                pass
