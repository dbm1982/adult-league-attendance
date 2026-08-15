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
        # FULL COMPACT GAME CARD
        # -----------------------------
        st.markdown(
            f"""
            <div style="
                padding:14px 16px;
                background-color:var(--background-color);
                border:1px solid var(--secondary-background-color);
                border-radius:12px;
                margin-bottom:16px;
                color:var(--text-color);
                line-height:1.35;
            ">
                <!-- GAME SUMMARY -->
                <div style="font-weight:700; font-size:16px;">
                    ⚽ {day_name}, {pretty_date} — {pretty_time}
                </div>
                <div style="font-weight:600;">
                    vs {opponent}
                </div>
                <div style="opacity:0.75; font-size:13px;">
                    📍 Field <strong>{field}</strong>
                </div>

                <hr style="opacity:0.2; margin-top:10px; margin-bottom:10px;">

                <!-- STATUS HEADER -->
                <div style="font-weight:600; margin-bottom:6px;">
                    Your status
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        # Radio buttons INSIDE the card visually
        options = ["Yes", "No", "Maybe", "No Response"]

        new_status = st.radio(
            "",
            options,
            index=options.index(current_status),
            key=f"player_{player_id}_{game_id}",
            horizontal=True
        )

        st.session_state.pending_updates[(player_id, game_id)] = new_status

        # -----------------------------
        # UNSAVED + SAVE BUTTON (compact)
        # -----------------------------
        has_unsaved = any(
            (pid == player_id and gid == game_id)
            for (pid, gid) in st.session_state.pending_updates.keys()
        )

        if has_unsaved:
            st.markdown(
                """
                <div style="
                    padding:6px 10px;
                    background-color:var(--background-color);
                    border:1px solid var(--secondary-background-color);
                    border-radius:6px;
                    margin-top:6px;
                    margin-bottom:6px;
                    color:var(--text-color);
                    font-size:13px;
                ">
                    ⚠️ Unsaved changes
                </div>
                """,
                unsafe_allow_html=True
            )

            if st.button(f"💾 Save {pretty_date} {pretty_time}", key=f"save_player_{game_id}"):
                _apply_player_update(player_id, game_id, new_status, attendance_df)
                updated = commit_changes(attendance_df)
                st.session_state.attendance_df = updated
                _clear_player_pending(player_id, game_id)
                st.success("Saved.")

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
