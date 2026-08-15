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


def player_view(players_df, games_df, attendance_df, player_id, commit_changes):

    st.markdown("### Player View")

    # Get player info
    player_row = players_df[players_df["player_id"] == player_id]
    if player_row.empty:
        st.error("Player not found.")
        return

    player_name = player_row.iloc[0]["player_name"]
    team_id = player_row.iloc[0]["team_id"]

    st.markdown(f"**{player_name} — {team_id}**")

    # Normalize games
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
        st.info("No upcoming games found.")
        return

    # Normalize attendance
    attendance_df["player_id"] = attendance_df["player_id"].astype(str).str.strip()
    attendance_df["game_id"] = attendance_df["game_id"].astype(str).str.strip()
    attendance_df["status"] = attendance_df["status"].apply(normalize_status)

    att_lookup = {
        (row["player_id"], row["game_id"]): row["status"]
        for _, row in attendance_df.iterrows()
    }

    # -----------------------------
    # Render each game
    # -----------------------------
    for _, g in upcoming_games.iterrows():

        game_id = g["game_id"]
        date = g["date"]
        time_raw = g["time"]
        opponent = g["opponent"]

        # Clean field formatting
        field_raw = g.get("field", "")
        field = str(field_raw).replace("Field ", "").replace("field ", "").strip()

        # Human-friendly date/time
        day_name = date.strftime("%A")
        pretty_date = date.strftime("%B %d")
        try:
            pretty_time = datetime.strptime(time_raw, "%H:%M").strftime("%I:%M %p")
        except:
            pretty_time = time_raw

        # Current status
        current_status = normalize_status(att_lookup.get((player_id, game_id), "No Response"))

        # -----------------------------
        # DARK-MODE-SAFE HEADER BOX
        # -----------------------------
        st.markdown(
            f"""
            <div style="
                padding:12px 16px;
                background-color:rgba(255,255,255,0.08);
                border:1px solid rgba(255,255,255,0.25);
                border-radius:10px;
                margin-bottom:12px;
                font-size:16px;
                color:#e0e0e0;
            ">
                <div style="font-weight:600; color:#ffffff;">
                    {day_name}, {pretty_date} — {pretty_time}
                </div>
                <div style="font-weight:600; color:#ffffff;">
                    vs {opponent}
                </div>
                <div style="color:#cccccc;">
                    Field <strong style="color:#ffffff;">{field}</strong>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        # -----------------------------
        # STATUS SELECTION
        # -----------------------------
        st.markdown(f"#### Your status for {day_name}, {pretty_date} at {pretty_time}")

        options = ["Yes", "No", "Maybe", "No Response"]

        new_status = st.radio(
            f"Status for {pretty_date} {pretty_time}",
            options,
            index=options.index(current_status),
            key=f"player_{player_id}_{game_id}",
        )

        st.session_state.pending_updates[(player_id, game_id)] = new_status

        # -----------------------------
        # SAVE BUTTON
        # -----------------------------
        has_unsaved = any(
            (gid == game_id) for (_, gid) in st.session_state.pending_updates.keys()
        )

        if has_unsaved:
            st.markdown(
                """
                <div style="
                    padding:8px 12px;
                    background-color:rgba(255,255,255,0.05);
                    border:1px solid rgba(255,255,255,0.15);
                    border-radius:6px;
                    margin-bottom:10px;
                    font-size:14px;
                    color:#e0e0e0;
                ">
                    <strong style="color:#ffffff;">Unsaved changes for this game.</strong>
                </div>
                """,
                unsafe_allow_html=True
            )

            if st.button(f"Save changes for {pretty_date} {pretty_time}", key=f"save_player_{game_id}"):
                _apply_player_update(player_id, game_id, new_status, attendance_df)
                updated = commit_changes(attendance_df)
                st.session_state.attendance_df = updated
                _clear_player_pending(player_id, game_id)
                st.success("Your status has been saved.")

        st.markdown("---")


def _apply_player_update(player_id, game_id, status, attendance_df):
    mask = (attendance_df["player_id"] == player_id) & (attendance_df["game_id"] == game_id)

    if mask.any():
        attendance_df.loc[mask, "status"] = status
        attendance_df.loc[mask, "updated_at"] = datetime.now(eastern).isoformat()
    else:
        attendance_df.loc[len(attendance_df)] = {
            "player_id": player_id,
            "game_id": game_id,
            "status": status,
            "updated_at": datetime.now(eastern).isoformat(),
        }


def _clear_player_pending(player_id, game_id):
    for key in list(st.session_state.pending_updates.keys()):
        pid, gid = key
        if pid == player_id and gid == game_id:
            del st.session_state.pending_updates[key]
