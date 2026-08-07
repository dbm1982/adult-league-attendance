import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# --------------------------------------------------
# PAGE CONFIG
# --------------------------------------------------

st.set_page_config(
    page_title="South Shore Adult Soccer League Portal",
    page_icon="⚽",
    layout="wide"
)

# --------------------------------------------------
# SESSION STATE
# --------------------------------------------------

if "selected_team" not in st.session_state:
    st.session_state.selected_team = None

if "selected_player" not in st.session_state:
    st.session_state.selected_player = None

if "view_mode" not in st.session_state:
    st.session_state.view_mode = "My Availability"

if "pending_updates" not in st.session_state:
    st.session_state.pending_updates = {}

# --------------------------------------------------
# CSS
# --------------------------------------------------

st.markdown(
    '<style>'
    '.column-header {padding:8px 12px; border-radius:8px; font-weight:700; font-size:16px; margin-bottom:10px;}'
    '.header-yes {background-color:#4CAF50; color:white;}'
    '.header-no {background-color:#F44336; color:white;}'
    '.header-maybe {background-color:#FFEB3B; color:black;}'
    '.header-nr {background-color:#1E88E5; color:white;}'
    '</style>',
    unsafe_allow_html=True
)

# --------------------------------------------------
# HELPERS
# --------------------------------------------------

def format_date(date_str):
    try:
        dt = datetime.strptime(str(date_str), "%Y-%m-%d")
        day = dt.day
        suffix = "th" if 4 <= day <= 20 or 24 <= day <= 30 else ["st", "nd", "rd"][min(day % 10 - 1, 2)]
        return dt.strftime(f"%B {day}{suffix}, %Y")
    except:
        return str(date_str)

def weekday(date_str):
    try:
        dt = datetime.strptime(str(date_str), "%Y-%m-%d")
        return dt.strftime("%A")
    except:
        return ""

def short_name(full):
    parts = full.split()
    return f"{parts[0]} {parts[-1][0]}."

def safe_write(func, *args, **kwargs):
    try:
        return func(*args, **kwargs)
    except Exception:
        import time
        time.sleep(0.3)
        try:
            return func(*args, **kwargs)
        except Exception:
            st.error("⚠️ Could not save your updates. Please try again.")
            st.stop()

def save_attendance(attendance_sheet, player_id, game_id, status):
    player_id = str(player_id).strip()
    game_id = str(game_id).strip()

    values = attendance_sheet.get_all_values()
    header = values[0]

    player_col = header.index("player_id")
    game_col = header.index("game_id")
    status_col = header.index("status")
    updated_col = header.index("updated_at")

    spreadsheet_status = "None" if status == "No Response" else status
    timestamp = datetime.now().strftime("%m/%d/%Y %H:%M:%S")

    row_index = None
    for row_num in range(1, len(values)):
        sheet_pid = str(values[row_num][player_col]).strip()
        sheet_gid = str(values[row_num][game_col]).strip()
        if sheet_pid == player_id and sheet_gid == game_id:
            row_index = row_num + 1
            break

    if row_index:
        safe_write(
            attendance_sheet.update,
            f"{chr(ord('A') + status_col)}{row_index}:{chr(ord('A') + updated_col)}{row_index}",
            [[spreadsheet_status, timestamp]]
        )
    else:
        safe_write(
            attendance_sheet.append_row,
            [player_id, game_id, spreadsheet_status, timestamp]
        )

# --------------------------------------------------
# GOOGLE CONNECTION
# --------------------------------------------------

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

creds = Credentials.from_service_account_info(
    dict(st.secrets["gcp_service_account"]),
    scopes=SCOPES
)

client = gspread.authorize(creds)

def safe_open_sheet(client, key):
    try:
        return client.open_by_key(key)
    except Exception:
        import time
        time.sleep(0.5)
        try:
            return client.open_by_key(key)
        except Exception:
            st.error("⚠️ The league database is temporarily unavailable. Please try again.")
            if st.button("🔄 Reload"):
                st.rerun()
            st.stop()

spreadsheet = safe_open_sheet(client, "1afoSDWnUlB6ZN5Wlz4CDyX1whhzNNHxm6vCINs-2LDM")

teams_sheet = spreadsheet.worksheet("Teams")
players_sheet = spreadsheet.worksheet("Players")
games_sheet = spreadsheet.worksheet("Games")
attendance_sheet = spreadsheet.worksheet("Attendance")

# --------------------------------------------------
# CACHING
# --------------------------------------------------

@st.cache_data(ttl=60)
def load_sheet_data():
    teams_data = teams_sheet.get("A2:C100")
    players = players_sheet.get_all_records()
    games = games_sheet.get_all_records()
    attendance = attendance_sheet.get_all_records()
    return teams_data, players, games, attendance

teams_data, players, games, attendance = load_sheet_data()

# --------------------------------------------------
# ACTIVE TEAMS
# --------------------------------------------------

teams = []
for row in teams_data:
    if len(row) < 3:
        continue
    team_name = str(row[1]).strip()
    active = str(row[2]).strip().upper()
    if active == "TRUE":
        teams.append(team_name)

