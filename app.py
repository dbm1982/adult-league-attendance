import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# --------------------------------------------------
# PAGE CONFIG (keep wide for mobile)
# --------------------------------------------------

st.set_page_config(
    page_title="South Shore Adult Soccer League Portal",
    page_icon="⚽",
    layout="wide"
)

# --------------------------------------------------
# MOBILE-FRIENDLY CSS (modern cards + buttons)
# --------------------------------------------------

st.markdown("""
<style>
/* Slightly larger base font */
html, body, [class*="css"] {
    font-size: 17px;
}

/* Game and captain cards */
.game-card, .captain-card {
    padding: 1rem;
    border-radius: 12px;
    background-color: #ffffff;
    margin-bottom: 1.25rem;
    border: 1px solid #e0e0e0;
    box-shadow: 0px 2px 6px rgba(0,0,0,0.06);
}

/* Card titles */
.game-card h3, .captain-card h3 {
    margin-top: 0;
    margin-bottom: 8px;
}

/* Card text spacing */
.game-card p, .captain-card p {
    margin: 4px 0;
    font-size: 16px;
}

/* Full-width buttons (general) */
.stButton>button {
    padding: 0.5rem 0.8rem;
    font-size: 15px;
    border-radius: 8px;
}

/* Inline status buttons container */
.player-row {
    display: flex;
    flex-direction: column;
    gap: 4px;
    margin-bottom: 6px;
}

/* Player name */
.player-name {
    font-weight: 600;
    margin-bottom: 2px;
}

/* Inline buttons row */
.player-buttons {
    display: flex;
    flex-wrap: wrap;
    gap: 4px;
}

/* Make Save Response button full width */
.save-response-btn > button {
    width: 100%;
    padding: 0.7rem 1rem;
    font-size: 17px;
    border-radius: 10px;
}

/* Radio buttons spacing */
.stRadio > div {
    gap: 0.4rem;
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
# PLAYERS
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
        # GAME CARD (clean, mobile-friendly)
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

            if st.container():
                if st.button("💾 Save Response", key=f"save_{game['game_id']}", type="primary"):
                    save_attendance(attendance_sheet, selected_player_id, game["game_id"], selected_status)
                    st.success("Attendance saved successfully.")
                    st.rerun()

        # --------------------------------------------------
        # CAPTAIN VIEW (modern cards + inline buttons)
        # --------------------------------------------------

        else:
            yes_players = []
            no_players = []
            maybe_players = []
            no_response_players = []

            for player in team_players:
                player_status = ""
                for record in attendance:
                    if str(record["player_id"]) == str(player["player_id"]) and str(record["game_id"]) == str(game["game_id"]):
                        player_status = str(record["status"]).strip()
                        break

                if player_status == "None":
                    player_status = ""

                player_data = {
                    "name": player["player_name"],
                    "id": player["player_id"],
                    "status": player_status if player_status else "No Response"
                }

                if player_data["status"] == "Yes":
                    yes_players.append(player_data)
                elif player_data["status"] == "No":
                    no_players.append(player_data)
                elif player_data["status"] == "Maybe":
                    maybe_players.append(player_data)
                else:
                    no_response_players.append(player_data)

            def show_group(title, color, group):
                with st.container():
                    st.markdown('<div class="captain-card">', unsafe_allow_html=True)
                    st.markdown(
                        f"### <span style='color:{color};'>{title} ({len(group)})</span>",
                        unsafe_allow_html=True
                    )

                    for player in group:
                        st.markdown(
                            f"<div class='player-row'>"
                            f"<div class='player-name'>{player['name']}</div>",
                            unsafe_allow_html=True
                        )

                        # Inline buttons row
                        btn_col = st.container()
                        with btn_col:
                            cols = st.columns(4)
                            statuses = ["Yes", "No", "Maybe", "No Response"]
                            for i, status in enumerate(statuses):
                                if cols[i].button(
                                    status,
                                    key=f"{title}_{game['game_id']}_{player['id']}_{status}"
                                ):
                                    save_attendance(
                                        attendance_sheet,
                                        player["id"],
                                        game["game_id"],
                                        status
                                    )
                                    st.success(f"{player['name']} set to {status}.")
                                    st.rerun()

                        st.markdown("</div>", unsafe_allow_html=True)

                    st.markdown('</div>', unsafe_allow_html=True)

            show_group("YES", "green", yes_players)
            show_group("NO", "red", no_players)
            show_group("MAYBE", "orange", maybe_players)
            show_group("No Response", "gray", no_response_players)

except Exception as e:
    st.error(f"Games error: {e}")
