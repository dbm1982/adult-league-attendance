import gspread
import pandas as pd
import datetime
from zoneinfo import ZoneInfo

# ---------------------------------------------------------
# GOOGLE SHEETS CONNECTION
# ---------------------------------------------------------
# Assumes you already authenticate gspread in app.py or earlier.
# If you authenticate here, adjust accordingly.
eastern = ZoneInfo("America/New_York")


# ---------------------------------------------------------
# LOADERS
# ---------------------------------------------------------
def load_players_df():
    gc = gspread.service_account()
    sheet = gc.open("AdultLeague")  # <-- CHANGE if your sheet name differs
    ws = sheet.worksheet("Players")
    rows = ws.get_all_records()
    return pd.DataFrame(rows)


def load_games_df():
    gc = gspread.service_account()
    sheet = gc.open("AdultLeague")  # <-- CHANGE if your sheet name differs
    ws = sheet.worksheet("Games")
    rows = ws.get_all_records()

    df = pd.DataFrame(rows)

    # Convert date column to datetime
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")

    return df


def load_attendance_df():
    gc = gspread.service_account()
    sheet = gc.open("AdultLeague")  # <-- CHANGE if your sheet name differs
    ws = sheet.worksheet("Attendance")
    rows = ws.get_all_records()
    return pd.DataFrame(rows)


# ---------------------------------------------------------
# COMMIT ATTENDANCE CHANGES
# ---------------------------------------------------------
def commit_attendance_changes(attendance_df, reload_after_save=True):
    """
    Writes the entire attendance_df back to Google Sheets.
    This is used by captain_view and player_view.
    """

    gc = gspread.service_account()
    sheet = gc.open("AdultLeague")  # <-- CHANGE if your sheet name differs
    ws = sheet.worksheet("Attendance")

    headers = ["player_id", "game_id", "status", "updated_at"]

    # Convert DataFrame → list-of-lists
    output = [headers] + attendance_df[headers].values.tolist()

    ws.update(output)

    if reload_after_save:
        # Reload fresh data after saving
        rows = ws.get_all_records()
        return pd.DataFrame(rows)

    return attendance_df


# ---------------------------------------------------------
# SAVE ATTENDANCE (used internally by player view)
# ---------------------------------------------------------
def save_attendance(sheet, updates):
    """
    Legacy function — kept for compatibility.
    Captain view uses commit_attendance_changes instead.
    """

    attendance_sheet = sheet.worksheet("Attendance")
    rows = attendance_sheet.get_all_records()

    lookup = {(row["player_id"], row["game_id"]): i for i, row in enumerate(rows)}

    for update in updates:
        key = (update["player_id"], update["game_id"])
        if key in lookup:
            idx = lookup[key]
            rows[idx]["status"] = update["status"]
            rows[idx]["updated_at"] = datetime.datetime.now(eastern).isoformat()
        else:
            rows.append({
                "player_id": update["player_id"],
                "game_id": update["game_id"],
                "status": update["status"],
                "updated_at": datetime.datetime.now(eastern).isoformat()
            })

    headers = ["player_id", "game_id", "status", "updated_at"]
    output = [headers] + [[row[h] for h in headers] for row in rows]

    attendance_sheet.update(output)

    return True
