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

    # Get player info
    player_row = players_df[players_df["player_id"] == player_id]
    if player_row.empty:
        st.error("Player not found.")
        return

    team_id = player_row.iloc[0]["team_id"]

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

        current_status = normalize_status(att_lookup.get((player_id, game_id), "No Response"))

        # -----------------------------
        # GAME CARD
        # -----------------------------
        st.markdown(
            f"""
            <div style="
                padding:14px 16px;
                background-color:var(--background-color);
                border:1px solid var(--secondary-background-color);
                border-radius:12px;
                margin-bottom:12px;
                color:var(--text-color);
                line-height:1.4;
            ">
                <div style="font-weight:700; font-size:16px; margin-bottom:4px;">
                    ⚽ {day_name}, {pretty_date}
                </div>
                <div style="font-size:15px; font-weight:600; margin-bottom:2px;">
                    🕒 {pretty_time}
                </div>
                <div style="font-size:15px; font-weight:600; margin-bottom:2px;">
                    🆚 {opponent}
                </div>
                <div style="font-size:14px; opacity:0.8; margin-bottom:8px;">
                    📍 Field <strong>{field}</strong>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown("**Choose your status:**")

        options = ["Yes", "No", "Maybe", "No Response"]

        new_status = st.radio(
            "",
            options,
            index=options.index(current_status),
            key=f"player_{player_id}_{game_id}",
            horizontal=True,
        )

        # ⭐ One-click saving fix: detect radio change → rerun immediately
        if st.session_state.pending_updates.get((player_id, game_id)) != new_status:
            st.session_state.pending_updates[(player_id, game_id)] = new_status
            st.rerun()

        # ⭐ Improved color palette
        bg_color = {
            "Yes": "#A5D6A7",        # deeper green (no yellow tint)
            "No": "#F2B8B5",         # strong red
            "Maybe": "#FFCC80",      # clean orange
            "No Response": "#E0E0E0" # neutral gray
        }[new_status]

        text_color = {
            "Yes": "#1E8E3E",        # strong green
            "No": "#D93025",         # strong red
            "Maybe": "#F9AB00",      # clean orange
            "No Response": "#5F6368" # neutral gray
        }[new_status]

        # ⭐ Selected status box
        st.markdown(
            f"""
            <div style="
                background-color:{bg_color};
                padding:12px;
                border-radius:10px;
                margin-top:6px;
                margin-bottom:12px;
                border:2px solid {text_color};
            ">
                <strong style="color:{text_color}; font-size:16px;">
                    Selected: {new_status}
                </strong>
            </div>
            """,
            unsafe_allow_html=True
        )

        # -----------------------------
        # UNSAVED + SAVE
        # -----------------------------
        has_unsaved = (new_status != current_status)

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
                unsafe_allow_html=True,
            )

            if st.button(f"💾 Save {pretty_date} {pretty_time}", key=f"save_player_{game_id}"):
                _apply_player_update(player_id, game_id, new_status, attendance_df)
                updated = commit_changes(attendance_df)
                st.session_state.attendance_df = updated
                _clear_player_pending(player_id, game_id)
                st.success("Saved.")
                st.rerun()

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
