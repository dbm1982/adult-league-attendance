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
                st.write(f"{g['date']} {g['time']} (Field {g['field']})")

    st.markdown("---")

    # ---------------------------------------------------------
    # Full Attendance Matrix (restored)
    # ---------------------------------------------------------

    st.markdown("### Team Attendance Overview")

    for g in team_games:

        # Correct header: date/time first, opponent small
        st.markdown(
            f"#### {g['date']} {g['time']} — Field {g['field']} "
            f"<span style='color:#888;font-size:14px;'>({g['opponent']})</span>",
            unsafe_allow_html=True
        )

        # Build table
        for p in team_players:
            status = att_lookup.get((p["player_id"], g["game_id"]), "")

            # Color-coded dots
            def dot(color):
                return f"<span style='color:{color};font-size:22px;'>●</span>"

            yes_dot = dot("green") if status == "Yes" else dot("#ccc")
            no_dot = dot("red") if status == "No" else dot("#ccc")
            maybe_dot = dot("orange") if status == "Maybe" else dot("#ccc")
            nr_dot = dot("gray") if status == "" else dot("#ccc")

            # Display row
            st.markdown(
                f"<b>{p['player_name']}</b> &nbsp;&nbsp; "
                f"Yes: {yes_dot} &nbsp;&nbsp; "
                f"No: {no_dot} &nbsp;&nbsp; "
                f"Maybe: {maybe_dot} &nbsp;&nbsp; "
                f"NR: {nr_dot}",
                unsafe_allow_html=True
            )

        st.markdown("---")
