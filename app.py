import streamlit as st
from attendance_logic import (
    load_players_df,
    load_games_df,
    load_attendance_df,
    load_teams_df,
    commit_attendance_changes,
)
from player_view import player_view
from captain_view import captain_view

st.set_page_config(page_title="South Shore Coed Adult Soccer League Portal", layout="wide")

# Global app CSS: mobile-friendly, still clean on desktop
st.markdown(
    """
    <style>
    /* Center content with a max width for desktop, full width on mobile */
    .main > div {
        max-width: 900px;
        margin: 0 auto;
        padding-top: 8px;
    }

    /* Reduce default Streamlit padding */
    .block-container {
        padding-top: 0.5rem;
        padding-bottom: 2rem;
    }

    /* Make selectboxes and buttons feel more app-like */
    .stSelectbox, .stButton button {
        border-radius: 8px !important;
        min-height: 40px;
    }

    .stButton button {
        width: 100%;
    }

    /* Tabs: tighter, more app-like */
    .stTabs [role="tablist"] {
        justify-content: center;
    }

    .stTabs [role="tab"] {
        padding: 6px 14px;
        border-radius: 999px;
        margin: 0 4px;
        font-size: 14px;
    }

    /* Mobile tweaks */
    @media (max-width: 600px) {
        .main > div {
            max-width: 100%;
            padding-left: 8px;
            padding-right: 8px;
        }

        .stTabs [role="tab"] {
            font-size: 13px;
            padding: 6px 10px;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Cache sheets (single load per session, no repeated pulls)
if "players_df" not in st.session_state:
    st.session_state.players_df = load_players_df()

if "games_df" not in st.session_state:
    st.session_state.games_df = load_games_df()

if "attendance_df" not in st.session_state:
    st.session_state.attendance_df = load_attendance_df()

if "teams_df" not in st.session_state:
    st.session_state.teams_df = load_teams_df()

if "pending_updates" not in st.session_state:
    st.session_state.pending_updates = {}

# Persistent selection
if "selected_team" not in st.session_state:
    st.session_state.selected_team = None

if "selected_player_id" not in st.session_state:
    st.session_state.selected_player_id = None

players_df = st.session_state.players_df
games_df = st.session_state.games_df
attendance_df = st.session_state.attendance_df
teams_df = st.session_state.teams_df

# App header bar
st.markdown(
    """
    <div style="
        padding: 12px 18px;
        background-color: #1a73e8;
        border-radius: 8px;
        margin-bottom: 14px;
    ">
        <h2 style="
            color: white;
            margin: 0;
            font-weight: 600;
            font-size: 22px;
        ">
            South Shore Coed Adult Soccer League Portal
        </h2>
    </div>
    """,
    unsafe_allow_html=True
)

active_team_ids = sorted(
    teams_df[teams_df["active"] == True]["team_id"].unique()
)

# Selectors (mobile-friendly, still fine on desktop)
if st.session_state.selected_team is None or st.session_state.selected_player_id is None:

    selector_container = st.container()

    with selector_container:

        st.markdown("#### Select your team and player")

        team_id = st.selectbox(
            "Team",
            active_team_ids,
            index=None,
            placeholder="Select a team",
        )

        if team_id:
            st.session_state.selected_team = team_id

            team_players = players_df[
                (players_df["team_id"] == team_id)
                & (players_df["team_id"] != "")
                & (~players_df["team_id"].str.contains("Inactive"))
                & (~players_df["team_id"].str.contains("Floaters"))
            ]

            player_name_to_id = {
                row["player_name"]: row["player_id"]
                for _, row in team_players.iterrows()
            }

            player_name = st.selectbox(
                "Player",
                list(player_name_to_id.keys()),
                index=None,
                placeholder="Select a player",
            )

            if player_name:
                st.session_state.selected_player_id = player_name_to_id[player_name]
                selector_container.empty()
                st.rerun()

# Badge
if st.session_state.selected_team and st.session_state.selected_player_id:

    player_row = players_df[
        players_df["player_id"] == st.session_state.selected_player_id
    ].iloc[0]

    player_name = player_row["player_name"]

    badge_col1, badge_col2 = st.columns([0.8, 0.2])

    with badge_col1:
        st.markdown(
            f"""
            <div style="
                background-color:#eef2f7;
                padding:10px 14px;
                border-radius:8px;
                margin-bottom:12px;
                font-size:15px;
                font-weight:600;
            ">
                Selected:
                <span style="color:#2c3e50;">Team {st.session_state.selected_team}</span> •
                <span style="color:#2c3e50;">{player_name}</span>
            </div>
            """,
            unsafe_allow_html=True
        )

    with badge_col2:
        if st.button("Change"):
            st.session_state.selected_team = None
            st.session_state.selected_player_id = None
            st.rerun()

# Stop if still missing selection
if st.session_state.selected_team is None or st.session_state.selected_player_id is None:
    st.stop()

# Load player row safely
player_row = players_df[
    players_df["player_id"] == st.session_state.selected_player_id
]

if player_row.empty:
    st.error("Player not found in Players sheet.")
    st.stop()

player_row = player_row.iloc[0]
player_id = player_row["player_id"]
is_captain = bool(player_row["is_captain"])

# Views: tabs already behave well on mobile, we just styled them
if is_captain:
    tab_player, tab_captain = st.tabs(["Player View", "Captain View"])
else:
    tab_player = st.tabs(["Player View"])[0]

with tab_player:
    player_view(
        players_df=players_df,
        games_df=games_df,
        attendance_df=st.session_state.attendance_df,
        player_id=player_id,
        commit_changes=commit_attendance_changes,
    )

if is_captain:
    with tab_captain:
        captain_view(
            players_df=players_df,
            games_df=games_df,
            attendance_df=st.session_state.attendance_df,
            team_id=st.session_state.selected_team,
            commit_changes=commit_attendance_changes,
        )
