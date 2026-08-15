import streamlit as st
import pandas as pd
import gspread
from datetime import datetime

from captain_view import captain_view
from player_view import player_view

st.set_page_config(page_title="Adult Team Attendance", layout="wide")

# ---------------------------------------------------------
# CONNECT TO GOOGLE SHEETS ONCE
# ---------------------------------------------------------

gc = gspread.service_account_from_dict(st.secrets["gcp_service_account"])
sheet = gc.open_by_key("1afoSDWnUlB6ZN5Wlz4CDyX1whhzNNHxm6vCINs-2LDM")

def sheet_to_df(ws):
    values = ws.get_all_values()
    if not values:
        return pd.DataFrame()
    header = values[0]
    rows = values[1:]
    return pd.DataFrame(rows, columns=header)

# ---------------------------------------------------------
# LOAD ALL SHEETS ONCE INTO SESSION STATE
# ---------------------------------------------------------

if "teams_df" not in st.session_state:
    st.session_state.teams_df = sheet_to_df(sheet.worksheet("Teams"))

if "players_df" not in st.session_state:
    st.session_state.players_df = sheet_to_df(sheet.worksheet("Players"))

if "games_df" not in st.session_state:
    st.session_state.games_df = sheet_to_df(sheet.worksheet("Games"))

if "attendance_df" not in st.session_state:
    raw_df = sheet_to_df(sheet.worksheet("Attendance"))
    raw_df.columns = raw_df.columns.str.strip().str.lower()

    # Deduplicate once
    raw_df = raw_df.drop_duplicates(
        subset=["player_id", "game_id"],
        keep="last"
    ).reset_index(drop=True)

    st.session_state.attendance_df = raw_df

# Always work on the in-memory DataFrames
teams_df = st.session_state.teams_df
players_df = st.session_state.players_df
games_df = st.session_state.games_df
attendance_df = st.session_state.attendance_df

# ---------------------------------------------------------
# CLEANUP (safe because no more reads)
# ---------------------------------------------------------

teams_df.columns = teams_df.columns.str.strip().str.lower()
players_df.columns = players_df.columns.str.strip().str.lower()
games_df.columns = games_df.columns.str.strip().str.lower()

teams_df["team_id"] = teams_df["team_id"].astype(str).str.strip()
players_df["team_id"] = players_df["team_id"].astype(str).str.strip()
games_df["team_id"] = games_df["team_id"].astype(str).str.strip()

players_df["player_name"] = players_df["player_name"].astype(str).str.strip()

teams_df["active"] = teams_df["active"].astype(str).str.lower().isin(["true", "yes", "1"])
players_df["is_captain"] = players_df["is_captain"].astype(str).str.lower().isin(["true", "yes", "1"])

games_df["date"] = pd.to_datetime(games_df["date"], errors="coerce")
games_df["display_date"] = games_df["date"].dt.strftime("%A, %b %d")
games_df["display_time"] = pd.to_datetime(
    games_df["time"], format="%I:%M %p", errors="coerce"
).dt.strftime("%-I:%M %p")

st.write("DEBUG — Parsed game dates:", games_df[["game_id", "date"]])
st.write("DEBUG — All games for Gray:", games_df[games_df["team_id"] == "Gray"])





# ---------------------------------------------------------
# LOGIN FLOW
# ---------------------------------------------------------

st.title("Adult Soccer Attendance Portal at Union Point")

active_teams = teams_df[teams_df["active"] == True]["team_id"].tolist()
team_options = ["-- Select Team --"] + active_teams

selected_team = st.selectbox("Select your team:", team_options)
if selected_team == "-- Select Team --":
    st.stop()

team_players = players_df[players_df["team_id"] == selected_team].copy()
player_options = ["-- Select Player --"] + team_players["player_name"].tolist()

selected_player_name = st.selectbox("Select your name:", player_options)
if selected_player_name == "-- Select Player --":
    st.stop()

player_row = team_players[team_players["player_name"] == selected_player_name].iloc[0]
player_token = player_row["token"]
team_id = player_row["team_id"]
is_captain = player_row["is_captain"]

st.success(f"Logged in as {selected_player_name} ({team_id})")

st.write("DEBUG — Attendance for Gray:", attendance_df[attendance_df["player_id"] == player_token])
st.write("DEBUG — Logged in team_id:", team_id)
# ---------------------------------------------------------
# COMMIT FUNCTION — ONE WRITE ONLY
# ---------------------------------------------------------

attendance_ws = sheet.worksheet("Attendance")

def commit_attendance_changes(reload_after_save=False):
    df = st.session_state.attendance_df

    # Write once
    attendance_ws.update(
        [df.columns.values.tolist()] +
        df.values.tolist()
    )

    st.session_state.last_saved = datetime.now().strftime("%I:%M %p")
    st.session_state.unsaved_changes = False

    st.success("All attendance changes have been saved.")

    # Optional reload (ONE read)
    if reload_after_save:
        new_df = sheet_to_df(attendance_ws)
        new_df.columns = new_df.columns.str.strip().str.lower()
        st.session_state.attendance_df = new_df

# ---------------------------------------------------------
# VIEW SWITCH
# ---------------------------------------------------------

if is_captain:

    tab_player, tab_captain = st.tabs(["👤 Player View", "⚽ Captain View"])

    with tab_player:
        player_view(
            players_df,
            games_df,
            st.session_state.attendance_df,
            team_id,
            selected_player_name,
            commit_attendance_changes
        )

    with tab_captain:
        captain_view(
            players_df,
            games_df,
            st.session_state.attendance_df,
            team_id,
            commit_attendance_changes
        )

else:
    player_view(
        players_df,
        games_df,
        st.session_state.attendance_df,
        team_id,
        selected_player_name,
        commit_attendance_changes
    )
