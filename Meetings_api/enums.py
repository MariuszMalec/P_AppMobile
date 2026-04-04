import enum


class PersonFamilyEnum(str, enum.Enum):
    TATA = "TATA"
    MAMA = "MAMA"
    GOSIA = "GOSIA"
    EMILKA = "EMILKA"
    RODZINA = "RODZINA"

class ActivityNameEnum(str, enum.Enum):
    All = "All"
    Sprzatanie_kuchni = "Sprzatanie_kuchni"
    Sprzatanie_lazienki = "Sprzatanie_lazienki"
    Zamiatanie_pokoji = "Zamiatanie_pokoji"
    Pranie = "Pranie"
    Odrabianie_lekcji = "Odrabianie_lekcji"
    Basen = "Basen"
    Wstazka = "Wstazka"
    Bajki = "Bajki"
    Czas_spac = "Czas_spac"
    Czas_do_pracy = "Czas_do_pracy"
    Rysowanie = "Rysowanie"
    Obiad = "Obiad"
    Czas_tylko_taty = "Czas_tylko_taty"
    Czas_tylko_mamy = "Czas_tylko_mamy"
    Spacer = "Spacer"
    Gry_i_zabawy = "Gry_i_zabawy"
    Kolacja = "Kolacja"
    Malowanie = "Malowanie"
    Cwiczenia_fizyczne = "Cwiczenia_fizyczne"
    Czas_z_mama = "Czas_z_mama"
    Czas_z_tata = "Czas_z_tata"
    Tance = "Tance"
    Test = "Test"


PERSON_ENUM_MAP = {
    1: PersonFamilyEnum.TATA,
    2: PersonFamilyEnum.MAMA,
    3: PersonFamilyEnum.GOSIA,
    4: PersonFamilyEnum.EMILKA,
    5: PersonFamilyEnum.RODZINA,
}


DAY_NAMES = {
    0: "ALL",
    1: "Niedziela",
    2: "Poniedzialek",
    3: "Wtorek",
    4: "Sroda",
    5: "Czwartek",
    6: "Piatek",
    7: "Sobota",
}


ACTIVITY_ENUM_MAP = {
            1: ActivityNameEnum.All,
                2: ActivityNameEnum.Sprzatanie_kuchni,
                    3: ActivityNameEnum.Sprzatanie_lazienki,
                        4: ActivityNameEnum.Zamiatanie_pokoji,
                            5: ActivityNameEnum.Pranie,
                                6: ActivityNameEnum.Odrabianie_lekcji,
                                    7: ActivityNameEnum.Basen,
                                        8: ActivityNameEnum.Wstazka,
                                            9: ActivityNameEnum.Bajki,
                                                10: ActivityNameEnum.Czas_spac,
                                                    11: ActivityNameEnum.Czas_do_pracy,
                                                        12: ActivityNameEnum.Rysowanie,
                                                            13: ActivityNameEnum.Obiad,
                                                                14: ActivityNameEnum.Czas_tylko_taty,
                                                                    15: ActivityNameEnum.Czas_tylko_mamy,
                                                                        16: ActivityNameEnum.Spacer,
                                                                            17: ActivityNameEnum.Gry_i_zabawy,
                                                                                18: ActivityNameEnum.Kolacja,
                                                                                    19: ActivityNameEnum.Malowanie,
                                                                                        20: ActivityNameEnum.Cwiczenia_fizyczne,
                                                                                            21: ActivityNameEnum.Czas_z_mama,
                                                                                                22: ActivityNameEnum.Czas_z_tata,
                                                                                                    23: ActivityNameEnum.Tance,
                                                                                                    24: ActivityNameEnum.Test,
                                                                                                    }