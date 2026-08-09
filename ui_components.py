# ui_components.py

import streamlit as st
from styles import SEGMENTED_CONTROL_CSS

def segmented_control(player_id, current_status):
    st.markdown(SEGMENTED_CONTROL_CSS, unsafe_allow_html=True)

    statuses = ["Y", "N", "M", "NR"]
    labels = {"Y": "Yes", "N": "No", "M": "Maybe", "NR": "NR"}

    selected = st.session_state.get(f"status_{player_id}", current_status)

    st.markdown('<div class="segmented-control">', unsafe_allow_html=True)
    cols = st.columns(len(statuses))

    for i, status in enumerate(statuses):
        active = "active" if selected == status else ""

        if cols[i].button(status, key=f"{player_id}_{status}"):
            st.session_state[f"status_{player_id}"] = status
            selected = status

        cols[i].markdown(
            f'<button class="{active}" data-value="{status}">{status}</button>',
            unsafe_allow_html=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)

    return labels[selected]
