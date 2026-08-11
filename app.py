import streamlit as st
import pandas as pd
import gspread

from captain_view import captain_view
from player_view import player_view
from ui_components import segmented_control

st.set_page_config(page_title="Adult Team Attendance", layout="wide")

# ---------------------------------------------------------
# CACHE DATA LOADING
# ---------------------------------------------------------

@st.cache_data(ttl=5)
def load_sheet_data():
    gc = gspread.service_account_from_dict(st.secrets["gcp_service_account"])
    sheet = gc.open_by_key("1afoSDWnUlB6ZN5Wlz4CDyX1whhzNNHxm6vCINs-2LDM")

    def sheet_to_df(ws):
        values = ws.get_all_values()
        if not values:
            return pd.DataFrame()
        header = values[0]
        rows = values[1:]
        return pd.DataFrame(rows, columns=header)

    teams_df = sheet_to_df(sheet.worksheet("Teams"))
    players_df = sheet_to_df(sheet.worksheet("Players"))
    games_df = sheet_to_df(sheet.worksheet("Games"))
    attendance_df = sheet_to_df(sheet.worksheet("Attendance"))

    return sheet, teams_df, players_df, games_df, attendance_df

sheet, teams_df, players_df, games_df, attendance_df = load_sheet_data()

# ---------------------------------------------------------
# SAVE ATTENDANCE (NO RELOAD)
# ---------------------------------------------------------

def save_attendance(updates):
    global attendance_df

    for player_id, game_id, status in updates:
        existing = attendance_df[
            (attendance_df["player_id"] == player_id) &
            (attendance_df["game_id"] == game_id)
        ]

        if existing.empty:
            attendance_df.loc[len(attendance_df)] = [
                player_id,
                game_id,
                status,
                str(pd.Timestamp.now()),
            ]
        else:
            attendance_df.loc[
                existing.index, ["status", "updated_at"]
            ] = [status, str(pd.Timestamp.now())]

    # Write to sheet
    attendance_ws = sheet.worksheet("Attendance")
    attendance_ws.update(
        [attendance_df.columns.values.tolist()] +
        attendance_df.values.tolist()
    )

    # DO NOT reload sheet here
    # Let Streamlit rerun with updated local dataframe
