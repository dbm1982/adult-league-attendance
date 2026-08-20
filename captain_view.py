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

    # Convert date column
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

    # Determine captain's team name
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

        field_raw = g.get("field", "")
        field = str(field_raw).replace("Field ", "").replace("field ", "").strip()

        day_name = date.strftime("%A")
        pretty_date = date.strftime("%B %d")
        try:
            pretty_time = datetime.strptime(time_raw, "%H:%M").strftime("%I:%M %p")
        except:
            pretty_time = time_raw

        # Build buckets
        buckets = {"Yes": [], "No": [], "Maybe": [], "No Response": []}

        for _, p in team_players.iterrows():
            pid = p["player_id"]
            pname = p["player_name"]
            status = normalize_status(att_lookup.get((pid, game_id), "No Response"))
            buckets[status].append(pname)

        yes_count = len(buckets["Yes"])
        undecided_count = len(buckets["Maybe"]) + len(buckets["No Response"])

        # -----------------------------
        # HEADER BOX
        # -----------------------------
        st.markdown(
            f"""
            <div style="
                padding:12px 16px;
                background-color:var(--background-color);
                border:1px solid var(--secondary-background-color);
                border-radius:10px;
                margin-bottom:12px;
                font-size:16px;
                color:var(--text-color);
            ">
                <div style="font-weight:600;">
                    {day_name}, {pretty_date} — {pretty_time}
                </div>
                <div style="font-weight:600;">
                    {captain_team_name} vs {opponent}
                </div>
                <div style="opacity:0.8;">
                    Field <strong>{field}</strong>
                </div>
                <div style="margin-top:6px;">
                    <span style="color:#2e7d32; font-weight:700;">Playing: {yes_count}</span>
                    &nbsp;•&nbsp;
                    <span style="color:#f57c00; font-weight:700;">Undecided: {undecided_count}</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        # -----------------------------
        # DETAILS EXPANDER
        # -----------------------------
        with st.expander("Details"):

            # Summary block
            st.markdown(
                f"""
                <div style="
                    padding:8px 12px;
                    background-color:var(--background-color);
                    border:1px solid var(--secondary-background-color);
                    border-radius:6px;
                    margin-bottom:10px;
                    font-size:14px;
                    color:var(--text-color);
                ">
                    <strong>Game Summary</strong><br>
                    <span style="color:#2e7d32; font-weight:700;">Playing: {yes_count}</span><br>
                    <span style="color:#f57c00; font-weight:700;">Undecided: {undecided_count}</span>
                </div>
                """,
                unsafe_allow_html=True
            )

            # Attendance Breakdown
            st.markdown("#### Attendance Breakdown")

            cols = st.columns(4)
            labels = ["Yes", "No", "Maybe", "No Response"]
            colors = {
                "Yes": "#2e7d32",
                "No": "#c62828",
                "Maybe": "#f57c00",
                "No Response": "#616161",
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
            st.markdown("#### Override Player Status")

            # -----------------------------
            # FULL-SECTION COLOR WRAP
            # -----------------------------
            for _, p in team_players.iterrows():
                pid = p["player_id"]
                pname = p["player_name"]
                current_status = normalize_status(att_lookup.get((pid, game_id), "No Response"))

                header_color = {
                    "Yes": "#2e7d32",
                    "No": "#c62828",
                    "Maybe": "#f57c00",
                    "No Response": "#616161",
                }[current_status]

                bg_color = {
                    "Yes": "#C8E6C9",
                    "No": "#F8D7DA",
                    "Maybe": "#FFE0B2",
                    "No Response": "#E0E0E0",
                }[current_status]

                st.markdown(
                    f"""
                    <div style="
                        background-color:{bg_color};
                        border-radius:10px;
                        padding:0px;
                        margin-bottom:14px;
                        border:1px solid var(--secondary-background-color);
                    ">
                        <div style="
                            background-color:{header_color};
                            color:white;
                            padding:10px 14px;
                            font-weight:600;
                            border-top-left-radius:10px;
                            border-top-right-radius:10px;
                        ">
                            {pname}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                new_status = st.radio(
                    "",
                    ["Yes", "No", "Maybe", "No Response"],
                    index=["Yes", "No", "Maybe", "No Response"].index(current_status),
                    key=f"capt_{pid}_{game_id}",
                    horizontal=True,
                )

                # ⭐ One‑click saving fix: detect radio change → rerun immediately
                if st.session_state.pending_updates.get((pid, game_id)) != new_status:
                    st.session_state.pending_updates[(pid, game_id)] = new_status
                    st.rerun()

                st.markdown(
                    f"""
                    <div style="
                        height:4px;
                        background-color:{header_color};
                        margin-top:-8px;
                        margin-bottom:12px;
                        border-bottom-left-radius:10px;
                        border-bottom-right-radius:10px;
                    "></div>
                    """,
                    unsafe_allow_html=True
                )

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
                    st.rerun()

        st.markdown("---")


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
