import streamlit as st
import pandas as pd

def captain_view(players_df, games_df, attendance_df, team_id, commit_changes):

    st.title("Captain View")
    st.info("Expand a game below to see player attendance and make updates.")

    # ---------------------------------------------------------
    # STATUS / SAVE FEEDBACK
    # ---------------------------------------------------------

    if "unsaved_changes" not in st.session_state:
        st.session_state.unsaved_changes = False

    if "last_saved" in st.session_state:
        st.info(f"Last saved at {st.session_state.last_saved}")

    if st.session_state.unsaved_changes:
        st.warning("You have unsaved changes.")

    # ---------------------------------------------------------
    # FILTER TEAM DATA
    # ---------------------------------------------------------

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

    # Build lookup from in-memory attendance_df (NO SHEET READS)
    attendance_lookup = {
        (row["player_id"], row["game_id"]): row["status"]
        for _, row in attendance_df.iterrows()
    }

    # ---------------------------------------------------------
    # CSS FOR PILLS
    # ---------------------------------------------------------
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

    # ---------------------------------------------------------
    # GAME LOOP
    # ---------------------------------------------------------
    for _, game in upcoming_games.iterrows():

        game_id = game["game_id"]
        game_date = game["display_date"]
        game_time = game["display_time"]
        opponent = game["opponent"]

        # Group attendance
        grouped = {s: [] for s in valid_statuses}

        for _, player in team_players.iterrows():
            pid = player["token"]
            raw = attendance_lookup.get((pid, game_id), "No Response")
            status = str(raw).strip().capitalize()
            status = status if status in valid_statuses else "No Response"
            grouped[status].append(player["player_name"])

        yes_count = len(grouped["Yes"])
        unconfirmed_count = len(grouped["Maybe"]) + len(grouped["No Response"])

        st.markdown("---")
        st.write(f"### {game_date} — {game_time}")
        st.write(f"**vs {opponent}**")

        colA, colB = st.columns(2)
        with colA:
            st.write(f"**Playing:** {yes_count}")
        with colB:
            st.write(f"**Unconfirmed:** {unconfirmed_count}")

        # ---------------------------------------------------------
        # EXPANDER
        # ---------------------------------------------------------
        with st.expander("View Details", expanded=False):

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

                # Mark unsaved changes
                if new_status != status:
                    st.session_state.unsaved_changes = True

            # ---------------------------------------------------------
            # SAVE BUTTON — ONE WRITE ONLY
            # ---------------------------------------------------------
            if st.button(f"Save All Changes for {game_date}", key=f"save_{game_id}"):

                # Update in-memory DataFrame (NO SHEET READS)
                for pid, gid, new_status in updated:
                    attendance_df.loc[
                        (attendance_df["player_id"] == pid) &
                        (attendance_df["game_id"] == gid),
                        "status"
                    ] = new_status

                # Write once
                commit_changes()

                st.session_state.unsaved_changes = False
                st.success(f"Saved all attendance updates for {game_date}")
