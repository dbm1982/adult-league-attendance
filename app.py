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
# CSS
# --------------------------------------------------

st.markdown("""
<style>

.player-name {
    font-size: 14px;
    font-weight: 500;
    padding-top: 6px;
}

.column-header {
    padding: 8px 12px;
    border-radius: 8px;
    font-weight: 700;
    font-size: 16px;
    margin-bottom: 10px;
    color: black;
}

.header-yes { background-color: #4CAF50; color: white; }
.header-no { background-color: #F44336; color: white; }
.header-maybe { background-color: #FFEB3B; color: black; }

/* ⭐ FINAL FIX — NR must be TRUE BLACK for mobile contrast */
.header-nr { 
    background-color: #000000; 
    color: white;
}

</style>
""", unsafe_allow_html=True)

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

def short_name(full):
    parts = full.split()
    return f"{parts[0]} {parts[-1][0]}."

def save_attendance(attendance_sheet, player_id, game_id, status):
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
        if str(values[row_num][player_col]) == str(player_id) and str(values[row_num][game_col]) == str(game_id):
            row_index = row_num + 1
            break

    if row_index:
        attendance_sheet.update_cell(row_index, status_col + 1, spreadsheet_status)
        attendance_sheet.update_cell(row_index, updated_col + 1, timestamp)
    else:
        attendance_sheet.append_row([player_id, game_id, spreadsheet_status, timestamp])

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
spreadsheet = client.open_by_key("1afoSDWnUlB6ZN5Wlz4CDyX1whhzNNHxm6vCINs-2LDM")

teams_sheet = spreadsheet.worksheet("Teams")
players_sheet = spreadsheet.worksheet("Players")
games_sheet = spreadsheet.worksheet("Games")
attendance_sheet = spreadsheet.worksheet("Attendance")

teams_data = teams_sheet.get("A2:C100")
players = players_sheet.get_all_records()
games = games_sheet.get_all_records()
attendance = attendance_sheet.get_all_records()

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

selected_team = st.selectbox(
    "⚽ Select Your Team",
    teams,
    index=None,
    placeholder="Choose your team..."
)

if not selected_team:
    st.stop()

# --------------------------------------------------
# PLAYER SELECTION
# --------------------------------------------------

team_players = [p for p in players if str(p["team_id"]).strip() == str(selected_team).strip()]
player_names = [p["player_name"] for p in team_players]

selected_player = st.selectbox(
    "👤 Select Your Name",
    player_names,
    index=None,
    placeholder="Choose your name..."
)

if not selected_player:
    st.stop()

selected_player_record = next(p for p in team_players if p["player_name"] == selected_player)
selected_player_id = selected_player_record["player_id"]
is_captain = str(selected_player_record.get("is_captain", "")).upper() == "TRUE"

# --------------------------------------------------
# HEADER
# --------------------------------------------------

st.markdown("---")
st.markdown(f"### ⚽ {selected_team}")
st.markdown(f"### 👤 {selected_player}")
st.markdown("---")

# --------------------------------------------------
# CAPTAIN OPTIONS
# --------------------------------------------------

if is_captain:
    view_mode = st.radio(
        "Captain Options",
        ["My Availability", "Team Availability"],
        horizontal=False
    )
