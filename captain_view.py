import streamlit as st

def captain_view(data):
    st.markdown("### Captain Tools")

    players = data["players"]
    games = data["games"]
    attendance = data["attendance"]

    # Build a lookup of attendance by (player_id, game_id)
    attendance_lookup = {
        (a["player_id"], a["game_id"]): a["status"]
        for a in attendance
    }

    # ---------------------------------------------------------
    # MISSING RESPONSES (clean, no duplicates)
    # ---------------------------------------------------------

    st.markdown("#### Players Missing Responses")

    missing_rows = []

    for p in players:
        pid = p["player_id"]

        for g in games:
            key = (pid, g["game_id"])

            # If no attendance record exists for this player/game
            if key not in attendance_lookup:
                missing_rows.append({
                    "player": p["player_name"],
                    "date": g["date"],
                    "time": g["time"]
                })

    # Remove duplicates
    unique_missing = {
        (row["player"], row["date"], row["time"]): row
        for row in missing_rows
    }.values()

    if unique_missing:
        for row in unique_missing:
            st.write(f"{row['player']} — {row['date']} {row['time']}")
    else:
        st.success("All players have responded!")

    # ---------------------------------------------------------
    # TEAM ATTENDANCE SUMMARY
    # ---------------------------------------------------------

    st.markdown("#### Team Attendance Summary")

    for g in games:
        yes = sum(1 for a in attendance if a["game_id"] == g["game_id"] and a["status"] == "Yes")
        no = sum(1 for a in attendance if a["game_id"] == g["game_id"] and a["status"] == "No")
        maybe = sum(1 for a in attendance if a["game_id"] == g["game_id"] and a["status"] == "Maybe")

        st.write(f"{g['date']} — Yes: {yes}, No: {no}, Maybe: {maybe}")
