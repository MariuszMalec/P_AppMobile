def list_trophies(db):
    rows = db.execute(
        """
        SELECT Trophies.*, Teams.Name AS TeamName
        FROM Trophies
        LEFT JOIN Teams ON Teams.Id = Trophies.TeamModelId
        ORDER BY Trophies.Name ASC
        """
    ).fetchall()
    return [dict(r) for r in rows]


def update_trophy(db, trophy_id, data):
    cur = db.cursor()
    existing = cur.execute(
        "SELECT * FROM Trophies WHERE Id = ?", (trophy_id,)
    ).fetchone()
    if not existing:
        return None

    name = (data.get("Name") or "").strip()
    if not name:
        raise ValueError("Trophy name cannot be empty")

    cur.execute(
        """
        UPDATE Trophies
        SET Name = ?, Description = ?, Picture = ?, TeamModelId = ?
        WHERE Id = ?
        """,
        (
            name,
            data.get("Description", existing["Description"]),
            data.get("Picture", existing["Picture"]),
            data.get("TeamModelId", existing["TeamModelId"]),
            trophy_id,
        ),
    )
    db.commit()
    return {"status": "ok", "Id": trophy_id}
