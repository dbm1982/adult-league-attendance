import streamlit as st
from datetime import datetime
from zoneinfo import ZoneInfo

eastern = ZoneInfo("America/New_York")

# -----------------------------
# Normalization helpers
# -----------------------------
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


# -----------------------------
# Main Captain View
# -----------------------------
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

    # Convert date column to date objects
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

    # Determine captain's team name (fallback to team_id)
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
        field = g.get("field", "")

        # Format date/time
        day_name = date.strftime("%A")
        pretty_date = date.strftime("%B %d")
        try:
            pretty_time = datetime.strptime(time_raw, "%H:%M").strftime("%I:%M %p")
        except:
            pretty_time = time_raw  # fallback if already formatted

        # Build buckets
        buckets = {"Yes": [], "No": [], "Maybe": [], "No Response": []}

        for _, p in team_players.iterrows():
            pid = p["player_id"]
            pname = p["player_name"]
            status = att_lookup.get((pid, game_id), "No Response")
            status = normalize_status(status)
            buckets[status].append(pname)

        yes_count = len(buckets["Yes"])
        undecided_count = len(buckets["Maybe"]) + len(buckets["No Response"])

        # Clean expander title
        expander_title = (
            f"{day_name}, {pretty_date} | {pretty_time} | "
            f"{captain_team_name} vs {opponent} | Field {field} "
            f"| Playing: {yes_count} ({captain_team_name}) • Undecided: {undecided_count}"
        )

        # -----------------------------
        # Expander UI
        # -----------------------------
        with st.expander(expander_title, expanded=False):

            # Summary block
            st.markdown(
                f"""
                <div style="
                    padding:8px 12px;
                    background-color:#f7f7f7;
                    border-radius:6px;
                    margin-bottom:12px;
                    font-size:15px;
                ">
                    <strong>Summary:</strong>
                    <span style="color:#5cb85c; font-weight:600;">Playing: {yes_count}</span> •
                    <span style="color:#999999; font-weight:600;">Undecided: {undecided_count}</span>
                </div>
                """,
                unsafe_allow_html=True
            )

            # Buckets
            cols = st.columns(4)
            labels = ["Yes", "No", "Maybe", "No Response"]
            colors = {
                "Yes": "#5cb85c",
                "No": "#d9534f",
                "Maybe": "#f0ad4e",
                "No Response": "#999999",
            }

            for col, label in zip(cols, labels):
                with col:
                    count = len(buckets[label])
                    st.markdown(
                        f"<span style='color:{colors[label]}; font-weight:bold;'>{label} ({count})</span>",
                        unsafe_allow_html=True,
                    )
                    if buckets[label]:
                        for name in sorted(buckets[label]):
                            st.markdown(f"- {name}")
                    else:
                        st.markdown("_None_")

            st.markdown("---")
            st.markdown("#### Override individual player status")

            # Override UI
            for _, p in team_players.iterrows():
                pid = p["player_id"]
                pname = p["player_name"]
                current_status = att_lookup.get((pid, game_id), "No Response")
                current_status = normalize_status(current_status)

                options = ["Yes", "No", "Maybe", "No Response"]

                st.markdown(f"**{pname}**")
                new_status = st.radio(
                    f"Status for {pname} ({pretty_date} {pretty_time})",
                    options,
                    index=options.index(current_status),
                    key=f"capt_{pid}_{game_id}",
                )

                st.session_state.pending_updates[(pid, game_id)] = new_status

            # Save button
            has_unsaved = any(
                (gid == game_id) for (_, gid) in st.session_state.pending_updates.keys()
            )

            if has_unsaved:
                st.warning("Unsaved changes for this game.")
                if st.button(f"Save changes for {pretty_date} {pretty_time}", key=f"save_capt_{game_id}"):
                    _apply_game_updates(game_id, attendance_df)
                    updated = commit_changes(attendance_df)
                    st.session_state.attendance_df = updated
                    _clear_game_pending(game_id)
                    st.success("Attendance for this game has been saved.")


# -----------------------------
# Apply pending updates
# -----------------------------
def _apply_game_updates(game_id, attendance_df):
    for (pid, gid), status in list(st.session_state.pending_updates.items()):
        if gid != game_id:
            continue

        mask = (attendance_df["player_id"] == pid) & (attendance_df["game_id"] == gid)

        if mask.any():
            attendance_df.loc[mask, "status"] = status
            attendance_df.loc[mask, "updated_at"] = datetime.now(eastern).isoformat()
        else:
            attendance_df.loc[len(attendance_df)] = {
                "player_id": pid,
                "game_id": gid,
                "status": status,
                "updated_at": datetime.now(eastern).isoformat(),
            }


# -----------------------------
# Clear pending updates
# -----------------------------
def _clear_game_pending(game_id):
    for key in list(st.session_state.pending_updates.keys()):
        pid, gid = key
        if gid == game_id:
            del st.session_state.pending_updates[key]
