import streamlit as st
import pandas as pd

def player_view(players_df, games_df, attendance_df, team_id, player_name, commit_changes):

    player_row = players_df[players_df["player_name"] == player_name].iloc[0]
    player_token = player_row["token"]

    # ---------------------------------------------------------
    # MINI CALENDAR SUMMARY (3-across grid, pure Streamlit)
    # ---------------------------------------------------------
    st.subheader("Your Season Calendar")

    player_att = attendance_df[attendance_df["player_id"] == player_token]
    merged = player_att.merge(games_df, on="game_id").sort_values("date")

    # Color mapping using emojis (dark-mode safe)
    emoji_map = {
        "Yes": "🟢",
        "No": "🔴",
        "Maybe": "🟡",
        "No Response": "⚪"
    }

    # Build items for the mini-calendar
    calendar_items = []
    for _, row in merged.iterrows():
        date_str = row["display_date"]
        status = row["status"]
        emoji = emoji_map.get(status, "⚪")
        calendar_items.append(f"{emoji}\n{date_str}")

    # Render 3-across grid
    for i in range(0, len(calendar_items), 3):
        row_items = calendar_items[i:i+3]
        cols = st.columns(len(row_items))
        for col, item in zip(cols, row_items):
            with col:
                st.markdown(f"### {item}")

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

    for _, game in upcoming_games.iterrows():

        game_id = game["game_id"]
        game_date = game["display_date"]
        game_time = game["display_time"]
        opponent = game["opponent"]
        field = game["field"]

        # Current status lookup
        raw = attendance_df.loc[
            (attendance_df["player_id"] == player_token) &
            (attendance_df["game_id"] == game_id),
            "status"
        ].values

        raw = raw[0] if len(raw) > 0 else "No Response"
        normalized = str(raw).strip().lower()

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

        # ---------------------------------------------------------
        # GAME CARD — PURE STREAMLIT (NO HTML, NO CSS)
        # ---------------------------------------------------------
        card = st.container(border=True)

        with card:
            st.write(f"### {game_date} — {game_time}")
            st.write(f"**vs {opponent}**")
            st.write(f"Field {field}")
            st.write(f"*Your current response: {current_status}*")

            st.divider()

            # ---------------------------------------------------------
            # RESPONSE RADIO
            # ---------------------------------------------------------
            new_status = st.radio(
                "Response",
                valid_statuses,
                index=valid_statuses.index(current_status),
                horizontal=True,
                key=f"player_{player_token}_{game_id}"
            )

            # ---------------------------------------------------------
            # SAVE BUTTON
            # ---------------------------------------------------------
            if st.button(f"Save Changes for {game_date}", key=f"save_{player_token}_{game_id}"):

                attendance_df.loc[
                    (attendance_df["player_id"] == player_token) &
                    (attendance_df["game_id"] == game_id),
                    "status"
                ] = new_status

                st.success(f"Saved changes for {game_date}")

                commit_changes()
