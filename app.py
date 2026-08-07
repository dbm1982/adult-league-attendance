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
# CSS — CLEAN, COLORED, NON‑OVERLAPPING CAPTAIN VIEW
# --------------------------------------------------

st.markdown("""
<style>

/* --------------------------------------------------
   READABLE HEADER SPACING
-------------------------------------------------- */

h1, .stMarkdown h1 {
    margin-top: 22px !important;
    margin-bottom: 14px !important;
}

.stCaption, .stMarkdown p {
    margin-bottom: 14px !important;
}

.block-container > div:first-child {
    margin-top: 18px !important;
}

div[data-testid="stSelectbox"] {
    margin-top: 10px !important;
    margin-bottom: 10px !important;
}

/* --------------------------------------------------
   GLOBAL SAFE SPACING (CV‑B)
-------------------------------------------------- */

.css-1kyxreq, .css-1r6slb0, .css-12w0qpk {
    padding: 0 !important;
    margin: 0 !important;
    gap: 6px !important;
}

div[data-testid="column"] {
    padding: 0 !important;
    margin: 0 !important;
}

/* --------------------------------------------------
   BUTTONS — SMALL, CLEAN (CV‑B)
-------------------------------------------------- */

div.stButton > button {
    padding: 3px 6px !important;
    font-size: 11px !important;
    border-radius: 4px !important;
    height: 22px !important;
    line-height: 16px !important;
    margin: 0 !important;
}

/* --------------------------------------------------
   PLAYER ROW — COMPACT, NO VERTICAL SPREAD
-------------------------------------------------- */

.player-row {
    padding: 2px 0 !important;
    gap: 3px !important;
    display: flex !important;
    align-items: center !important;
}

.player-name {
    font-size: 13px !important;
    min-width: 140px !important;
    white-space: nowrap !important;
}

/* --------------------------------------------------
   COLORED CAPTAIN BOXES (C1 + B1 + T2)
-------------------------------------------------- */

.captain-column {
    padding: 12px !important;
    border-radius: 10px !important;
    margin-bottom: 14px !important;
    color: black !important;
}

/* Section title inside colored box */
.captain-title {
    font-size: 16px !important;
    font-weight: 700 !important;
    margin-bottom: 10px !important;
}

/* Color themes */
.captain-yes   { background-color: #4CAF50 !important; }
.captain-no    { background-color: #F44336 !important; }
.captain-maybe { background-color: #FFEB3B !important; }
.captain-none  { background-color: #BDBDBD !important; }

/* --------------------------------------------------
   MINI SUMMARY BAR
-------------------------------------------------- */

.game-mini-summary {
    font-size: 12px !important;
    margin: 4px 0 10px 0 !important;
    display: flex;
    gap: 12px;
    flex-wrap: wrap;
}

.game-mini-summary span {
    font-weight: 600;
}

.summary-yes { color: #2e7d32 !important; }
.summary-no { color: #c62828 !important; }
.summary-maybe { color: #f9a825 !important; }
.summary-none { color: #616161 !important; }

/* --------------------------------------------------
   CAPTAIN ALERT BAR (NR LIST)
-------------------------------------------------- */

.captain-alert {
    background-color: #f5f5f5;
    border-left: 5px solid #616161;
    padding: 8px 12px;
    border-radius: 6px;
    margin: 6px 0 14px 0;
    font-size: 13px;
}

.captain-alert strong {
    font-weight: 700;
}

.captain-alert span {
    font-weight: 600;
    color: #424242;
}

/* --------------------------------------------------
   INNER WRAPPERS — SAFE WRAP (fix overlap)
-------------------------------------------------- */

div[data-testid="stHorizontalBlock"] {
    gap: 6px !important;
    flex-wrap: wrap !important;
}

/* --------------------------------------------------
   WEIGHTED COLUMN WIDTHS (W3)
-------------------------------------------------- */

.weight-yes   { flex: 1 !important; }
.weight-no    { flex: 1 !important; }
.weight-maybe { flex: 1 !important; }
.weight-none  { flex: 2 !important; }

/* --------------------------------------------------
   GAME CALLOUT
-------------------------------------------------- */

.game-callout {
    background: #e8f5e9;
    padding: 12px 16px;
    border-radius: 10px;
    margin-bottom: 12px !important;
    border-left: 6px solid #2e7d32;
    color: #1b5e20;
}

/* --------------------------------------------------
   MOBILE — STACK COLUMNS (M1)
-------------------------------------------------- */

@media (max-width: 600px) {

    .captain-column {
        width: 100% !important;
        margin-bottom: 14px !important;
    }

    .player-row {
        flex-direction: column !important;
        align-items: flex-start !important;
        gap: 4px !important;
    }

    .player-name {
        margin-bottom: 4px !important;
    }

    div.stButton > button {
        width: 100% !important;
        margin-bottom: 4px !important;
    }
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
            <div class="game-callout">
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

        yes_count = len(yes_players)
        no_count = len(no_players)
        maybe_count = len(maybe_players)
        none_count = len(none_players)

        st.markdown(
            f"""
            <div class="game-mini-summary">
                <span class="summary-yes">YES: {yes_count}</span>
                <span class="summary-no">NO: {no_count}</span>
                <span class="summary-maybe">MAYBE: {maybe_count}</span>
                <span class="summary-none">NR: {none_count}</span>
            </div>
            """,
            unsafe_allow_html=True
        )

        # --------------------------------------------------
        # CAPTAIN ALERT BAR (NR LIST) — CAPTAIN ONLY
        # --------------------------------------------------

        if is_captain and view_mode == "Team Availability" and none_count > 0:
            nr_names = ", ".join([short_name(p["player_name"]) for p in none_players])

            st.markdown(
                f"""
                <div class="captain-alert">
                    <strong>⚠️ {none_count} players have not responded:</strong>
                    <span>{nr_names}</span>
                </div>
                """,
                unsafe_allow_html=True
            )

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
        # CAPTAIN VIEW
        # --------------------------------------------------

        else:

            col_yes, col_no, col_maybe, col_none = st.columns([1, 1, 1, 2])

            def render_column(col, title, color_class, players_list):
                with col:
                    st.markdown(f'<div class="captain-column {color_class}">', unsafe_allow_html=True)
                    st.markdown(
                        f'<div class="captain-title">{title} ({len(players_list)})</div>',
                        unsafe_allow_html=True
                    )

                    for p in players_list:
                        st.markdown('<div class="player-row">', unsafe_allow_html=True)
                        st.markdown(f'<div class="player-name">{p["player_name"]}</div>', unsafe_allow_html=True)

                        b_yes, b_no, b_maybe, b_none = st.columns([1, 1, 1, 1])

                        with b_yes:
                            if st.button("Yes", key=f"{title}_yes_{game['game_id']}_{p['player_id']}"):
                                save_attendance(attendance_sheet, p["player_id"], game["game_id"], "Yes")
                                st.rerun()

                        with b_no:
                            if st.button("No", key=f"{title}_no_{game['game_id']}_{p['player_id']}"):
                                save_attendance(attendance_sheet, p["player_id"], game["game_id"], "No")
                                st.rerun()

                        with b_maybe:
                            if st.button("Maybe", key=f"{title}_maybe_{game['game_id']}_{p['player_id']}"):
                                save_attendance(attendance_sheet, p["player_id"], game["game_id"], "Maybe")
                                st.rerun()

                        with b_none:
                            if st.button("No Resp", key=f"{title}_none_{game['game_id']}_{p['player_id']}"):
                                save_attendance(attendance_sheet, p["player_id"], game["game_id"], "No Response")
                                st.rerun()

                        st.markdown('</div>', unsafe_allow_html=True)

                    st.markdown('</div>', unsafe_allow_html=True)

            render_column(col_yes, "YES", "captain-yes", yes_players)
            render_column(col_no, "NO", "captain-no", no_players)
            render_column(col_maybe, "MAYBE", "captain-maybe", maybe_players)
            render_column(col_none, "No Response", "captain-none", none_players)

except Exception as e:
    st.error(f"Games error: {e}")