else:
    view_mode = "My Availability"

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

    for game in team_games:

        # Current status for selected player
        current_status = "No Response"
        for record in attendance:
            if str(record["player_id"]) == str(selected_player_id) and str(record["game_id"]) == str(game["game_id"]):
                s = str(record["status"]).strip()
                current_status = "No Response" if s in ("", "None") else s
                break

        # Game callout
        st.markdown(
            f"""
            <div style="
                background:#e8f5e9;
                padding:12px 16px;
                border-radius:10px;
                margin-bottom:12px;
                border-left:6px solid #2e7d32;
                color:#1b5e20;">
                <span style="font-size:18px; font-weight:700;">
                    GAME: {format_date(game.get('date',''))} — {game.get('time','')}
                </span><br>
                <span style="font-size:14px; font-weight:500;">
                    Field {game.get('field','')} • Opponent: {game.get('opponent','')}
                </span>
            </div>
            """,
            unsafe_allow_html=True
        )

        # --------------------------------------------------
        # MINI SUMMARY BAR
        # --------------------------------------------------

        yes_players = []
        no_players = []
        maybe_players = []
        none_players = []

        for player in team_players:
            player_status = "No Response"
            for record in attendance:
                if str(record["player_id"]) == str(player["player_id"]) and str(record["game_id"]) == str(game["game_id"]):
                    s = str(record["status"]).strip()
                    player_status = "No Response" if s in ("", "None") else s
                    break

            if player_status == "Yes":
                yes_players.append(player)
            elif player_status == "No":
                no_players.append(player)
            elif player_status == "Maybe":
                maybe_players.append(player)
            else:
                none_players.append(player)

        # --------------------------------------------------
        # CAPTAIN ALERT BAR
        # --------------------------------------------------

        if is_captain and view_mode == "Team Availability" and len(none_players) > 0:
            nr_names = ", ".join([short_name(p["player_name"]) for p in none_players])
            st.markdown(
                f"""
                <div style="
                    background-color:#f5f5f5;
                    border-left:5px solid #616161;
                    padding:8px 12px;
                    border-radius:6px;
                    margin:6px 0 14px 0;
                    font-size:13px;">
                    <strong>⚠️ {len(none_players)} players have not responded:</strong>
                    <span>{nr_names}</span>
                </div>
                """,
                unsafe_allow_html=True
            )

        # --------------------------------------------------
        # PLAYER VIEW
        # --------------------------------------------------

        if view_mode == "My Availability":

            options = ["No Response", "Yes", "No", "Maybe"]
            default_index = options.index(current_status) if current_status in options else 0

            selected_status = st.radio(
                "Update Availability",
                options,
                index=default_index,
                horizontal=False,
                key=f"attendance_{game['game_id']}"
            )

            if st.button("💾 Save Response", key=f"save_{game['game_id']}", type="primary"):
                save_attendance(attendance_sheet, selected_player_id, game["game_id"], selected_status)
                st.success("Attendance saved successfully.")
                st.rerun()

        # --------------------------------------------------
        # CAPTAIN VIEW (LOWEST LOAD + PLAYER LISTINGS)
        # --------------------------------------------------

        else:
            # Summary columns with player listings
            col_yes, col_no, col_maybe, col_none = st.columns(4)

            with col_yes:
                st.markdown(
                    f'<div class="column-header header-yes">YES ({len(yes_players)})</div>',
                    unsafe_allow_html=True
                )
                for p in yes_players:
                    st.markdown(f"- {p['player_name']}")

            with col_no:
                st.markdown(
                    f'<div class="column-header header-no">NO ({len(no_players)})</div>',
                    unsafe_allow_html=True
                )
                for p in no_players:
                    st.markdown(f"- {p['player_name']}")

            with col_maybe:
                st.markdown(
                    f'<div class="column-header header-maybe">MAYBE ({len(maybe_players)})</div>',
                    unsafe_allow_html=True
                )
                for p in maybe_players:
                    st.markdown(f"- {p['player_name']}")

            with col_none:
                st.markdown(
                    f'<div class="column-header header-nr">NR ({len(none_players)})</div>',
                    unsafe_allow_html=True
                )
                for p in none_players:
                    st.markdown(f"- {p['player_name']}")

            st.markdown("---")
            st.markdown("### 🧭 Update a player's status")

            # Captain picks ONE player to update
            player_to_update = st.selectbox(
                "Choose a player to update",
                [p["player_name"] for p in team_players],
                key=f"captain_player_select_{game['game_id']}"
            )

            selected_player_record_for_game = next(
                (p for p in team_players if p["player_name"] == player_to_update),
                None
            )

            current_player_status = "No Response"
            if selected_player_record_for_game:
                for record in attendance:
                    if (
                        str(record["player_id"]) == str(selected_player_record_for_game["player_id"])
                        and str(record["game_id"]) == str(game["game_id"])
                    ):
                        s = str(record["status"]).strip()
                        current_player_status = "No Response" if s in ("", "None") else s
                        break

            options = ["No Response", "Yes", "No", "Maybe"]
            default_index = options.index(current_player_status) if current_player_status in options else 0

            selected_status_for_player = st.radio(
                "Set status",
                options,
                index=default_index,
                horizontal=True,
                key=f"captain_status_{game['game_id']}"
            )

            if st.button("💾 Save Player Status", key=f"captain_save_{game['game_id']}"):
                if selected_player_record_for_game:
                    save_attendance(
                        attendance_sheet,
                        selected_player_record_for_game["player_id"],
                        game["game_id"],
                        selected_status_for_player
                    )
                    st.success(f"Updated {player_to_update} to {selected_status_for_player}.")
                    st.rerun()

except Exception as e:
    st.error(f"Games error: {e}")
