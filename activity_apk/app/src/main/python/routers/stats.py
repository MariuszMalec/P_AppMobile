from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse

from templates import templates
from validators import time_to_minutes
from db import get_db

router = APIRouter(prefix="/stats", tags=["stats"])

DAY_TABS = [
    (0, "Tydzień"), (2, "Pn"), (3, "Wt"), (4, "Śr"),
    (5, "Cz"), (6, "Pt"), (7, "So"), (1, "Nd"),
]


@router.get("", response_class=HTMLResponse)
def stats_page(request: Request, day: int = 0, db=Depends(get_db)):
    cur = db.cursor()

    persons = [
        {"id": r["Id"], "name": r["PersonName"]}
        for r in cur.execute(
            "SELECT Id, PersonName FROM PersonFamilies "
            "WHERE PersonName != 'RODZINA' ORDER BY Id"
        ).fetchall()
    ]

    sql = """
        SELECT ad.StartTime, ad.EndTime, ad.ModelPersonFamilyId AS Pid,
               COALESCE(pa.Name, 'Brak') AS Act
        FROM ActiviesDays ad
        LEFT JOIN PictureActivities pa ON ad.ModelPictureActivityId = pa.Id
    """
    if 1 <= day <= 7:
        rows = cur.execute(sql + " WHERE ad.DayOfWeek = ?", (day,)).fetchall()
    else:
        day = 0
        rows = cur.execute(sql).fetchall()
    db.close()

    pids = [p["id"] for p in persons]
    acts = {}
    totals = {pid: {"n": 0, "min": 0} for pid in pids}

    for r in rows:
        pid = r["Pid"]
        if pid not in totals:
            continue
        dur = (time_to_minutes(r["EndTime"]) - time_to_minutes(r["StartTime"])) % 1440
        a = acts.setdefault(r["Act"], {i: {"n": 0, "min": 0} for i in pids})
        a[pid]["n"] += 1
        a[pid]["min"] += dur
        totals[pid]["n"] += 1
        totals[pid]["min"] += dur

    out = []
    for name, cells in acts.items():
        counts = [cells[i]["n"] for i in pids]
        mx, mn, tot = max(counts), min(counts), sum(counts)
        if mx - mn <= 1:
            verdict, level = "równo", "ok"
        else:
            lead = persons[counts.index(mx)]["name"]
            verdict, level = f"przechył: {lead} {round(mx * 100 / tot)}%", "warn"
        out.append({
            "name": name.replace("_", " "),
            "total": tot,
            "verdict": verdict,
            "level": level,
            "cells": [
                {"n": cells[i]["n"], "pct": round(cells[i]["n"] * 100 / mx) if mx else 0}
                for i in pids
            ],
        })
    out.sort(key=lambda x: -x["total"])

    return templates.TemplateResponse(
        request,
        "stats.html",
        {
            "persons": persons,
            "rows": out,
            "totals": [totals[i] for i in pids],
            "tabs": DAY_TABS,
            "day": day,
        },
    )
