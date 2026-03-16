import pandas as pd
import streamlit as st
import random

# -----------------------------
# Google Sheet URL (public)
# -----------------------------
GOOGLE_SHEET_URL = "https://docs.google.com/spreadsheets/d/1w2MY5EMTdaPKpaBymqvrlekc22IOqbzSb9GbUNtHLGk/edit?gid=1634970899#gid=1634970899"
MIN_PLAYERS = 10
APP_TITLE = "⚽ Team Balancer"

# -----------------------------
# Read players from Google Sheet
# -----------------------------
def read_players_from_google_sheet(sheet_url):
    sheet_url = sheet_url.replace("/edit?", "/gviz/tq?tqx=out:csv&")
    try:
        df = pd.read_csv(sheet_url)
        players = []
        for _, row in df.iterrows():
            name = str(row.iloc[0]).strip()
            rating = float(row.iloc[2])
            players.append({"name": name, "rating": rating})
        return players
    except Exception as e:
        st.error(f"Error reading Google Sheet: {e}")
        return []

# -----------------------------
# Team balancing
# -----------------------------
def balance_teams(active_players, gk1, gk2):
    if len(active_players) < 4:
        return None, None

    field_players = [p for p in active_players if p["name"] not in [gk1, gk2]]
    team_size = len(active_players) // 2 - 1

    best_diff = float('inf')
    best_t1, best_t2 = None, None

    for _ in range(10000):
        random.shuffle(field_players)
        t1 = [p for p in active_players if p["name"] == gk1] + field_players[:team_size]
        t2 = [p for p in active_players if p["name"] == gk2] + field_players[team_size:]
        diff = abs(sum(p['rating'] for p in t1) - sum(p['rating'] for p in t2))
        if diff < best_diff:
            best_diff = diff
            best_t1, best_t2 = t1[:], t2[:]

    return best_t1, best_t2

# -----------------------------
# Utility
# -----------------------------
def calculate_total(team, player_dict):
    return sum(player_dict[n]['rating'] for n in team)

