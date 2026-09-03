import streamlit as st
from datetime import datetime
from zoneinfo import ZoneInfo

eastern = ZoneInfo("America/New_York")


def normalize_status(raw):
    s = str(raw).strip()
    if s == "" or s.lower() in ["none", "no response"]:
        return "No Response"
    if s.lower() in ["yes", "y"]:
        return "Yes"
    if s.lower() in ["no", "n"]:
        return "No"
    if s.lower() in ["maybe", "m"]:
        return "Maybe"
    return "No Response"


def captain_view(players_df, games_df, attendance_df, team_id, commit_changes):

    st.markdown("### Captain View")

    # Filter players on captain's team
    team_players = players_df[
        (players_df["team_id"] == team_id)
        & (players_df["team_id"] != "")
        & (~players_df["team_id"].str.contains("Inactive"))
        & (~players_df["team_id"].str.contains("Floaters"))
    ].copy()

    if team_players.empty:
        st.info(f"No players found for team '{team_id}'.")
        return

    # Normalize team_id in games
    games_df["team_id_norm"] = games_df["team_id"].astype(str).str.strip().str.lower()
    team_id_norm = team_id.strip().lower()

    team_games = games_df[games_df["team_id_norm"] == team_id_norm].copy()

    # Convert date column
    if "date" in team_games.columns:
        team_games["date"] = team_games["date"].apply(
            lambda d: d.date() if hasattr(d, "date") else None
        )

    today_local = datetime.now(eastern).date()
    upcoming_games = team_games[team_games["date"] >= today_local].sort_values("date")

    if upcoming_games.empty:
        st.info("No upcoming games found for this team.")
        return

    # Normalize attendance
    attendance_df["player_id"] = attendance_df["player_id"].astype(str).str.strip()
    attendance_df["game_id"] = attendance_df["game_id"].astype(str).str.strip()
    attendance_df["status"] = attendance_df["status"].apply(normalize_status)

    att_lookup = {
        (row["player_id"], row["game_id"]): row["status"]
        for _, row in attendance_df.iterrows()
    }

    # Determine captain's team name
    if "team_name" in players_df.columns:
        captain_team_name = players_df.loc[
            players_df["team_id"] == team_id, "team_name"
        ].iloc[0]
    else:
        captain_team_name = team_id

    # -----------------------------
    # Render each upcoming game
    # -----------------------------
    for _, g in upcoming_games.iterrows():

        game_id = g["game_id"]
        date = g["date"]
        time_raw = g["time"]
        opponent = g["opponent"]

        field_raw = g.get("field", "")
        field = str(field_raw).replace("Field ", "").replace("field ", "").strip()

        day_name = date.strftime("%A")
        pretty_date = date.strftime("%B %d")
        try:
            pretty_time = datetime.strptime(time_raw, "%H:%M").strftime("%I:%M %p")
        except:
            pretty_time = time_raw

        # Build buckets
        buckets = {"Yes": [], "No": [], "Maybe": [], "No Response": []}

        for _, p in team_players.iterrows():
            pid = p["player_id"]
            pname = p["player_name"]
            status = normalize_status(att_lookup.get((pid, game_id), "No Response"))
            buckets[status].append(pname)

        yes_count = len(buckets["Yes"])
        undecided_count = len(buckets["Maybe"]) + len(buckets["No Response"])

        # -----------------------------
        # MODERN CAPTAIN HEADER CARD
        # -----------------------------
        st.markdown(
            f"""
            <div style="
                padding:18px;
                background-color:#F7F7F7;
                border:1px solid var(--secondary-background-color);
                border-radius:14px;
                margin-bottom:18px;
                color:var(--text-color);
                line-height:1.55;
                box-shadow:0px 1px 3px rgba(0,0,0,0.08);
            ">
                <div style="font-weight:700; font-size:18px; margin-bottom:6px;">
                    ⚽ {day_name}, {pretty_date}
                </div>

                <div style="font-size:16px; font-weight:600; margin-bottom:4px;">
                    🕒 {pretty_time}
                </div>

                <div style="font-size:16px; font-weight:600; margin-bottom:4px;">
                    🆚 {captain_team_name} vs {opponent}
                </div>

                <div style="font-size:14px; opacity:0.85; margin-bottom:12px;">
                    📍 Field <strong>{field}</strong>
                </div>

