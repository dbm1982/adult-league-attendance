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


def captain_view(players_df, games_df, attendance_df, team_id, commit_changes):
    st.markdown("### Captain View")

    team_players = players_df[
        (players_df["team_id"] == team_id)
        & (players_df["team_id"].ne(""))
        & (~players_df["team_id"].str.contains("Inactive", case=False))
        & (~players_df["team_id"].str.contains("Floaters", case=False))
    ].copy()

    if team_players.empty:
        st.info(f"No players found for team '{team_id}'.")
        return

    games_df["team_id_norm"] = games_df["team_id"].astype(str).str.strip().str.lower()
    team_id_norm = team_id.strip().lower()

    team_games = games_df[games_df["team_id_norm"] == team_id_norm].copy()

    if "date" in team_games.columns:
        team_games["date"] = team_games["date"].apply(
            lambda d: d.date() if hasattr(d, "date") else None
        )

    today_local = datetime.now(eastern).date()
    upcoming_games = team_games[team_games["date"] >= today_local].sort_values("date")

    if upcoming_games.empty:
        st.info("No upcoming games found for this team.")
        return

    attendance_df["player_id"] = attendance_df["player_id"].astype(str).str.strip()
    attendance_df["game_id"] = attendance_df["game_id"].astype(str).str.strip()
    attendance_df["status"] = attendance_df["status"].apply(normalize_status)

    att_lookup = {
        (row["player_id"], row["game_id"]): row["status"]
        for _, row in attendance_df.iterrows()
    }

    for _, g in upcoming_games.iterrows():
        game_id = g["game_id"]
        date = g["date"]
        time = g["time"]
        opponent = g["opponent"]
        field = g.get("field", "")

        with st.expander(f"{date} — {time} vs {opponent} ({field})", expanded=False):
            buckets = {"Yes": [], "No": [], "Maybe": [], "No Response": []}

            for _, p in team_players.iterrows():
                pid = p["player_id"]
                pname = p["player_name"]
                status = att_lookup.get((pid, game_id), "No Response")
                status = normalize_status(status)
                buckets[status].append(pname)

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
                    st.markdown(
                        f"<span style='color:{colors[label]}; font-weight:bold;'>{label}</span>",
                        unsafe_allow_html=True,
                    )
                    if buckets[label]:
                        for name in sorted(buckets[label]):
                            st.markdown(f"- {name}")
                    else:
                        st.markdown("_None_")

            st.markdown("---")
            st.markdown("#### Override individual player status")

            for _, p in team_players.iterrows():
                pid = p["player_id"]
                pname = p["player_name"]
                current_status = att_lookup.get((pid, game_id), "No Response")
                current_status = normalize_status(current_status)

                options = ["Yes", "No", "Maybe", "No Response"]

                st.markdown(f"**{pname}**")
                new_status = st.radio(
                    f"Status for {pname} ({date} {time})",
                    options,
                    index=options.index(current_status),
                    key=f"capt_{pid}_{game_id}",
                )

                st.session_state.pending_updates[(pid, game_id)] = new_status

            has_unsaved = any(
                (gid == game_id) for (_, gid) in st.session_state.pending_updates.keys()
            )

            if has_unsaved:
                st.warning("Unsaved changes for this game.")
                if st.button(f"Save changes for {date} {time}", key=f"save_capt_{game_id}"):
                    _apply_game_updates(game_id, attendance_df)
                    updated = commit_changes(attendance_df)
                    st.session_state.attendance_df = updated
                    _clear_game_pending(game_id)
                    st.success("Attendance for this game has been saved.")


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


def _clear_game_pending(game_id):
    for key in list(st.session_state.pending_updates.keys()):
        pid, gid = key
        if gid == game_id:
            del st.session_state.pending_updates[key]