# -----------------------------
# Main App
# -----------------------------
def main():
    st.set_page_config(page_title=APP_TITLE)
    st.title(APP_TITLE)
    st.write("Reading player data from Termin google sheet")

    # -----------------------------
    # Initialize session state
    # -----------------------------
    if "move_requests" not in st.session_state:
        st.session_state.move_requests = []
    if "team_crni" not in st.session_state:
        st.session_state.team_crni = []
    if "team_bijeli" not in st.session_state:
        st.session_state.team_bijeli = []

    # -----------------------------
    # Read players from Google Sheet
    # -----------------------------
    if "players" not in st.session_state:
        # load players only ONCE
        st.session_state.players = read_players_from_google_sheet(GOOGLE_SHEET_URL)
    
    # reference for convenience
    players = st.session_state.players

    # Ensure all_players includes Google Sheet names
    if "all_players" not in st.session_state:
        st.session_state.all_players = []
        for p in players:
            if p['name'] not in st.session_state.all_players:
                st.session_state.all_players.append(p['name'])

    if "player_dict" not in st.session_state:
        st.session_state.player_dict = {p['name']: p for p in players}
    
    submitted_new_player = False

    # -----------------------------
    # Step 0: Add a new player manually
    # -----------------------------
    st.subheader("Add a new player (optional)")
    with st.form("add_player_form", clear_on_submit=True):
        new_name = st.text_input("Player Name")
        new_rating = st.number_input("Rating", min_value=0.0, max_value=100.0, value=50.0, step=1.0)
        submitted = st.form_submit_button("Add Player")
        if submitted:
            if not new_name.strip():
                st.warning("Please enter a valid name.")
            elif new_name.strip() in st.session_state.all_players:
                st.warning("This player already exists.")
            else:
                # Add to session state and players list
                st.session_state.all_players.append(new_name.strip())
                st.session_state.players.append({"name": new_name.strip(), "rating": float(new_rating)})
                st.session_state.player_dict[new_name.strip()] = {"name": new_name.strip(), "rating": float(new_rating)}
                st.success(f"Added player {new_name.strip()} ({new_rating:.2f})")
                submitted_new_player = True

    # -----------------------------
    # Step 1: Select active players and goalkeepers
    # -----------------------------
    st.subheader("Step 1 & 2: Select active players and goalkeepers")

    for p_name in st.session_state.all_players:
        if f"cb_play_{p_name}" not in st.session_state:
            st.session_state[f"cb_play_{p_name}"] = False
        if f"cb_gk_{p_name}" not in st.session_state:
            st.session_state[f"cb_gk_{p_name}"] = False
        if f"rating_{p_name}" not in st.session_state:
            st.session_state[f"rating_{p_name}"] = float(st.session_state.player_dict[p_name]["rating"])

    st.markdown("""
    <style>
    [data-testid="stHorizontalBlock"] {
        flex-wrap: nowrap !important;
        align-items: center !important;
        gap: 8px !important;
    }
    [data-testid="stHorizontalBlock"] > div {
        min-width: 0 !important;
        flex-shrink: 1 !important;
    }
    [data-testid="stHorizontalBlock"] p {
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }
    </style>
    """, unsafe_allow_html=True)

    _, h2, h3, h4 = st.columns([4, 1, 1, 2])
    h2.markdown("**Play**")
    h3.markdown("**GK**")
    h4.markdown("**Rating**")

    def on_gk_change(p_name):
        if st.session_state.get(f"cb_gk_{p_name}", False):
            st.session_state[f"cb_play_{p_name}"] = True

    for p_name in st.session_state.all_players:
        c1, c2, c3, c4 = st.columns([4, 1, 1, 2])
        c1.markdown(p_name)
        with c2:
            st.toggle("", key=f"cb_play_{p_name}", label_visibility="collapsed")
        with c3:
            st.toggle("", key=f"cb_gk_{p_name}", label_visibility="collapsed", on_change=on_gk_change, args=(p_name,))
        with c4:
            st.number_input("", key=f"rating_{p_name}", min_value=0.0, max_value=100.0, step=1.0, format="%.0f", label_visibility="collapsed")

    active_players = [p for p in st.session_state.all_players if st.session_state.get(f"cb_play_{p}", False)]
    gk_names = [p for p in active_players if st.session_state.get(f"cb_gk_{p}", False)]

    # -----------------------------
    # Counter (how many players selected)
    # -----------------------------
    st.metric("Selected players", len(active_players))


    # Validation
    if len(active_players) < MIN_PLAYERS:
        st.info(f"Please select at least {MIN_PLAYERS} players.")
        st.stop()

    if len(gk_names) < 2:
        st.info("Please tick exactly 2 goalkeepers.")
        st.stop()

    if len(gk_names) > 2:
        st.warning("Too many goalkeepers selected. Uncheck until exactly 2 remain.")
        st.stop()

    # Apply any rating overrides from the UI
    for p_name in st.session_state.all_players:
        new_rating = st.session_state.get(f"rating_{p_name}")
        if new_rating is not None:
            st.session_state.player_dict[p_name]["rating"] = new_rating

    # Convert active players into dict format with updated ratings
    active_player_dicts = [
        {"name": p["name"], "rating": st.session_state.player_dict[p["name"]]["rating"]}
        for p in st.session_state.players if p["name"] in active_players
    ]

    # -----------------------------
    # Shuffle / create teams
    # -----------------------------
    if st.button("Create teams / Shuffle") or submitted_new_player:
        submitted_new_player = False
        t1, t2 = balance_teams(active_player_dicts, gk_names[0], gk_names[1])
        st.session_state.team_crni = [p["name"] for p in t1]
        st.session_state.team_bijeli = [p["name"] for p in t2]

    # -----------------------------
    # Process queued moves
    # -----------------------------
    for src, dest, player in st.session_state.move_requests:
        st.write("Move request new")
        if player in st.session_state[src]:
            st.session_state[src].remove(player)
            st.session_state[dest].append(player)
    st.session_state.move_requests = []

    col1, col2 = st.columns(2)

    # -----------------------------
    # Display Teams
    # -----------------------------
    def display_team(session_team_name, other_session_team_name, team_label):
        team_list = st.session_state[session_team_name]
        st.markdown(f"**{team_label}** (Rating: {calculate_total(team_list, st.session_state.player_dict):.2f})")
        for idx, name in enumerate(team_list):
            p = st.session_state.player_dict[name]
            is_gk = "🧤 " if name in gk_names else ""
            c1, c2, c3 = st.columns([3, 2, 2])
            with c1:
                st.markdown(f"{idx+1}. {is_gk}{p['name']}")
            with c2:
                st.markdown(f"{p['rating']:.2f}")
            with c3:
                btn_key = f"{session_team_name}_move_{idx}_{name}"
                if st.button("↔️", key=btn_key):
                    # Apply move immediately
                    if name in st.session_state[session_team_name]:
                        st.session_state[session_team_name].remove(name)
                        st.session_state[other_session_team_name].append(name)

                    # Re-render app with updated team lists
                    st.rerun()
              
    with col1:
        display_team("team_crni", "team_bijeli", "Crni")
    with col2:
        display_team("team_bijeli", "team_crni", "Bijeli")

    # -----------------------------
    # WhatsApp-friendly output
    # -----------------------------
    total_crni = calculate_total(st.session_state.team_crni, st.session_state.player_dict)
    total_bijeli = calculate_total(st.session_state.team_bijeli, st.session_state.player_dict)

    def show_friendly_output(team_name, team, rating):
        lines = [team_name]
        num_players=len(team)
        lines.append(f"|Players: {num_players}, Rating: {rating:.2f}|")
        for idx, n in enumerate(team, 1):
            lines.append(f"{idx}. {n}")
        
        return lines
    
    lines=[]
    lines.extend(show_friendly_output("CRNI", st.session_state.team_crni, total_crni))
    lines.append("")
    lines.extend(show_friendly_output("BIJELI", st.session_state.team_bijeli, total_bijeli))
    
    team_text = "\n".join(lines)
    st.text_area("📋 Teams (copy/paste to WhatsApp)", value=team_text, height=300)
    st.download_button("⬇️ Download as TXT", data=team_text, file_name="teams.txt")


if __name__ == "__main__":
    main()
