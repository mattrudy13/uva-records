"""The sports we track and how each one labels its seasons.

sport_id is virginiasports.com's internal id. term decides the season label:
fall sports use the first year of the academic year, spring sports the second,
winter sports span both (e.g. academic 2005-06 -> "2005", "2006", "2005-06").
"""

FIRST_SEASON = 2000  # academic 2000-01, the oldest season the site has

SPORTS = {
    "football": {"sport_id": 27, "name": "Football", "term": "fall"},
    "msoc": {"sport_id": 20, "name": "Men's Soccer", "term": "fall"},
    "wsoc": {"sport_id": 11, "name": "Women's Soccer", "term": "fall"},
    "fhockey": {"sport_id": 28, "name": "Field Hockey", "term": "fall"},
    "wvball": {"sport_id": 8, "name": "Volleyball", "term": "fall"},
    "mbball": {"sport_id": 23, "name": "Men's Basketball", "term": "winter"},
    "wbball": {"sport_id": 15, "name": "Women's Basketball", "term": "winter"},
    "wrestling": {"sport_id": 7, "name": "Wrestling", "term": "winter"},
    "baseball": {"sport_id": 31, "name": "Baseball", "term": "spring"},
    "softball": {"sport_id": 17, "name": "Softball", "term": "spring"},
    "mlax": {"sport_id": 21, "name": "Men's Lacrosse", "term": "spring"},
    "wlax": {"sport_id": 13, "name": "Women's Lacrosse", "term": "spring"},
    "mten": {"sport_id": 18, "name": "Men's Tennis", "term": "spring"},
    "wten": {"sport_id": 9, "name": "Women's Tennis", "term": "spring"},
}


def season_label(slug, start):
    term = SPORTS[slug]["term"]
    if term == "fall":
        return str(start)
    if term == "spring":
        return str(start + 1)
    return f"{start}-{str(start + 1)[2:]}"
