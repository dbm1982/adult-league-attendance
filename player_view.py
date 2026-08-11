import streamlit as st
import pandas as pd

def player_view(players_df, games_df, attendance_df, team_id, player_name, save_attendance):

    # Identify player
    player_row = players_df[players_df["player_name"] == player_name].iloc[0]
    player_token = player_row["token"]

    # -----------------------------
    # SEASON SUMMARY
    # -----------------------------
    st.subheader("Season Summary")

    player_att = attendance_df[attendance_df["player_id"] == player_token]
    summary = player_att["status"].value_counts().to_dict()

    for status in ["Yes", "No", "Maybe", "No Response"]:
        st.write(f"{status}: {summary.get(status, 0)} games")

    # -----------------------------
    # UPCOMING GAMES
    # -----------------------------
    today = pd.Timestamp.now()
    upcoming_games = games_df[
        (games_df["team_id"] == team_id) &
        (games_df["date"] >= today)
    ].sort_values("date")

    if upcoming_games.empty:
        st.info("No upcoming games found.")
        return

    valid_statuses = ["Yes", "No", "Maybe", "No Response"]

    # Color map for game cards
    color_map = {
        "Yes": "#e8f8f0",        # soft green
        "No": "#fdecea",         # soft red
        "Maybe": "#fff8e1",      # soft yellow
        "No Response": "#f2f2f2" # soft gray
    }

    for _, game in upcoming_games.iterrows():

        game_date = game["display_date"]
        game_time = game["display_time"]
        opponent = game["opponent"]
        field = game["field"]

    # -----------------------------
    # CURRENT STATUS
    # -----------------------------
    raw = attendance_df.loc[
        (attendance_df["player_id"] == player_token) &
        (attendance_df["game_id"] == game["game_id"]),
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


        # -----------------------------
        # GAME CARD (color-coded)
        # -----------------------------
        st.markdown(
            f"""
            <div style="
                padding:16px;
                border-radius:12px;
                border:1px solid #DDD;
                margin-bottom:18px;
                background:{bg_color};
            ">
                <h4 style="margin:0 0 6px 0;">{game_date} — {game_time}</h4>
                <div style="font-size:16px;"><strong>vs {opponent}</strong></div>
                <div style="color:#555; margin-bottom:12px;">{field}</div>
                <div style="font-size:14px; color:#333;">
                    <em>Current response: {current_status}</em>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        # -----------------------------
        # STATUS SELECTOR
        # -----------------------------
        new_status = st.radio(
            f"{player_name}",
            valid_statuses,
            index=valid_statuses.index(current_status),
            horizontal=True,
            key=f"player_{player_token}_{game['game_id']}"
        )

        # -----------------------------
        # SAVE BUTTON
        # -----------------------------
        if st.button(
            f"Save Changes for {game_date}",
            key=f"save_{player_token}_{game['game_id']}"
        ):
            save_attendance([(player_token, game["game_id"], new_status)])
            st.success(f"Saved changes for {game_date}")
