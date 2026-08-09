import streamlit as st

def captain_view(data, captain_player_id):

    players = data["players"]
    games = data["games"]
    attendance = data["attendance"]

    # Identify captain's team
    captain = next(p for p in players if p["player_id"] == captain_player_id)
    team_id = captain["team_id"]

    # Filter players on captain's team
    team_players = [p for p in players if p["team_id"] == team_id]

    # Filter games for captain's team
    team_games = [g for g in games if g["team_id"] == team_id]

    # Sort games by date/time and pick the next upcoming game
    if not team_games:
        st.info("No games found for your team.")
        return

    next_game = sorted(team_games, key=lambda g: (g["date"], g["time"]))[0]
    game_id = next_game["game_id"]

    # Build attendance lookup for this game
    att_lookup = {
        a["player_id"]: a["status"]
        for a in attendance
        if a["game_id"] == game_id
    }

    st.markdown("### Captain Tools")

    # ---------------------------------------------------------
    # Game Header (correct formatting)
    # ---------------------------------------------------------
    st.markdown(
        f"#### {next_game['date']} {next_game['time']} — Field {next_game['field']} "
        f"<span style='color:#888;font-size:14px;'>({next_game['opponent']})</span>",
        unsafe_allow_html=True
    )

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
    # Display grouped lists (clean, readable)
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
