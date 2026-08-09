import streamlit as st

def captain_view(data, captain_player_id):

    players = data["players"]
    games = data["games"]
    attendance = data["attendance"]
    sheet = data["sheet"]

    # Identify captain's team
    captain = next(p for p in players if p["player_id"] == captain_player_id)
    team_id = captain["team_id"]

    # Filter players on captain's team
    team_players = [p for p in players if p["team_id"] == team_id]

    # Filter games for captain's team
    team_games = [g for g in games if g["team_id"] == team_id]
    team_game_ids = {g["game_id"] for g in team_games}

    # Build attendance lookup
    att_lookup = {
        (a["player_id"], a["game_id"]): a["status"]
        for a in attendance
        if a["game_id"] in team_game_ids
    }

    st.markdown("### Captain Tools")

    # ---------------------------------------------------------
    # Missing Responses
    # ---------------------------------------------------------
    st.markdown("#### Players Missing Responses")

    for p in team_players:
        missing = [
            g for g in team_games
            if att_lookup.get((p["player_id"], g["game_id"]), "") == ""
        ]
        if missing:
            st.markdown(f"**{p['player_name']}**")
            for g in missing:
                st.write(f"{g['date']} {g['time']}")

    st.markdown("---")

    # ---------------------------------------------------------
    # Full Attendance Matrix (restored)
    # ---------------------------------------------------------

    st.markdown("### Team Attendance Overview")

    for g in team_games:
        st.markdown(f"#### {g['opponent']} — {g['date']} {g['time']} (Field {g['field']})")

        # Build table
        table = []
        for p in team_players:
            status = att_lookup.get((p["player_id"], g["game_id"]), "")

            # Colored buttons
            yes = st.button("Yes", key=f"yes_{p['player_id']}_{g['game_id']}")
            no = st.button("No", key=f"no_{p['player_id']}_{g['game_id']}")
            maybe = st.button("Maybe", key=f"maybe_{p['player_id']}_{g['game_id']}")
            nr = (status == "")

            # Display row
            st.write(
                f"{p['player_name']} — "
                f"Yes: {'●' if status=='Yes' else '○'}  "
                f"No: {'●' if status=='No' else '○'}  "
                f"Maybe: {'●' if status=='Maybe' else '○'}  "
                f"NR: {'●' if nr else '○'}"
            )

        st.markdown("---")
