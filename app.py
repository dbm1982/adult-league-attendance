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
# CSS — COMPACT INLINE ROWS
# --------------------------------------------------

st.markdown("""
<style>

.player-name {
    font-size: 14px;
    font-weight: 500;
    padding-top: 6px;
}

.segmented {
    display: flex;
    gap: 6px;
}

.segmented button {
    font-size: 16px !important;
    padding: 2px 6px !important;
    border-radius: 6px !important;
    min-width: 40px !important;
    text-align: center !important;
    background: white;
    border: 1px solid #999;
}

.segmented .selected {
    border: 2px solid black !important;
}

.column-header {
    padding: 8px 12px;
    border-radius: 8px;
    font-weight: 700;
    font-size: 16px;
    margin-bottom: 10px;
    color: black;
}

.header-yes { background-color: #4CAF50; }
.header-no { background-color: #F44336; }
.header-maybe { background-color: #FFEB3B; }
.header-nr { background-color: #BDBDBD; }

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
        current_status = ""
        for record in attendance:
            if str(record["player_id"]) == str(selected_player_id) and str(record["game_id"]) == str(game["game_id"]):
                current_status = str(record["status"]).strip()
                if current_status == "None":
                    current_status = ""
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
            player_status = ""
            for record in attendance:
                if str(record["player_id"]) == str(player["player_id"]) and str(record["game_id"]) == str(game["game_id"]):
                    player_status = str(record["status"]).strip()
                    break

            if player_status == "None" or player_status == "":
                player_status = "No Response"

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
        # CAPTAIN VIEW
        # --------------------------------------------------

        else:

            def render_column(title, color_class, players_list):
                st.markdown(
                    f'<div class="column-header {color_class}">{title} ({len(players_list)})</div>',
                    unsafe_allow_html=True
                )

                for p in players_list:

                    # Determine current status
                    if title == "YES":
                        current = "Yes"
                    elif title == "NO":
                        current = "No"
                    elif title == "MAYBE":
                        current = "Maybe"
                    else:
                        current = "No Response"

                    # ONE-LINE ROW USING 2 COLUMNS
                    name_col, seg_col = st.columns([2, 3])

                    with name_col:
                        st.markdown(f'<div class="player-name">{p["player_name"]}</div>', unsafe_allow_html=True)

                    with seg_col:
                        st.markdown('<div class="segmented">', unsafe_allow_html=True)

                        def seg_button(label, emoji, status_value):
                            selected = (current == status_value)
                            css = "selected" if selected else ""
                            if st.button(f"{emoji} {label}", key=f"{p['player_id']}_{game['game_id']}_{label}"):
                                save_attendance(attendance_sheet, p["player_id"], game["game_id"], status_value)
                                st.rerun()

                        seg_button("Y", "🟩", "Yes")
                        seg_button("N", "🟥", "No")
                        seg_button("M", "🟨", "Maybe")
                        seg_button("?", "🟦", "No Response")

                        st.markdown('</div>', unsafe_allow_html=True)

            col_yes, col_no, col_maybe, col_none = st.columns(4)

            with col_yes:
                render_column("YES", "header-yes", yes_players)

            with col_no:
                render_column("NO", "header-no", no_players)

            with col_maybe:
                render_column("MAYBE", "header-maybe", maybe_players)

            with col_none:
                render_column("NR", "header-nr", none_players)

except Exception as e:
    st.error(f"Games error: {e}")
