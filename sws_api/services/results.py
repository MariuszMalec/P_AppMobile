import re


def get_result_status(result: str | None, team_name: str) -> dict:
    """
    Odpowiednik Reactowego getResultStatus().

    Zwraca:
        {
            "display_result": str,
            "lose": bool,
        }
    """

    value = result or ""
    lose = False
    display_result = value

    # =========================
    # Wstępne ustalenie statusu
    # =========================

    if value and "winner" in value.lower():
        lose = False

    elif value and ":" not in value:
        lose = True

    elif value and "round" in value.lower():
        lose = True

    if value and ":" not in value:
        lose = True

    if value and "round" in value.lower():
        lose = True

    # =========================
    # Wynik z karnymi
    # =========================

    if "PEN" in value and ":" in value:
        main_part = value.split("(", 1)[0].strip()

        pen_parts = value.split("PEN", 1)

        if len(pen_parts) == 2:
            pen_part = (
                pen_parts[1]
                .replace("(", "")
                .replace(")", "")
                .strip()
            )

            space_index = main_part.find(" ")

            if space_index != -1:
                teams_part = main_part[:space_index].strip()
                score_part = main_part[space_index + 1:].strip()

                teams = teams_part.split(":", 1)
                scores = score_part.split(":", 1)
                pens = pen_part.split(":", 1)

                if (
                    len(teams) == 2
                    and len(scores) == 2
                    and len(pens) == 2
                ):
                    team_a = teams[0].strip()
                    team_b = teams[1].strip()

                    goals_a = scores[0].strip()
                    goals_b = scores[1].strip()

                    pen_a = pens[0].strip()
                    pen_b = pens[1].strip()

                    if (
                        re.fullmatch(r"\d+", goals_a)
                        and re.fullmatch(r"\d+", goals_b)
                        and re.fullmatch(r"\d+", pen_a)
                        and re.fullmatch(r"\d+", pen_b)
                    ):
                        if (
                            team_name == team_a
                            and int(pen_a) < int(pen_b)
                        ):
                            lose = True

                        elif (
                            team_name == team_b
                            and int(pen_b) < int(pen_a)
                        ):
                            lose = True

    # =========================
    # Wynik po dogrywce
    # =========================

    elif "A.E.T" in value and ":" in value:
        main_part = value.split("(", 1)[0].strip()
        space_index = main_part.find(" ")

        if space_index != -1:
            teams = (
                main_part[:space_index]
                .strip()
                .split(":", 1)
            )

            scores = (
                main_part[space_index + 1:]
                .strip()
                .split(":", 1)
            )

            if len(teams) == 2 and len(scores) == 2:
                team_a = teams[0].strip()
                team_b = teams[1].strip()

                goals_a = scores[0].strip()
                goals_b = scores[1].strip()

                if (
                    re.fullmatch(r"\d+", goals_a)
                    and re.fullmatch(r"\d+", goals_b)
                ):
                    if (
                        team_name == team_a
                        and int(goals_a) < int(goals_b)
                    ):
                        lose = True

                    elif (
                        team_name == team_b
                        and int(goals_b) < int(goals_a)
                    ):
                        lose = True

    # =========================
    # Normalny wynik
    # =========================

    elif " " in value and ":" in value:
        space_index = value.find(" ")

        teams = (
            value[:space_index]
            .strip()
            .split(":", 1)
        )

        scores = (
            value[space_index + 1:]
            .strip()
            .split(":", 1)
        )

        if len(teams) == 2 and len(scores) == 2:
            team_a = teams[0].strip()
            team_b = teams[1].strip()

            goals_a = scores[0].strip()
            goals_b = scores[1].strip()

            if (
                re.fullmatch(r"\d+", goals_a)
                and re.fullmatch(r"\d+", goals_b)
            ):
                if (
                    team_name == team_a
                    and int(goals_a) < int(goals_b)
                ):
                    lose = True

                elif (
                    team_name == team_b
                    and int(goals_b) < int(goals_a)
                ):
                    lose = True

    # =========================
    # Stary format
    # np. Parma:Ajax2:0
    # =========================

    elif ":" in value:
        parts = value.split(":")

        if len(parts) == 3:
            possible_team_a = parts[0].strip()
            possible_team_b_with_score = parts[1].strip()
            goals_b = parts[2].strip()

            if re.fullmatch(r"\d+", goals_b):

                if team_name == possible_team_a:
                    goals_a = possible_team_b_with_score[-1:]

                    if re.fullmatch(r"\d", goals_a):
                        team_b = possible_team_b_with_score[:-1].strip()

                        display_result = (
                            f"{possible_team_a}:{team_b} "
                            f"{int(goals_a)}:{int(goals_b)}"
                        )

                        if int(goals_a) < int(goals_b):
                            lose = True

                elif possible_team_b_with_score.endswith(team_name):
                    score_text = (
                        possible_team_b_with_score[
                            :-len(team_name)
                        ].strip()
                    )

                    if re.fullmatch(r"\d+", score_text):
                        display_result = (
                            f"{possible_team_a}:{team_name} "
                            f"{int(score_text)}:{int(goals_b)}"
                        )

                        if int(goals_b) < int(score_text):
                            lose = True

    # =========================
    # Ostateczne ustalenie
    # =========================

    if value and "winner" in value.lower():
        lose = False

    elif value and "round" in value.lower():
        lose = True

    elif value and ":" not in value:
        lose = True

    return {
        "display_result": display_result,
        "lose": lose,
    }
