from fastapi import APIRouter, Request, Depends, Query
from fastapi.responses import HTMLResponse

from templates import templates
from db import get_db
from services.results import get_result_status


router = APIRouter(prefix="/teams", tags=["team-trophy-matrix"])


@router.get("/trophy-matrix", response_class=HTMLResponse)
def trophy_matrix(
    request: Request,
    name: str = Query(None),
    team_id: int = Query(None),
    db=Depends(get_db),
):
    try:
        cur = db.cursor()

        names = [
            r["Name"]
            for r in cur.execute(
                "SELECT DISTINCT Name FROM Teams ORDER BY Name ASC"
            ).fetchall()
        ]

        if team_id and not name:
            row = cur.execute(
                "SELECT Name FROM Teams WHERE Id = ?", (team_id,)
            ).fetchone()
            name = row["Name"] if row else None

        seasons, trophies, cells = [], {}, {}

        if name:
            rows = cur.execute(
                """
                SELECT Teams.Season, Teams.FinalResult, Teams.TrophyModelId,
                       Trophies.Name AS TrophyName,
                       Trophies.Picture AS TrophyPicture
                FROM Teams
                LEFT JOIN Trophies ON Trophies.Id = Teams.TrophyModelId
                WHERE Teams.Name = ?
                ORDER BY Teams.Season ASC
                """,
                (name,),
            ).fetchall()

            season_set = set()
            for r in rows:
                season_set.add(r["Season"])
                tid = r["TrophyModelId"]
                if not tid:
                    continue
                trophies.setdefault(
                    tid,
                    {
                        "id": tid,
                        "name": r["TrophyName"],
                        "picture": r["TrophyPicture"],
                    },
                )
                lose = get_result_status(r["FinalResult"], name)["lose"]
                cells.setdefault(r["Season"], {})[tid] = (
                    "lose" if lose else "win"
                )
            seasons = sorted(season_set)

        trophy_list = sorted(trophies.values(), key=lambda t: t["name"] or "")

        totals = {
            t["id"]: {
                "win": sum(1 for s in seasons if cells.get(s, {}).get(t["id"]) == "win"),
                "lose": sum(1 for s in seasons if cells.get(s, {}).get(t["id"]) == "lose"),
            }
            for t in trophy_list
        }

        return templates.TemplateResponse(
            request,
            "team_trophy_matrix.html",
            {
                "names": names,
                "name": name,
                "seasons": seasons,
                "trophies": trophy_list,
                "cells": cells,
                "totals": totals,
            },
        )
    finally:
        db.close()
