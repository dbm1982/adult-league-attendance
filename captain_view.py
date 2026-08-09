import streamlit as st

def captain_view(data):
    st.markdown("### Captain Tools")

    players = data["players"]
    games = data["games"]
    attendance = data["attendance"]

    # Show missing responses
    st.markdown("#### Players Missing Responses")

    missing = []
    for p in players:
        pid = p["player_id"]
        for g in games:
            key = (pid, g["game_id"])
            if not any(a["player_id"] == pid and a["game_id"] == g["game_id"] for a in attendance):
                missing.append((p["player_name"], g["date"], g["time"]))

    if missing:
        for name, date, time in missing:
            st.write(f"{name} — {date} {time}")
    else:
        st.success("All players have responded!")

    # Team attendance summary
    st.markdown("#### Team Attendance Summary")

    for g in games:
        yes = sum(1 for a in attendance if a["game_id"] == g["game_id"] and a["status"] == "Yes")
        no = sum(1 for a in attendance if a["game_id"] == g["game_id"] and a["status"] == "No")
        maybe = sum(1 for a in attendance if a["game_id"] == g["game_id"] and a["status"] == "Maybe")

        st.write(f"{g['date']} — Yes: {yes}, No: {no}, Maybe: {maybe}")
