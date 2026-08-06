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
# CSS — COMPRESSION + FIXED HEADER + FIXED OVERLAP
# --------------------------------------------------

st.markdown("""
<style>

/* --------------------------------------------------
   RESTORE NORMAL READABLE HEADER SPACING
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
   GLOBAL STREAMLIT SPACING REDUCTION (Captain View Only)
-------------------------------------------------- */

.css-1kyxreq, .css-1r6slb0, .css-12w0qpk {
    padding: 0 !important;
    margin: 0 !important;
    gap: 2px !important;
}

div[data-testid="column"] {
    padding: 0 !important;
    margin: 0 !important;
    min-width: 0 !important;
}

div[data-testid="stVerticalBlock"] {
    padding: 0 !important;
    margin: 0 !important;
    gap: 2px !important;
}

.block-container {
    padding-bottom: 0 !important;
    margin: 0 !important;
}

/* --------------------------------------------------
   BUTTON COMPRESSION (B)
-------------------------------------------------- */

div.stButton > button {
    padding: 1px 3px !important;
    font-size: 10px !important;
    border-radius: 3px !important;
    height: 18px !important;
    line-height: 14px !important;
    margin: 0 !important;
}

/* Color-coded buttons */
.btn-yes > button { background-color: #4CAF50 !important; color: white !important; }
.btn-no > button { background-color: #F44336 !important; color: white !important; }
.btn-maybe > button { background-color: #FFB300 !important; color: black !important; }
.btn-none > button { background-color: #E0E0E0 !important; color: #555 !important; }

/* --------------------------------------------------
   PLAYER ROW COMPRESSION + NAME PROTECTION (N2)
-------------------------------------------------- */

.player-row {
    margin: 0 !important;
    padding: 2px 0 !important;
    display: flex !important;
    align-items: center !important;
}

.player-name {
    font-size: 12px !important;
    margin: 0 4px 0 0 !important;
    padding: 0 !important;
    min-width: 140px !important;  /* N2 */
    display: inline-block !important;
    white-space: nowrap !important;
}

/* --------------------------------------------------
   CAPTAIN COLUMN COMPRESSION + PADDING (P2)
-------------------------------------------------- */

.captain-column {
    padding: 6px 8px !important;  /* P2 */
    margin: 0 0 4px 0 !important;
    background-color: #ffffff;
    border: 1px solid #c8c8c8;
    border-radius: 6px;
}

.captain-title {
    font-size: 14px !important;
    margin: 0 0 3px 0 !important;
    padding: 0 !important;
    font-weight: 600;
}

/* --------------------------------------------------
   INNER WRAPPER COMPRESSION (T2)
-------------------------------------------------- */

div[data-testid="stHorizontalBlock"] {
    padding: 0 !important;
    margin: 0 !important;
    gap: 2px !important;
    flex-wrap: nowrap !important;
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
    padding: 10px 14px;
    border-radius: 10px;
    margin: 0 0 10px 0 !important;
    border-left: 6px solid #2e7d32;
    color: #1b5e20;
}

/* --------------------------------------------------
   MOBILE STACKING + MOBILE COMPRESSION
-------------------------------------------------- */

@media (max-width: 600px) {

    .captain-column {
        width: 100% !important;
        display: block !important;
        margin-bottom: 6px !important;
    }

    .css-1kyxreq, .css-1r6slb0, .css-12w0qpk {
        flex-direction: column !important;
        width: 100% !important;
        gap: 1px !important;
    }

    div.stButton > button {
        width: 100% !important;
        margin-bottom: 2px !important;
    }

    .player-row {
        flex-direction: column !important;
        align-items: flex-start !important;
    }

    .player-name {
        margin-bottom: 2px !important;
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

            # Weighted widths (W3)
            col_yes, col_no, col_maybe, col_none = st.columns([1, 1, 1, 2])

            def render_column(col, title, color, players_list):
                with col:
                    st.markdown('<div class="captain-column">', unsafe_allow_html=True)
                    st.markdown(
                        f'<div class="captain-title" style="color:{color};">{title} ({len(players_list)})</div>',
                        unsafe_allow_html=True
                    )

                    for p in players_list:
                        st.markdown('<div class="player-row">', unsafe_allow_html=True)
                        st.markdown(f'<div class="player-name">{p["name"]}</div>', unsafe_allow_html=True)

                        b_yes, b_no, b_maybe, b_none = st.columns([1, 1, 1, 1])

                        with b_yes:
                            st.markdown('<div class="btn-yes">', unsafe_allow_html=True)
                            if st.button("Yes", key=f"{title}_yes_{game['game_id']}_{p['id']}"):
                                save_attendance(attendance_sheet, p["id"], game["game_id"], "Yes")
                                st.rerun()
                            st.markdown('</div>', unsafe_allow_html=True)

                        with b_no:
                            st.markdown('<div class="btn-no">', unsafe_allow_html=True)
                            if st.button("No", key=f"{title}_no_{game['game_id']}_{p['id']}"):
                                save_attendance(attendance_sheet, p["id"], game["game_id"], "No")
                                st.rerun()
                            st.markdown('</div>', unsafe_allow_html=True)

                        with b_maybe:
                            st.markdown('<div class="btn-maybe">', unsafe_allow_html=True)
                            if st.button("Maybe", key=f"{title}_maybe_{game['game_id']}_{p['id']}"):
                                save_attendance(attendance_sheet, p["id"], game["game_id"], "Maybe")
                                st.rerun()
                            st.markdown('</div>', unsafe_allow_html=True)

                        with b_none:
                            st.markdown('<div class="btn-none">', unsafe_allow_html=True)
                            if st.button("No Resp", key=f"{title}_none_{game['game_id']}_{p['id']}"):
                                save_attendance(attendance_sheet, p["id"], game["game_id"], "No Response")
                                st.rerun()
                            st.markdown('</div>', unsafe_allow_html=True)

                        st.markdown('</div>', unsafe_allow_html=True)

                    st.markdown('</div>', unsafe_allow_html=True)

            render_column(col_yes, "YES", "green", yes_players)
            render_column(col_no, "NO", "red", no_players)
            render_column(col_maybe, "MAYBE", "orange", maybe_players)
            render_column(col_none, "No Response", "gray", none_players)

except Exception as e:
    st.error(f"Games error: {e}")
