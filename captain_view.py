import streamlit as st

def captain_view(data, current_player_id):
    st.markdown("### Captain Tools")

    players = data["players"]
    games = data["games"]
    attendance = data["attendance"]

    # Build lookup
    attendance_lookup = {
        (a["player_id"], a["game_id"]): a["status"]
        for a in attendance
    }

    # ---------------------------------------------------------
    # MISSING RESPONSES — CLEAN, NO DUPLICATES, NO SELF
    # ---------------------------------------------------------

    st.markdown("#### Players Missing Responses")

    missing = []

    for p in players:
        pid = p["player_id"]

        # Skip the captain themselves
        if pid == current_player_id:
            continue

        for g in games:
            key = (pid, g["game_id"])
            if key not in attendance_lookup:
                missing.append((p["player_name"], g["date"], g["time"]))

    # Deduplicate
    unique_missing = sorted(set(missing))

    if unique_missing:
        for name, date, time in unique_missing:
            st.write(f"{name} — {date} {time}")
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