teams = sorted(teams)

# --------------------------------------------------
# PAGE HEADER
# --------------------------------------------------

st.title("⚽ South Shore Adult Soccer League Portal")
st.caption("Select your team and your name to view upcoming games and attendance.")

# --------------------------------------------------
# TEAM SELECTION
# --------------------------------------------------

st.session_state.selected_team = st.selectbox(
    "⚽ Select Your Team",
    teams,
    index=teams.index(st.session_state.selected_team) if st.session_state.selected_team in teams else None,
    placeholder="Choose your team..."
)

selected_team = st.session_state.selected_team

if not selected_team:
    st.stop()

# --------------------------------------------------
# PLAYER SELECTION
# --------------------------------------------------

team_players = [p for p in players if str(p["team_id"]).strip() == str(selected_team).strip()]
player_names = [p["player_name"] for p in team_players]

st.session_state.selected_player = st.selectbox(
    "👤 Select Your Name",
    player_names,
    index=player_names.index(st.session_state.selected_player) if st.session_state.selected_player in player_names else None,
    placeholder="Choose your name..."
)

selected_player = st.session_state.selected_player

if not selected_player:
    st.stop()

selected_player_record = next(p for p in team_players if p["player_name"] == selected_player)
selected_player_id = str(selected_player_record["player_id"]).strip()
is_captain = str(selected_player_record.get("is_captain", "")).upper() == "TRUE"

st.markdown("---")
st.markdown(f"### ⚽ {selected_team}")
st.markdown(f"### 👤 {selected_player}")
st.markdown("---")

if is_captain:
    st.session_state.view_mode = st.radio(
        "Captain Options",
        ["My Availability", "Team Availability"],
        index=["My Availability", "Team Availability"].index(st.session_state.view_mode)
    )
else:
    st.session_state.view_mode = "My Availability"

view_mode = st.session_state.view_mode

st.markdown("---")

# --------------------------------------------------
# GAMES
# --------------------------------------------------

st.header("Upcoming Games")

