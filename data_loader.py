import gspread
from google.oauth2.service_account import Credentials

# ---------------------------------------------------------
# CONNECT TO GOOGLE SHEETS
# ---------------------------------------------------------

def connect_to_sheet():
    """
    Connects to your Google Sheet using your service account.
    Returns the gspread client and the spreadsheet object.
    """

    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]

    creds = Credentials.from_service_account_file(
        "service_account.json",  # <-- your JSON file
        scopes=scopes
    )

    client = gspread.authorize(creds)

    # IMPORTANT: replace with your actual sheet name
    sheet = client.open("HAYSA League Data")

    return sheet


# ---------------------------------------------------------
# LOAD TEAMS
# ---------------------------------------------------------

def load_teams(sheet):
    teams_sheet = sheet.worksheet("Teams")
    rows = teams_sheet.get_all_records()
    return rows


# ---------------------------------------------------------
# LOAD PLAYERS
# ---------------------------------------------------------

def load_players(sheet):
    players_sheet = sheet.worksheet("Players")
    rows = players_sheet.get_all_records()

    # Rename token → player_id for clarity
    for row in rows:
        row["player_id"] = row["token"]

    return rows


# ---------------------------------------------------------
# LOAD GAMES
# ---------------------------------------------------------

def load_games(sheet):
    games_sheet = sheet.worksheet("Games")
    rows = games_sheet.get_all_records()
    return rows


# ---------------------------------------------------------
# LOAD ATTENDANCE
# ---------------------------------------------------------

def load_attendance(sheet):
    attendance_sheet = sheet.worksheet("Attendance")
    rows = attendance_sheet.get_all_records()
    return rows


# ---------------------------------------------------------
# MASTER LOADER (called once per session)
# ---------------------------------------------------------

def load_all_data():
    """
    Loads all league data at once.
    This function is called ONCE per Streamlit session.
    """

    sheet = connect_to_sheet()

    data = {
        "teams": load_teams(sheet),
        "players": load_players(sheet),
        "games": load_games(sheet),
        "attendance": load_attendance(sheet),
        "sheet": sheet  # keep reference for saving later
    }

    return data
