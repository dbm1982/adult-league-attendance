import gspread
import pandas as pd
import datetime
from zoneinfo import ZoneInfo
import streamlit as st

eastern = ZoneInfo("America/New_York")

# ---------------------------------------------------------
# GOOGLE SHEETS CLIENT (Streamlit Cloud secrets)
# ---------------------------------------------------------
def get_client():
    return gspread.service_account_from_dict(st.secrets["gcp_service_account"])


# ---------------------------------------------------------
# LOADERS
# ---------------------------------------------------------
def load_players_df():
    gc = get_client()
    sheet = gc.open("AdultLeague")   # <-- change if needed
    ws = sheet.worksheet("Players")
    rows = ws.get_all_records()
    return pd.DataFrame(rows)


def load_games_df():
    gc = get_client()
    sheet = gc.open("AdultLeague")   # <-- change if needed
    ws = sheet.worksheet("Games")
    rows = ws.get_all_records()

    df = pd.DataFrame(rows)

    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")

    return df


def load_attendance_df():
    gc = get_client()
    sheet = gc.open("AdultLeague")   # <-- change if needed
    ws = sheet.worksheet("Attendance")
    rows = ws.get_all_records()
    return pd.DataFrame(rows)


# ---------------------------------------------------------
# COMMIT ATTENDANCE CHANGES
# ---------------------------------------------------------
def commit_attendance_changes(attendance_df, reload_after_save=True):
    gc = get_client()
    sheet = gc.open("AdultLeague")   # <-- change if needed
    ws = sheet.worksheet("Attendance")

    headers = ["player_id", "game_id", "status", "updated_at"]
    output = [headers] + attendance_df[headers].values.tolist()

    ws.update(output)

    if reload_after_save:
        rows = ws.get_all_records()
        return pd.DataFrame(rows)

    return attendance_df


# ---------------------------------------------------------
# LEGACY SAVE FUNCTION (player view)
# ---------------------------------------------------------
def save_attendance(sheet, updates):
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