try:
    team_games = [
        g for g in games
        if str(g.get("team_id", "")).strip() == str(selected_team).strip()
    ]

    today = datetime.now().date()
    team_games = [
        g for g in team_games
        if datetime.strptime(str(g["date"]), "%Y-%m-%d").date() >= today
    ]

    team_games = sorted(team_games, key=lambda x: x["date"])

    if not team_games:
        st.warning("No games found.")
        st.stop()

    # --------------------------------------------------
    # PLAYER SUMMARY
    # --------------------------------------------------

    if view_mode == "My Availability":
        st.markdown("### 🗂️ Your Availability Summary")

        summary_html = '<div style="padding:10px 0;">'
        for g in team_games:
            status = "No Response"
            for record in attendance:
                if str(record["player_id"]).strip() == selected_player_id and str(record["game_id"]).strip() == str(g["game_id"]).strip():
                    s = str(record["status"]).strip()
                    status = "No Response" if s in ("", "None") else s
                    break

            icon = {"Yes":"🟢","No":"🔴","Maybe":"🟡","No Response":"⚪"}[status]

            summary_html += (
                f'<div style="font-size:15px; margin-bottom:4px;">'
                f'{icon} {weekday(g["date"])}, {format_date(g["date"])} — {status}'
                f'</div>'
            )
        summary_html += '</div>'
        st.markdown(summary_html, unsafe_allow_html=True)
        st.markdown("---")

    # --------------------------------------------------
    # CAPTAIN SUMMARY
    # --------------------------------------------------

    if is_captain and view_mode == "Team Availability":
        st.markdown("### 🟢 Quick Commitment Summary")

        summary_html = '<div style="margin-bottom:20px;">'
        for g in team_games:
            yes_count = sum(
                1 for record in attendance
                if str(record["game_id"]).strip() == str(g["game_id"]).strip()
                and str(record["status"]).strip() == "Yes"
            )

            summary_html += (
                f'<div style="padding:8px 12px; margin-bottom:6px; '
                'border-left:4px solid #B0BEC5; background:#FAFAFA; font-size:14px;">'
                f'<strong>{weekday(g["date"])}, {format_date(g["date"])}</strong> — '
                f'{g["time"]} vs {g["opponent"]} — '
                f'<strong>{yes_count} Yes</strong>'
                f'</div>'
            )
        summary_html += '</div>'
        st.markdown(summary_html, unsafe_allow_html=True)

    # --------------------------------------------------
    # SAVE ALL BUTTON (TOP)
    # --------------------------------------------------

    if st.session_state.pending_updates:
        st.markdown("### 💾 Save All Updates")
        if st.button("✅ Save All Updates Now"):
            for (pid, gid), status in st.session_state.pending_updates.items():
                save_attendance(attendance_sheet, pid, gid, status)
            st.session_state.pending_updates = {}
            st.success("All updates saved.")
            st.rerun()

    # --------------------------------------------------
    # GAME LOOP
    # --------------------------------------------------

    for game in team_games:
        game_id = str(game["game_id"]).strip()

        # Current player status
        current_status = "No Response"
        for record in attendance:
            if str(record["player_id"]).strip() == selected_player_id and str(record["game_id"]).strip() == game_id:
                s = str(record["status"]).strip()
                current_status = "No Response" if s in ("", "None") else s
                break

        field_clean = str(game.get("field", "")).replace("Field ", "")

        game_html = (
            '<div style="background:#e8f5e9; padding:12px 16px; border-radius:10px; '
            'margin-bottom:12px; border-left:6px solid #2e7d32; color:#1b5e20; font-size:16px;">'
            f'<div style="font-size:18px; font-weight:700; margin-bottom:6px;">'
            f'🗓️ {weekday(game["date"])}, {format_date(game["date"])} • {game["time"]}'
            '</div>'
            f'<div style="margin-bottom:4px;">📍 Field {field_clean}</div>'
            f'<div>⚔️ Opponent: {game["opponent"]}</div>'
            '</div>'
        )
        st.markdown(game_html, unsafe_allow_html=True)

        # Build team status lists
        yes_players = []
        no_players = []
        maybe_players = []
        none_players = []

        for player in team_players:
            pid = str(player["player_id"]).strip()
            pstatus = "No Response"
            for record in attendance:
                if str(record["player_id"]).strip() == pid and str(record["game_id"]).strip() == game_id:
                    s = str(record["status"]).strip()
                    pstatus = "No Response" if s in ("", "None") else s
                    break

            if pstatus == "Yes":
                yes_players.append(player)
            elif pstatus == "No":
                no_players.append(player)
            elif pstatus == "Maybe":
                maybe_players.append(player)
            else:
                none_players.append(player)

        # PLAYER VIEW
        if view_mode == "My Availability":
            options = ["No Response", "Yes", "No", "Maybe"]
            selected_status = st.radio(
                "Can you make this game?",
                options,
                index=options.index(current_status),
                key=f"attendance_{game_id}"
            )

            if st.button("💾 Add to Updates", key=f"save_{game_id}", type="primary"):
                st.session_state.pending_updates[(selected_player_id, game_id)] = selected_status
                st.success("Change stored. Save all updates at the top.")

        # CAPTAIN VIEW
        else:
            col_yes, col_no, col_maybe, col_none = st.columns(4)

            col_yes.markdown(f'<div class="column-header header-yes">YES ({len(yes_players)})</div>', unsafe_allow_html=True)
            for p in yes_players:
                col_yes.markdown(f"- {p['player_name']}")

            col_no.markdown(f'<div class="column-header header-no">NO ({len(no_players)})</div>', unsafe_allow_html=True)
            for p in no_players:
                col_no.markdown(f"- {p['player_name']}")

            col_maybe.markdown(f'<div class="column-header header-maybe">MAYBE ({len(maybe_players)})</div>', unsafe_allow_html=True)
            for p in maybe_players:
                col_maybe.markdown(f"- {p['player_name']}")

            col_none.markdown(f'<div class="column-header header-nr">NR ({len(none_players)})</div>', unsafe_allow_html=True)
            for p in none_players:
                col_none.markdown(f"- {p['player_name']}")

            st.markdown("---")
            st.markdown("### 🧭 Update a player's status")

            player_to_update = st.selectbox(
                "Choose a player to update",
                [p["player_name"] for p in team_players],
                key=f"captain_player_select_{game_id}"
            )

            selected_player_record_for_game = next(
                (p for p in team_players if p["player_name"] == player_to_update),
                None
            )

            pid = str(selected_player_record_for_game["player_id"]).strip()

            current_player_status = "No Response"
            for record in attendance:
                if str(record["player_id"]).strip() == pid and str(record["game_id"]).strip() == game_id:
                    s = str(record["status"]).strip()
                    current_player_status = "No Response" if s in ("", "None") else s
                    break

            options = ["No Response", "Yes", "No", "Maybe"]
            selected_status_for_player = st.radio(
                "Set status",
                options,
                index=options.index(current_player_status),
                horizontal=True,
                key=f"captain_status_{game_id}"
            )

            if st.button("💾 Add Player Change", key=f"captain_save_{game_id}"):
                st.session_state.pending_updates[(pid, game_id)] = selected_status_for_player
                st.success(f"Stored change for {player_to_update}. Save all updates at the top.")

        # Divider between games
        st.markdown(
            '<hr style="border:0; height:3px; background:#0D47A1; margin:40px 0;">',
            unsafe_allow_html=True
        )

    # --------------------------------------------------
    # SAVE ALL UPDATES (BOTTOM — SAFETY NET)
    # --------------------------------------------------

    if st.session_state.pending_updates:
        st.markdown("### 💾 Save All Updates")
        if st.button("✅ Save All Updates Now", key="save_all_bottom"):
            for (pid, gid), status in st.session_state.pending_updates.items():
                save_attendance(attendance_sheet, pid, gid, status)
            st.session_state.pending_updates = {}
            st.success("All updates saved.")
            st.rerun()

# --------------------------------------------------
# GLOBAL ERROR HANDLER
# --------------------------------------------------

except Exception as e:
    st.error("⚠️ Something went wrong while loading games. Please try again.")
    if st.button("🔄 Reload games"):
        st.rerun()

