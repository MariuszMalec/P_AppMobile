from collections import Counter
from services.results import get_result_status


def top(counter, n=5):
    items = counter.most_common(n)
    mx = items[0][1] if items else 1
    return [{"label": k, "value": v, "pct": round(v * 100 / mx)} for k, v in items]


def get_insights(db):
    insights = {
        "by_team": [], "by_trophy": [], "lost_trophy": [], "scorers": [],
        "countries": [], "seasons": [],
        "wins": 0, "losses": 0, "rate": 0,
    }
    try:
        rows = db.cursor().execute(
            """
            SELECT Teams.Name, Teams.NationalityName, Teams.Season,
                   Teams.TopScorer, Teams.FinalResult, Teams.TrophyModelId,
                   Trophies.Name AS TrophyName
            FROM Teams
            LEFT JOIN Trophies ON Trophies.Id = Teams.TrophyModelId
            """
        ).fetchall()

        by_team, by_trophy, lost_trophy = Counter(), Counter(), Counter()
        countries, seasons, scorers = Counter(), Counter(), Counter()
        seen_scorer = set()
        wins = losses = 0

        for r in rows:
            key = (r["Name"], r["Season"], r["TopScorer"])
            if r["TopScorer"] and key not in seen_scorer:
                seen_scorer.add(key)
                scorers[r["TopScorer"]] += 1

            if not r["TrophyModelId"]:
                continue

            if get_result_status(r["FinalResult"], r["Name"])["lose"]:
                losses += 1
                lost_trophy[r["TrophyName"] or "?"] += 1
            else:
                wins += 1
                by_team[r["Name"]] += 1
                by_trophy[r["TrophyName"] or "?"] += 1
                if r["NationalityName"]:
                    countries[r["NationalityName"]] += 1
                seasons[str(r["Season"])] += 1

        total = wins + losses
        insights = {
            "by_team": top(by_team), "by_trophy": top(by_trophy),
            "lost_trophy": top(lost_trophy),
            "scorers": top(scorers), "countries": top(countries),
            "seasons": top(seasons),
            "wins": wins, "losses": losses,
            "rate": round(wins * 100 / total) if total else 0,
        }
    except Exception:
        pass
    return insights
