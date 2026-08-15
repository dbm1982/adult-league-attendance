import gspread
import pandas as pd
import datetime
from zoneinfo import ZoneInfo
import streamlit as st

eastern = ZoneInfo("America/New_York")

def get_client():
    return gspread.service_account_from_dict(st.secrets["gcp_service_account"])

def load_players_df():
    gc = get_client()
    sheet = gc.open("Adult Team Attendance Dev")
    ws = sheet.worksheet("Players")
    rows = ws.get_all_records()
    return pd.DataFrame(rows)

def load_games_df():
    gc = get_client()
    sheet = gc.open("Adult Team Attendance Dev")
    ws = sheet.worksheet("Games")
    rows = ws.get_all_records()
    df = pd.DataFrame(rows)
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
    return df

def load_attendance_df():
    gc = get_client()
    sheet = gc.open("Adult Team Attendance Dev")
    ws = sheet.worksheet("Attendance")
    rows = ws.get_all_records()
    return pd.DataFrame(rows)

def load_teams_df():
    gc = get_client()
    sheet = gc.open("Adult Team Attendance Dev")
    ws = sheet.worksheet("Teams")
    rows = ws.get_all_records()
    return pd.DataFrame(rows)

def commit_attendance_changes(attendance_df, reload_after_save=True):
    gc = get_client()
    sheet = gc.open("Adult Team Attendance Dev")
    ws = sheet.worksheet("Attendance")

    headers = ["player_id", "game_id", "status", "updated_at"]
    output = [headers] + attendance_df[headers].values.tolist()
    ws.update(output)

    if reload_after_save:
        rows = ws.get_all_records()
        return pd.DataFrame(rows)

    return attendance_df
