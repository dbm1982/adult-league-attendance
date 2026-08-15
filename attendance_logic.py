import gspread
import pandas as pd
import streamlit as st

SHEET_NAME = "Adult Team Attendance Dev"


def get_client():
    return gspread.service_account_from_dict(st.secrets["gcp_service_account"])


def load_players_df():
    gc = get_client()
    sheet = gc.open(SHEET_NAME)
    ws = sheet.worksheet("Players")
    rows = ws.get_all_records()
    df = pd.DataFrame(rows)

    if "team_id" in df.columns:
        df["team_id"] = df["team_id"].astype(str).str.strip()

    if "is_captain" in df.columns:
        df["is_captain"] = df["is_captain"].astype(str).str.upper().eq("TRUE")

    return df


def load_games_df():
    gc = get_client()
    sheet = gc.open(SHEET_NAME)
    ws = sheet.worksheet("Games")
    rows = ws.get_all_records()
    df = pd.DataFrame(rows)

    if "team_id" in df.columns:
        df["team_id"] = df["team_id"].astype(str).str.strip()

    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")

    return df


def load_attendance_df():
    gc = get_client()
    sheet = gc.open(SHEET_NAME)
    ws = sheet.worksheet("Attendance")
    rows = ws.get_all_records()
    df = pd.DataFrame(rows)

    if "player_id" in df.columns:
        df["player_id"] = df["player_id"].astype(str).str.strip()
    if "game_id" in df.columns:
        df["game_id"] = df["game_id"].astype(str).str.strip()
    if "status" in df.columns:
        df["status"] = df["status"].astype(str).str.strip()

    return df


def load_teams_df():
    gc = get_client()
    sheet = gc.open(SHEET_NAME)
    ws = sheet.worksheet("Teams")
    rows = ws.get_all_records()
    df = pd.DataFrame(rows)

    if "team_id" in df.columns:
        df["team_id"] = df["team_id"].astype(str).str.strip()
    if "active" in df.columns:
        df["active"] = df["active"].astype(str).str.upper().eq("TRUE")

    return df


def commit_attendance_changes(attendance_df, reload_after_save=True):
    gc = get_client()
    sheet = gc.open(SHEET_NAME)
    ws = sheet.worksheet("Attendance")

    headers = ["player_id", "game_id", "status", "updated_at"]
    output = [headers] + attendance_df[headers].values.tolist()
    ws.update(output)

    if reload_after_save:
        rows = ws.get_all_records()
        return pd.DataFrame(rows)

    return attendance_df
