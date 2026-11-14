from datetime import date, timedelta

from fastapi import APIRouter, Depends, Request, Query
from fastapi.responses import HTMLResponse

from db import get_db
from templates import templates

router = APIRouter(prefix="/stats", tags=["stats"])

MONTHS = ["Styczeń", "Luty", "Marzec", "Kwiecień", "Maj", "Czerwiec",
          "Lipiec", "Sierpień", "Wrzesień", "Październik", "Listopad",
          "Grudzień"]
MONTHS_SHORT = ["Sty", "Lut", "Mar", "Kwi", "Maj", "Cze",
                "Lip", "Sie", "Wrz", "Paź", "Lis", "Gru"]
WEEKDAYS = ["Poniedziałek", "Wtorek", "Środa", "Czwartek",
            "Piątek", "Sobota", "Niedziela"]

DUR = (
    "(CAST(substr(s.EndTime,1,2) AS INTEGER)*60"
    "+CAST(substr(s.EndTime,4,2) AS INTEGER))"
    "-(CAST(substr(s.StartTime,1,2) AS INTEGER)*60"
    "+CAST(substr(s.StartTime,4,2) AS INTEGER))"
)
BASE = (
    "FROM Session s JOIN Client c ON c.Id = s.ClientId "
    "WHERE c.IsActive = 1 AND s.SessionDate BETWEEN ? AND ?"
)

# ---------------------------------------------------------
# REJESTR SEKCJI: nowa statystyka = nowa funkcja z @section
# Funkcja dostaje ctx i zwraca słownik:
#   title, type ("cards" | "bars" | "hbars"), items
#   item: label, value, sub (opcj.), highlight (opcj.), color (opcj.)
# ---------------------------------------------------------
SECTIONS = []


def section(func):
    SECTIONS.append(func)
    return func


def month_bounds(today, offset):
    y, m = divmod(today.year * 12 + (today.month - 1) + offset, 12)
    first = date(y, m + 1, 1)
    ny, nm = divmod(y * 12 + m + 1, 12)
    last = date(ny, nm + 1, 1) - timedelta(days=1)
    return first, last


def count_range(db, d1, d2):
    row = db.execute(
        f"SELECT COUNT(*) AS n, COALESCE(SUM({DUR}),0) AS m {BASE}",
        (d1.isoformat(), d2.isoformat())
    ).fetchone()
    return row["n"], round(row["m"] / 60, 1)


@section
def summary(ctx):
    db, today = ctx["db"], ctx["today"]
    monday = today - timedelta(days=today.weekday())
    periods = [
        ("Dziś", today, today),
        ("Ten tydzień", monday, monday + timedelta(days=6)),
        ("Ten miesiąc", *month_bounds(today, 0)),
        ("Ten rok", date(today.year, 1, 1), date(today.year, 12, 31)),
    ]
    items = []
    for label, d1, d2 in periods:
        n, h = count_range(db, d1, d2)
        items.append({"label": label, "value": n, "sub": f"{h} h"})
    return {"title": "Podsumowanie", "type": "cards", "items": items}


@section
def days_in_month(ctx):
    db, today = ctx["db"], ctx["today"]
    first, last = month_bounds(today, ctx["month_offset"])
    rows = db.execute(
        f"SELECT s.SessionDate AS d, COUNT(*) AS n {BASE} "
        "GROUP BY s.SessionDate",
        (first.isoformat(), last.isoformat())
    ).fetchall()
    by_day = {r["d"]: r["n"] for r in rows}
    items = []
    d = first
    while d <= last:
        items.append({
            "label": str(d.day),
            "value": by_day.get(d.isoformat(), 0),
            "highlight": d == today,
        })
        d += timedelta(days=1)
    return {"title": f"Sesje w dniach – {ctx['month_label']}",
            "type": "bars", "items": items}


@section
def last_weeks(ctx):
    db, today = ctx["db"], ctx["today"]
    monday = today - timedelta(days=today.weekday())
    items = []
    for i in range(11, -1, -1):
        start = monday - timedelta(weeks=i)
        n, h = count_range(db, start, start + timedelta(days=6))
        items.append({"label": start.strftime("%d.%m"), "value": n,
                      "sub": f"{h} h", "highlight": i == 0})
    return {"title": "Ostatnie 12 tygodni", "type": "bars",
            "items": items}


@section
def last_months(ctx):
    db, today = ctx["db"], ctx["today"]
    items = []
    for i in range(-11, 1):
        first, last = month_bounds(today, i)
        n, h = count_range(db, first, last)
        items.append({
            "label": f"{MONTHS_SHORT[first.month - 1]} {str(first.year)[2:]}",
            "value": n, "sub": f"{h} h", "highlight": i == 0})
    return {"title": "Ostatnie 12 miesięcy", "type": "bars",
            "items": items}


@section
def weekdays(ctx):
    db, today = ctx["db"], ctx["today"]
    rows = db.execute(
        f"SELECT strftime('%w', s.SessionDate) AS w, COUNT(*) AS n {BASE} "
        "GROUP BY w",
        (date(today.year, 1, 1).isoformat(),
         date(today.year, 12, 31).isoformat())
    ).fetchall()
    by = {int(r["w"]): r["n"] for r in rows}
    items = []
    for i, name in enumerate(WEEKDAYS):
        sqlite_w = (i + 1) % 7   # 0 = niedziela
        items.append({"label": name, "value": by.get(sqlite_w, 0)})
    return {"title": f"Dni tygodnia – {today.year}", "type": "hbars",
            "items": items}


@section
def top_clients(ctx):
    db, today = ctx["db"], ctx["today"]
    first, last = month_bounds(today, ctx["month_offset"])
    rows = db.execute(
        f"SELECT c.FirstName AS f, c.LastName AS l, c.Color AS color, "
        f"COUNT(*) AS n, COALESCE(SUM({DUR}),0) AS m {BASE} "
        "GROUP BY c.Id ORDER BY n DESC, m DESC LIMIT 8",
        (first.isoformat(), last.isoformat())
    ).fetchall()
    items = [{
        "label": f"{r['f'] or ''} {r['l'] or ''}".strip(),
        "value": r["n"],
        "sub": f"{round(r['m'] / 60, 1)} h",
        "color": r["color"] or "",
    } for r in rows]
    return {"title": f"Klienci – {ctx['month_label']}",
            "type": "hbars", "items": items}


def collect(db, month_offset=0):
    today = date.today()
    first, _ = month_bounds(today, month_offset)
    ctx = {
        "db": db,
        "today": today,
        "month_offset": month_offset,
        "month_label": f"{MONTHS[first.month - 1]} {first.year}",
    }
    sections = []
    for func in SECTIONS:
        sec = func(ctx)
        sec["key"] = func.__name__
        peak = max([i["value"] for i in sec["items"]] or [0])
        for it in sec["items"]:
            it["pct"] = round(it["value"] / peak * 100, 1) if peak else 0
        sections.append(sec)
    return {
        "generated": today.isoformat(),
        "month_offset": month_offset,
        "month_label": ctx["month_label"],
        "sections": sections,
    }


@router.get("/", response_class=HTMLResponse)
def stats_page(request: Request, db=Depends(get_db),
               month_offset: int = Query(0)):
    return templates.TemplateResponse(
        request, "stats.html", collect(db, month_offset)
    )


@router.get("/api")
def stats_api(db=Depends(get_db), month_offset: int = Query(0)):
    return collect(db, month_offset)
