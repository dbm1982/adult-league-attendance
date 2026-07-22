import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# --------------------------------------------------
# PAGE CONFIG
# --------------------------------------------------

st.set_page_config(
    page_title="South Shore Adult Soccer League Attendance",
    page_icon="⚽",
    layout="wide"
)

# --------------------------------------------------
# HELPERS
# --------------------------------------------------

def format_date(date_str):

    try:

        dt = datetime.strptime(
            str(date_str),
            "%Y-%m-%d"
        )

        day = dt.day

        if 4 <= day <= 20 or 24 <= day <= 30:
            suffix = "th"
        else:
            suffix = ["st", "nd", "rd"][
                min(day % 10 - 1, 2)
            ]

        return dt.strftime(
            f"%B {day}{suffix}, %Y"
        )

    except:
        return str(date_str)


def save_attendance(
    attendance_sheet,
    player_id,
    game_id,
    status
):

    values = attendance_sheet.get_all_values()

    header = values[0]

    player_col = header.index("player_id")
    game_col = header.index("game_id")
    status_col = header.index("status")
    updated_col = header.index("updated_at")

    spreadsheet_status = (
        "None"
        if status == "No Response"
        else status
    )

    timestamp = datetime.now().strftime(
        "%m/%d/%Y %H:%M:%S"
    )

    for row_num in range(1, len(values)):

        if (
            str(values[row_num][player_col])
            == str(player_id)
            and
            str(values[row_num][game_col])
            == str(game_id)
        ):

            attendance_sheet.update_cell(
                row_num + 1,
                status_col + 1,
                spreadsheet_status
            )

            attendance_sheet.update_cell(
                row_num + 1,
                updated_col + 1,
                timestamp
            )

            return "updated"

    attendance_sheet.append_row([
        player_id,
        game_id,
        spreadsheet_status,
        timestamp
    ])

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

# --------------------------------------------------
# DEV SPREADSHEET
# --------------------------------------------------

spreadsheet = client.open_by_key(
    "1afoSDWnUlB6ZN5Wlz4CDyX1whhzNNHxm6vCINs-2LDM"
)

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

st.title("⚽ South Shore Adult Soccer League Attendance")

st.caption(
    "Select your team and your name to view upcoming games and attendance."
)

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

team_players = [
    p for p in players
    if str(p["team_id"]).strip()
    == str(selected_team).strip()
]

player_names = [
    p["player_name"]
    for p in team_players
]

selected_player = st.selectbox(
    "👤 Select Your Name",
    player_names,
    index=None,
    placeholder="Choose your name..."
)

if not selected_player:
    st.stop()

selected_player_record = next(
    p for p in team_players
    if p["player_name"] == selected_player
)

selected_player_id = selected_player_record["player_id"]

is_captain = str(
    selected_player_record.get(
        "is_captain",
        ""
    )
).upper() == "TRUE"

# --------------------------------------------------
# HEADER
# --------------------------------------------------

st.markdown("---")

col1, col2 = st.columns(2)

with col1:
    st.markdown(f"## ⚽ {selected_team}")

with col2:
    st.markdown(f"## 👤 {selected_player}")

# --------------------------------------------------
# CAPTAIN OPTIONS
# --------------------------------------------------

