# ---------------------------------------------------------
# FILTER ACTIVE TEAMS THAT HAVE PLAYERS
# ---------------------------------------------------------

active_teams = [
    t for t in teams
    if t.get("active", False) == True
    and any(p["team_id"] == t["team_id"] for p in players)
]
