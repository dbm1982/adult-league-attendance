import streamlit as st
import pandas as pd

def player_view(players_df, games_df, attendance_df, team_id, player_name, commit_changes):

    # ---------------------------------------------------------
    # HARD DEDUPE: remove duplicates from the sheet data
    # ---------------------------------------------------------
    attendance_df = attendance_df.drop_duplicates(
        subset=["player_id", "game_id"],
        keep="last"
    ).reset_index(drop=True)

    # ---------------------------------------------------------
    # Identify player
    # ---------------------------------------------------------
    player_row = players_df[players_df["player_name"] == player_name].iloc[0]
    player_token = player_row["token"]

    # ---------------------------------------------------------
    # MICRO TIMELINE SUMMARY (tiny row of dates + colors)
    # ---------------------------------------------------------
    st.subheader("Your Season Calendar")

    season_game_ids = set(games_df["game_id"])

    player_att = attendance_df[
        (attendance_df["player_id"] == player_token) &
        (attendance_df["game_id"].isin(season_game_ids))
    ]

    # Dedupe again (in case sheet had issues)
    player_att = player_att.drop_duplicates(subset=["game_id"], keep="last")

    merged = player_att.merge(games_df, on="game_id").sort_values("date")

    emoji_map = {
        "Yes": "🟢",
        "No": "🔴",
        "Maybe": "🟡",
        "No Response": "⚪"
    }

    timeline = []
    for _, row in merged.iterrows():
        date_short = pd.to_datetime(row["date"]).strftime("%m/%d")
        status = row["status"]
        emoji = emoji_map.get(status, "⚪")
        timeline.append(f"{emoji} {date_short}")

    st.write("   ".join(timeline))

    # ---------------------------------------------------------
    # UPCOMING GAMES
    # ---------------------------------------------------------
    today = pd.Timestamp.now()
    upcoming_games = games_df[
        (games_df["team_id"] == team_id) &
        (games_df["date"] >= today)
    ].sort_values("date")

    if upcoming_games.empty:
        st.info("No upcoming games found.")
        return

    valid_statuses = ["Yes", "No", "Maybe", "No Response"]

    # ---------------------------------------------------------
    # GAME LOOP
    # ---------------------------------------------------------
    for _, game in upcoming_games.iterrows():

        game_id = game["game_id"]
        game_date = game["display_date"]
        game_time = game["display_time"]
        opponent = game["opponent"]
        field = game["field"]

        mask = (
            (attendance_df["player_id"] == player_token) &
            (attendance_df["game_id"] == game_id)
        )

        if attendance_df.loc[mask].empty:
            current_status = "No Response"
        else:
            current_status = attendance_df.loc[mask, "status"].iloc[-1]

        normalized = str(current_status).strip().lower()
        mapping = {
            "yes": "Yes",
            "no": "No",
            "maybe": "Maybe",
            "no response": "No Response",
            "": "No Response",
            "none": "No Response",
            "nr": "No Response",
        }
        current_status = mapping.get(normalized, "No Response")

        card = st.container(border=True)

        with card:
            st.write(f"### {game_date} — {game_time}")
            st.write(f"**vs {opponent}**")
            st.write(f"Field {field}")
            st.write(f"*Your current response: {current_status}*")

            st.divider()

            new_status = st.radio(
                "Response",
                valid_statuses,
                index=valid_statuses.index(current_status),
                horizontal=True,
                key=f"player_{player_token}_{game_id}"
            )

            if st.button(f"Save Changes for {game_date}", key=f"save_{player_token}_{game_id}"):

                # UPDATE instead of append
                if attendance_df.loc[mask].empty:
                    attendance_df.loc[len(attendance_df)] = {
                        "player_id": player_token,
                        "game_id": game_id,
                        "status": new_status
                    }
                else:
                    attendance_df.loc[mask, "status"] = new_status

                # HARD DEDUPE before saving back
                attendance_df = attendance_df.drop_duplicates(
                    subset=["player_id", "game_id"],
                    keep="last"
                ).reset_index(drop=True)

                st.success(f"Saved changes for {game_date}")

                commit_changes(attendance_df)
