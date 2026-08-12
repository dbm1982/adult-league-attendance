import streamlit as st
import pandas as pd

def captain_view(players_df, games_df, attendance_df, team_id, commit_changes):

    st.title("Captain View")

    # Simple instructions for captains
    st.info("Expand each game below to view player attendance and make updates.")

    players_df["team_id"] = players_df["team_id"].astype(str).str.strip()
    games_df["team_id"] = games_df["team_id"].astype(str).str.strip()

    team_players = players_df[players_df["team_id"] == team_id].copy()
    team_games = games_df[games_df["team_id"] == team_id].copy()

    today = pd.Timestamp.now()
    upcoming_games = team_games[team_games["date"] >= today].sort_values("date")

    if upcoming_games.empty:
        st.info("No upcoming games found for this team.")
        return

    valid_statuses = ["Yes", "No", "Maybe", "No Response"]

    attendance_lookup = {
        (row["player_id"], row["game_id"]): row["status"]
        for _, row in attendance_df.iterrows()
    }

    # Cleaner pill styling
    st.markdown("""
        <style>
            .pill {
                display:inline-block;
                padding:6px 10px;
                border-radius:12px;
                color:white;
                margin:4px 6px 4px 0;
                font-size:14px;
            }
            .pill-yes { background:#2ecc71; }
            .pill-no { background:#e74c3c; }
            .pill-maybe { background:#f1c40f; color:black; }
            .pill-nr { background:#7f8c8d; }
        </style>
    """, unsafe_allow_html=True)

    for _, game in upcoming_games.iterrows():

        game_id = game["game_id"]
        game_date = game["display_date"]
        game_time = game["display_time"]
        opponent = game["opponent"]

        grouped = {s: [] for s in valid_statuses}

        for _, player in team_players.iterrows():
            pid = player["token"]
            raw = attendance_lookup.get((pid, game_id), "No Response")
            status = str(raw).strip().capitalize()
            status = status if status in valid_statuses else "No Response"
            grouped[status].append(player["player_name"])

        yes_count = len(grouped["Yes"])
        unconfirmed_count = len(grouped["Maybe"]) + len(grouped["No Response"])

        # ---------------------------------------------------------
        # CLEAN GAME HEADER (front-and-center info)
        # ---------------------------------------------------------
        st.markdown(
            f"""
            <div style="
                padding:16px;
                border-radius:12px;
                border:1px solid #DDD;
                margin-bottom:6px;
                background:#fafafa;
            ">
                <div style="font-size:18px; font-weight:600;">
                    {game_date} — {game_time}
                </div>
                <div style="font-size:16px; margin-bottom:8px;">
                    vs <strong>{opponent}</strong>
                </div>

                <div style="display:flex; gap:12px; margin-top:6px;">
                    <div style="
                        background:#2ecc71;
                        padding:6px 12px;
                        border-radius:8px;
                        color:white;
                        font-weight:600;
                    ">
                        {yes_count} playing
                    </div>

                    <div style="
                        background:#7f8c8d;
                        padding:6px 12px;
                        border-radius:8px;
                        color:white;
                        font-weight:600;
                    ">
                        {unconfirmed_count} unconfirmed
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        # ---------------------------------------------------------
        # EXPANDER FOR DETAILS
        # ---------------------------------------------------------
        with st.expander("View Details", expanded=False):

            # Pills inside expander
            def pill_row(label, names, css_class):
                if not names:
                    st.markdown(f"**{label}:** _None_")
                    return

                pills_html = "".join(
                    f"<span class='pill {css_class}'>{n}</span>"
                    for n in names
                )
                st.markdown(f"**{label} ({len(names)}):**<br>{pills_html}", unsafe_allow_html=True)

            pill_row("Yes", grouped["Yes"], "pill-yes")
            pill_row("No", grouped["No"], "pill-no")
            pill_row("Maybe", grouped["Maybe"], "pill-maybe")
            pill_row("No Response", grouped["No Response"], "pill-nr")

            st.markdown("---")

            st.subheader("Update Attendance")

            updated = []

            for _, player in team_players.iterrows():
                pid = player["token"]
                pname = player["player_name"]

                raw = attendance_lookup.get((pid, game_id), "No Response")
                status = str(raw).strip().capitalize()
                status = status if status in valid_statuses else "No Response"

                new_status = st.radio(
                    pname,
                    valid_statuses,
                    index=valid_statuses.index(status),
                    horizontal=True,
                    key=f"radio_{pid}_{game_id}"
                )

                updated.append((pid, game_id, new_status))

            if st.button(f"Save All Changes for {game_date}", key=f"save_{game_id}"):

                for pid, gid, new_status in updated:
                    attendance_df.loc[
                        (attendance_df["player_id"] == pid) &
                        (attendance_df["game_id"] == gid),
                        "status"
                    ] = new_status

                st.success(f"Saved all attendance updates for {game_date}")
                commit_changes()
