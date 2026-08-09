import streamlit as st

def inject_css():
    st.markdown("""
        <style>

        /* Card container */
        .game-card {
            background-color: #ffffff;
            padding: 18px 22px;
            border-radius: 10px;
            margin-bottom: 18px;
            border: 1px solid #e0e0e0;
        }

        /* Opponent badge */
        .opp-badge {
            display: inline-block;
            padding: 4px 10px;
            border-radius: 6px;
            font-weight: 600;
            color: white;
            margin-right: 10px;
        }

        /* Field badge */
        .field-badge {
            background-color: #444;
            color: white;
            padding: 4px 10px;
            border-radius: 6px;
            margin-left: 10px;
            font-size: 13px;
        }

        /* Time badge */
        .time-badge {
            background-color: #777;
            color: white;
            padding: 4px 10px;
            border-radius: 6px;
            margin-left: 10px;
            font-size: 13px;
        }

        /* Section headers */
        .section-header {
            font-size: 20px;
            font-weight: 700;
            margin-top: 20px;
            margin-bottom: 10px;
        }

        </style>
    """, unsafe_allow_html=True)
