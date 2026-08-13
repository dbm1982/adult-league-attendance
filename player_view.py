import streamlit as st
import pandas as pd

def player_view(players_df, games_df, attendance_df, team_id, player_name, commit_changes):

    # Identify player
    player_row = players_df[players_df["player_name"] == player_name].iloc[0]
    player_token = player_row["token"]

    # ALWAYS use the real session DataFrame
    df = st.session_state.attendance_df

    # HARD DEDUPE
    df = df.drop_duplicates(subset=["player_id", "game_id"], keep="last").reset_index(drop=True)
    st.session_state.attendance_df = df

    # ---------------------------------------------------------
    # MICRO TIMELINE SUMMARY
    # ---------------------------------------------------------
    
    st.subheader("Your Season Calendar")
    
    # Only games for THIS team
    team_games = games_df[games_df["team_id"] == team_id].copy()
    
    # Attendance for this player
    player_att = st.session_state.attendance_df[
        st.session_state.attendance_df["player_id"] == player_token
    ].copy()
    
    # Merge so that ALL games appear, even with no attendance yet
    merged = (
        team_games
        .merge(player_att, on="game_id", how="left")
        .sort_values("date")
    )
    
    # Normalize status
    merged["status"] = (
        merged["status"]
        .fillna("No Response")
        .replace(["", "none", "None", "NR"], "No Response")
    )
    
    emoji_map = {
        "Yes": "🟢",
        "No": "🔴",
        "Maybe": "🟡",
        "No Response": "⚪"   # light gray / empty circle
    }
    
    timeline = []
    for _, row in merged.iterrows():
        date_short = pd.to_datetime(row["date"]).strftime("%m/%d")
        status = row["status"]
        emoji = emoji_map.get(status, "⚪")
        timeline.append(f"{emoji} {date_short}")
    
    st.write("   ".join(timeline))


    # UPCOMING GAMES
    today = pd.Timestamp.now()
    upcoming_games = games_df[
        (games_df["team_id"] == team_id) &
        (games_df["date"] >= today)
    ].sort_values("date")

    if upcoming_games.empty:
        st.info("No upcoming games found.")
        return

    valid_statuses = ["Yes", "No", "Maybe", "No Response"]

    for _, game in upcoming_games.iterrows():

        game_id = game["game_id"]
        mask = (df["player_id"] == player_token) & (df["game_id"] == game_id)

        current_status = (
            df.loc[mask, "status"].iloc[-1]
            if not df.loc[mask].empty
            else "No Response"
        )

        normalized = str(current_status).strip().lower()
        mapping = {
            "yes": "Yes", "no": "No", "maybe": "Maybe",
            "no response": "No Response", "": "No Response",
            "none": "No Response", "nr": "No Response"
        }
        current_status = mapping.get(normalized, "No Response")

        card = st.container(border=True)

        with card:
            st.write(f"### {game['display_date']} — {game['display_time']}")
            st.write(f"**vs {game['opponent']}**")
            st.write(f"Field {game['field']}")
            st.write(f"*Your current response: {current_status}*")

            st.divider()

            new_status = st.radio(
                "Response",
                valid_statuses,
                index=valid_statuses.index(current_status),
                horizontal=True,
                key=f"player_{player_token}_{game_id}"
            )

            if st.button(f"Save Changes for {game['display_date']}", key=f"save_{player_token}_{game_id}"):

                # UPDATE or INSERT
                if df.loc[mask].empty:
                    st.session_state.attendance_df.loc[len(df)] = {
                        "player_id": player_token,
                        "game_id": game_id,
                        "status": new_status
                    }
                else:
                    st.session_state.attendance_df.loc[mask, "status"] = new_status

                # HARD DEDUPE
                st.session_state.attendance_df = (
                    st.session_state.attendance_df
                    .drop_duplicates(subset=["player_id", "game_id"], keep="last")
                    .reset_index(drop=True)
                )

                st.success(f"Saved changes for {game['display_date']}")

                commit_changes()