if is_captain:

    view_mode = st.radio(
        "Captain Options",
        [
            "My Availability",
            "Team Availability"
        ],
        horizontal=True
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
        if str(g.get("team_id", "")).strip()
        == str(selected_team).strip()
    ]

    today = datetime.now().date()

    team_games = [
        g for g in team_games
        if datetime.strptime(
            str(g["date"]),
            "%Y-%m-%d"
        ).date() >= today
    ]
    
    team_games = sorted(
        team_games,
        key=lambda x: x["date"]
    )

    if not team_games:

        st.warning("No games found.")
        st.stop()

    for game in team_games:

        current_status = ""

        for record in attendance:

            if (
                str(record["player_id"])
                == str(selected_player_id)
                and
                str(record["game_id"])
                == str(game["game_id"])
            ):
                current_status = str(
                    record["status"]
                ).strip()

                if current_status == "None":
                    current_status = ""

                break

        with st.container(border=True):

            st.markdown(
                f"## 📅 {format_date(game.get('date', ''))}"
            )

            col1, col2 = st.columns(2)

            with col1:
                st.markdown(
                    f"### ⏰ {game.get('time', '')}"
                )

            with col2:
                st.markdown(
                    f"### 📍 {game.get('field', '')}"
                )

            st.markdown(
                f"**Opponent:** {game.get('opponent', '')}"
            )

            st.markdown("---")

            if view_mode == "My Availability":

                if current_status == "Yes":

                    st.success(
                        "Current Response: Yes"
                    )

                elif current_status == "No":

                    st.error(
                        "Current Response: No"
                    )

                elif current_status == "Maybe":

                    st.warning(
                        "Current Response: Maybe"
                    )

                else:

                    st.info(
                        "Current Response: No Response"
                    )

                options = [
                    "No Response",
                    "Yes",
                    "No",
                    "Maybe"
                ]

                if current_status in [
                    "Yes",
                    "No",
                    "Maybe"
                ]:

                    default_index = options.index(
                        current_status
                    )

                else:

                    default_index = 0

                selected_status = st.radio(
                    "Update Availability",
                    options,
                    index=default_index,
                    horizontal=True,
                    key=f"attendance_{game['game_id']}"
                )

                if st.button(
                    "💾 Save Response",
                    key=f"save_{game['game_id']}"
                ):

                    result = save_attendance(
                        attendance_sheet,
                        selected_player_id,
                        game["game_id"],
                        selected_status
                    )

                    st.success(
                        "Attendance saved successfully."
                    )

                    st.rerun()

            else:
            
                yes_players = []
                no_players = []
                maybe_players = []
                no_response_players = []
            
                for player in team_players:
            
                    player_status = ""
            
                    for record in attendance:
            
                        if (
                            str(record["player_id"])
                            ==
                            str(player["player_id"])
                            and
                            str(record["game_id"])
                            ==
                            str(game["game_id"])
                        ):
                            player_status = str(
                                record["status"]
                            ).strip()
                            break
            
                    if player_status == "None":
                        player_status = ""
            
                    player_data = {
                        "name": player["player_name"],
                        "id": player["player_id"]
                    }
            
                    if player_status == "Yes":
            
                        yes_players.append(player_data)
            
                    elif player_status == "No":
            
                        no_players.append(player_data)
            
                    elif player_status == "Maybe":
            
                        maybe_players.append(player_data)
            
                    else:
            
                        no_response_players.append(player_data)
            
                col1, col2, col3, col4 = st.columns(4)
            
                with col1:
            
                    st.success(f"YES ({len(yes_players)})")
            
                    for player in yes_players:
            
                        c1, c2 = st.columns([5, 1])
            
                        with c1:
                            st.write(player["name"])
            
                        with c2:
            
                            if st.button(
                                "✏️",
                                key=f"yes_{game['game_id']}_{player['id']}"
                            ):
                                st.session_state[
                                    f"edit_player_{game['game_id']}"
                                ] = player
            
                with col2:
            
                    st.error(f"NO ({len(no_players)})")
            
                    for player in no_players:
            
                        c1, c2 = st.columns([5, 1])
            
                        with c1:
                            st.write(player["name"])
            
                        with c2:
            
                            if st.button(
                                "✏️",
                                key=f"no_{game['game_id']}_{player['id']}"
                            ):
                                st.session_state[
                                    f"edit_player_{game['game_id']}"
                                ] = player
            
                with col3:
            
                    st.warning(f"MAYBE ({len(maybe_players)})")
            
                    for player in maybe_players:
            
                        c1, c2 = st.columns([5, 1])
            
                        with c1:
                            st.write(player["name"])
            
                        with c2:
            
                            if st.button(
                                "✏️",
                                key=f"maybe_{game['game_id']}_{player['id']}"
                            ):
                                st.session_state[
                                    f"edit_player_{game['game_id']}"
                                ] = player
            
                with col4:
            
                    st.info(
                        f"No Response ({len(no_response_players)})"
                    )
            
                    for player in no_response_players:
            
                        c1, c2 = st.columns([5, 1])
            
                        with c1:
                            st.write(player["name"])
            
                        with c2:
            
                            if st.button(
                                "✏️",
                                key=f"pending_{game['game_id']}_{player['id']}"
                            ):
                                st.session_state[
                                    f"edit_player_{game['game_id']}"
                                ] = player
            
                edit_player = st.session_state.get(
                    f"edit_player_{game['game_id']}"
                )
            
                if edit_player:
            
                    st.markdown("---")
            
                    st.subheader(
                        f"Captain Override: {edit_player['name']}"
                    )
            
                    override_status = st.radio(
                        "Move Player To",
                        [
                            "Yes",
                            "No",
                            "Maybe",
                            "No Response"
                        ],
                        horizontal=True,
                        key=f"override_{game['game_id']}"
                    )
            
                    if st.button(
                        "💾 Save Captain Override",
                        key=f"save_override_{game['game_id']}"
                    ):
            
                        save_attendance(
                            attendance_sheet,
                            edit_player["id"],
                            game["game_id"],
                            override_status
                        )
            
                        st.success(
                            f"{edit_player['name']} updated."
                        )
            
                        del st.session_state[
                            f"edit_player_{game['game_id']}"
                        ]
            
                        st.rerun()
except Exception as e:

    st.error(
        f"Games error: {e}"
    )
