import streamlit as st
from datetime import datetime

def captain_view(data, captain_player_id):

    players = data["players"]
    games = data["games"]
    attendance = data["attendance"]

    # Identify captain
    captain = next(p for p in players if p["player_id"] == captain_player_id)
    team_id = captain["team_id"]

    # First name only
    first_name = captain["player_name"].split()[0]
    st.markdown(f"### Hello {first_name}")

    # Filter players on captain's team
    team_players = [p for p in players if p["team_id"] == team_id]

    # Filter games for captain's team
    team_games = [g for g in games if g["team_id"] == team_id]

    if not team_games:
        st.info("No games found for your team.")
        return

    # Sort games by date/time and pick the next upcoming game
    def parse_dt(g):
        return datetime.strptime(f"{g['date']} {g['time']}", "%Y-%m-%d %H:%M %p")

    next_game = sorted(team_games, key=parse_dt)[0]
    game_id = next_game["game_id"]

    # Build attendance lookup for this game
    att_lookup = {
        a["player_id"]: a["status"]
        for a in attendance
        if a["game_id"] == game_id
    }

    # ---------------------------------------------------------
    # Format date nicely
    # ---------------------------------------------------------
    dt = parse_dt(next_game)
    formatted_date = dt.strftime("%A, %B %-d, %Y at %-I:%M%p")

    st.markdown(
        f"#### {formatted_date} — Opponent: {next_game['opponent']}",
        unsafe_allow_html=True
    )

    st.markdown("---")

    # ---------------------------------------------------------
    # Group players by response
    # ---------------------------------------------------------

    yes_list = []
    no_list = []
    maybe_list = []
    nr_list = []

    for p in team_players:
        status = att_lookup.get(p["player_id"], "")
        if status == "Yes":
            yes_list.append(p["player_name"])
        elif status == "No":
            no_list.append(p["player_name"])
        elif status == "Maybe":
            maybe_list.append(p["player_name"])
        else:
            nr_list.append(p["player_name"])

    # ---------------------------------------------------------
    # Quick Summary
    # ---------------------------------------------------------

    st.markdown("### Summary")

    st.markdown(
        f"- **{len(yes_list)}** coming (Yes)\n"
        f"- **{len(no_list)}** not coming (No)\n"
        f"- **{len(maybe_list)}** unsure (Maybe)\n"
        f"- **{len(nr_list)}** no response (NR)"
    )

    st.markdown("---")

    # ---------------------------------------------------------
    # Detailed Lists
    # ---------------------------------------------------------

    def show_group(title, names, color):
        st.markdown(f"### <span style='color:{color};'>{title} ({len(names)})</span>", unsafe_allow_html=True)
        if names:
            for n in names:
                st.markdown(f"- {n}")
        else:
            st.markdown("_None_")

    show_group("YES", yes_list, "green")
    show_group("NO", no_list, "red")
    show_group("MAYBE", maybe_list, "orange")
    show_group("NO RESPONSE", nr_list, "gray")
