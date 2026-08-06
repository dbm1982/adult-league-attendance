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
# CSS — MODERN + COMPACT + COLUMN LAYOUT
# --------------------------------------------------

st.markdown("""
<style>

/* Base font */
html, body, [class*="css"] {
    font-size: 17px;
}

/* Game card */
.game-card {
    padding: 1rem;
    border-radius: 12px;
    background-color: #ffffff;
    margin-bottom: 1.25rem;
    border: 1px solid #e0e0e0;
    box-shadow: 0px 2px 6px rgba(0,0,0,0.06);
}

/* Captain column container */
.captain-columns {
    display: flex;
    flex-direction: row;
    gap: 12px;
    width: 100%;
}

/* Column widths (desktop) */
.column-yes, .column-no, .column-maybe {
    width: 20%;
}

.column-none {
    width: 40%;
}

/* Column card */
.captain-card {
    padding: 0.6rem;
    border-radius: 10px;
    background-color: #ffffff;
    border: 1px solid #e0e0e0;
    box-shadow: 0px 2px 6px rgba(0,0,0,0.06);
}

/* Column title */
.captain-card h3 {
    margin-top: 0;
    margin-bottom: 10px;
}

/* Player row — compact desktop */
@media (min-width: 800px) {
    .player-row {
        display: flex;
        flex-direction: column;
        margin-bottom: 8px;
    }

    .player-name {
        font-size: 15px;
        font-weight: 600;
        margin-bottom: 4px;
    }

    .player-buttons {
        display: flex;
        flex-direction: row;
        gap: 4px;
    }

    .player-buttons button {
        padding: 3px 6px !important;
        font-size: 13px !important;
        border-radius: 6px !important;
        min-width: 70px !important;
    }
}

/* Mobile layout */
@media (max-width: 799px) {
    .captain-columns {
        flex-direction: column;
    }

    .player-row {
        display: flex;
        flex-direction: column;
        margin-bottom: 12px;
    }

    .player-buttons button {
        padding: 6px 10px !important;
        font-size: 15px !important;
        border-radius: 8px !important;
        min-width: 100px !important;
    }
}

/* Color-coded buttons */
.status-yes > button {
    background-color: #4CAF50 !important;
    color: white !important;
}

.status-no > button {
    background-color: #F44336 !important;
    color: white !important;
}

.status-maybe > button {
    background-color: #FFB300 !important;
    color: black !important;
}

.status-none > button {
    background-color: #E0E0E0 !important;
    color: #555 !important;
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

def save_attendance(attendance_sheet, player_id, game_id, status):
    values = attendance_sheet.get_all_values()
    header = values[0]

    player_col = header.index("player_id")
    game_col = header.index("game_id")
    status_col = header.index("status")
    updated_col = header.index("updated_at")

    spreadsheet_status = "None" if status == "No Response" else status
    timestamp = datetime.now().strftime("%m/%d/%Y %H:%M:%S")

    for row_num in range(1, len(values)):
        if str(values[row_num][player_col]) == str(player_id) and str(values[row_num][game_col]) == str(game_id):
            attendance_sheet.update_cell(row_num + 1, status_col + 1, spreadsheet_status)
            attendance_sheet.update_cell(row_num + 1, updated_col + 1, timestamp)
            return "updated"

    attendance_sheet.append_row([player_id, game_id, spreadsheet_status, timestamp])
    return "created"

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

# --------------------------------------------------
# LOAD SHEETS
# --------------------------------------------------

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

        # Find current status for selected player
        current_status = ""
        for record in attendance:
            if str(record["player_id"]) == str(selected_player_id) and str(record["game_id"]) == str(game["game_id"]):
                current_status = str(record["status"]).strip()
                if current_status == "None":
                    current_status = ""
                break

        # --------------------------------------------------
        # GAME CARD
        # --------------------------------------------------

        with st.container():
            st.markdown('<div class="game-card">', unsafe_allow_html=True)
            st.markdown(f"### 📅 {format_date(game.get('date', ''))}")
            st.markdown(f"**⏰ {game.get('time', '')}**")
            st.markdown(f"**📍 {game.get('field', '')}**")
            st.markdown(f"**Opponent:** {game.get('opponent', '')}")
            st.markdown('</div>', unsafe_allow_html=True)

        # --------------------------------------------------
        # PLAYER VIEW
        # --------------------------------------------------

        if view_mode == "My Availability":

            if current_status == "Yes":
                st.success("Current Response: Yes")
            elif current_status == "No":
                st.error("Current Response: No")
            elif current_status == "Maybe":
                st.warning("Current Response: Maybe")
            else:
                st.info("Current Response: No Response")

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
        # CAPTAIN VIEW — 4 COLUMNS
        # --------------------------------------------------

        else:
            yes_players = []
            no_players = []
            maybe_players = []
            none_players = []

            for player in team_players:
                player_status = ""
                for record in attendance:
                    if str(record["player_id"]) == str(player["player_id"]) and str(record["game_id"]) == str(game["game_id"]):
                        player_status = str(record["status"]).strip()
                        break

                if player_status == "None" or player_status == "":
                    player_status = "No Response"

                pdata = {
                    "name": player["player_name"],
                    "id": player["player_id"],
                    "status": player_status
                }

                if player_status == "Yes":
                    yes_players.append(pdata)
                elif player_status == "No":
                    no_players.append(pdata)
                elif player_status == "Maybe":
                    maybe_players.append(pdata)
                else:
                    none_players.append(pdata)

            # Column rendering
            st.markdown('<div class="captain-columns">', unsafe_allow_html=True)

            def render_column(title, color, players, css_class):
                st.markdown(f'<div class="{css_class}">', unsafe_allow_html=True)
                st.markdown(f'<div class="captain-card"><h3 style="color:{color};">{title} ({len(players)})</h3>', unsafe_allow_html=True)

                for p in players:
                    st.markdown('<div class="player-row">', unsafe_allow_html=True)
                    st.markdown(f'<div class="player-name">{p["name"]}</div>', unsafe_allow_html=True)

                    cols = st.columns(4)
                    status_map = {
                        "Yes": "status-yes",
                        "No": "status-no",
                        "Maybe": "status-maybe",
                        "No Response": "status-none"
                    }

                    for i, status in enumerate(status_map.keys()):
                        with cols[i]:
                            st.markdown(f"<div class='{status_map[status]}'>", unsafe_allow_html=True)
                            if st.button(
                                status,
                                key=f"{title}_{game['game_id']}_{p['id']}_{status}"
                            ):
                                save_attendance(attendance_sheet, p["id"], game["game_id"], status)
                                st.success(f"{p['name']} set to {status}.")
                                st.rerun()
                            st.markdown("</div>", unsafe_allow_html=True)

                    st.markdown('</div>', unsafe_allow_html=True)

                st.markdown('</div></div>', unsafe_allow_html=True)

            render_column("YES", "green", yes_players, "column-yes")
            render_column("NO", "red", no_players, "column-no")
            render_column("MAYBE", "orange", maybe_players, "column-maybe")
            render_column("No Response", "gray", none_players, "column-none")

            st.markdown('</div>', unsafe_allow_html=True)

except Exception as e:
    st.error(f"Games error: {e}")
