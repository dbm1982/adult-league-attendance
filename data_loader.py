import gspread
import streamlit as st

# ---------------------------------------------------------
# CONNECT TO GOOGLE SHEETS USING STREAMLIT SECRETS
# ---------------------------------------------------------

def connect_to_sheet():
    client = gspread.service_account_from_dict(st.secrets["gcp_service_account"])
    sheet = client.open("Adult Team Attendance Dev")
    return sheet



# ---------------------------------------------------------
# LOAD TEAMS
# ---------------------------------------------------------

def load_teams(sheet):
    teams_sheet = sheet.worksheet("Teams")
    return teams_sheet.get_all_records()


# ---------------------------------------------------------
# LOAD PLAYERS
# ---------------------------------------------------------

def load_players(sheet):
    players_sheet = sheet.worksheet("Players")
    rows = players_sheet.get_all_records()

    for row in rows:
        row["player_id"] = row["token"]

    return rows


# ---------------------------------------------------------
# LOAD GAMES
# ---------------------------------------------------------

def load_games(sheet):
    games_sheet = sheet.worksheet("Games")
    return games_sheet.get_all_records()


# ---------------------------------------------------------
# LOAD ATTENDANCE
# ---------------------------------------------------------

def load_attendance(sheet):
    attendance_sheet = sheet.worksheet("Attendance")
    return attendance_sheet.get_all_records()


# ---------------------------------------------------------
# MASTER LOADER
# ---------------------------------------------------------

def load_all_data():
    sheet = connect_to_sheet()

    data = {
        "teams": load_teams(sheet),
        "players": load_players(sheet),
        "games": load_games(sheet),
        "attendance": load_attendance(sheet),
        "sheet": sheet
    }

    return data
