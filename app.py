import streamlit as st
import csv
import random

# ----------------------------
# CSV Reading
# ----------------------------
def read_players_from_upload(uploaded_file):
    players = []
    content = uploaded_file.read().decode("utf-8").splitlines()
    delimiter = "\t" if "\t" in content[0] else ","
    reader = csv.reader(content, delimiter=delimiter)
    # Include header
    for row in reader:
        if len(row) < 3:
            continue
        name = row[0].strip()
        try:
            rating = float(row[2].strip())
        except ValueError:
            continue
        players.append({"name": name, "rating": rating})
    return players

# ----------------------------
# Team balancing
# ----------------------------
def balance_teams(players):
    if len(players) < 4:
        return None, None
    gk1, gk2 = players[0], players[1]
    field_players = players[2:]
    team_size = len(players) // 2 - 1
    best_diff = float('inf')
    best_t1, best_t2 = None, None
    for _ in range(10000):
        random.shuffle(field_players)
        t1 = [gk1] + field_players[:team_size]
        t2 = [gk2] + field_players[team_size:]
        diff = abs(sum(p['rating'] for p in t1) - sum(p['rating'] for p in t2))
        if diff < best_diff:
            best_diff = diff
            best_t1, best_t2 = t1[:], t2[:]
    return best_t1, best_t2

# ----------------------------
# Utility
# ----------------------------
def calculate_total(team, player_dict):
    return sum(player_dict[n]['rating'] for n in team)

# ----------------------------
# Main app
# ----------------------------
def main():
    st.title("⚽ Two-Column Team Balancer")
    st.write("Upload CSV (first two players = goalkeepers). Move players using buttons; totals auto-update.")

    uploaded_file = st.file_uploader("Upload CSV file", type=["csv"])
    if not uploaded_file:
        return

    players = read_players_from_upload(uploaded_file)
    if not players:
        st.error("No valid player data found.")
        return

    player_dict = {p['name']: p for p in players}

    # ----------------------------
    # Initialize session state
    # ----------------------------
    if "team_crni" not in st.session_state:
        t1, t2 = balance_teams(players)
        st.session_state.team_crni = [p['name'] for p in t1]
        st.session_state.team_bijeli = [p['name'] for p in t2]

    if "move_requests" not in st.session_state:
        st.session_state.move_requests = []

    # ----------------------------
    # Process queued moves
    # ----------------------------
    for src, dest, player in st.session_state.move_requests:
        gk_names = [players[0]['name'], players[1]['name']]
        # goalkeeper check
        if player in gk_names:
            other_gk = [gk for gk in gk_names if gk != player][0]
            if other_gk in st.session_state[dest]:
                st.warning(f"Goalkeepers must be separated!")
                continue
        if player in st.session_state[src]:
            st.session_state[src].remove(player)
            st.session_state[dest].append(player)
    st.session_state.move_requests = []

    # ----------------------------
    # Shuffle Teams
    # ----------------------------
    if st.button("🔀 Shuffle Teams"):
        t1, t2 = balance_teams(players)
        st.session_state.team_crni = [p['name'] for p in t1]
        st.session_state.team_bijeli = [p['name'] for p in t2]

    col1, col2 = st.columns(2)

    # ----------------------------
    # Display Teams
    # ----------------------------
    def display_team(session_team_name, other_session_team_name, team_label):
        team_list = st.session_state[session_team_name]
        other_team_list = st.session_state[other_session_team_name]

        st.markdown(f"**{team_label}** (Total: {calculate_total(team_list, player_dict):.2f})")

        for idx, name in enumerate(team_list):
            p = player_dict[name]
            c1, c2, c3 = st.columns([3, 1, 2])
            with c1:
                label = f"🧤 {p['name']}" if name in [players[0]['name'], players[1]['name']] else p['name']
                st.markdown(label)
            with c2:
                st.markdown(f"{p['rating']:.2f}")
            with c3:
                btn_key = f"{session_team_name}_move_{idx}_{name}"  # unique key
                if st.button("Move", key=btn_key):
                    st.session_state.move_requests.append((session_team_name, other_session_team_name, name))

    with col1:
        display_team("team_crni", "team_bijeli", "Crni")
    with col2:
        display_team("team_bijeli", "team_crni", "Bijeli")

    # ----------------------------
    # WhatsApp-friendly output
    # ----------------------------
    total_crni = calculate_total(st.session_state.team_crni, player_dict)
    total_bijeli = calculate_total(st.session_state.team_bijeli, player_dict)

    lines = [f"CRNI (Total: {total_crni:.2f})"]
    for idx, n in enumerate(st.session_state.team_crni, 1):
        lines.append(f"{idx}. {n}")
    lines.append("")
    lines.append(f"BIJELI (Total: {total_bijeli:.2f})")
    for idx, n in enumerate(st.session_state.team_bijeli, 1):
        lines.append(f"{idx}. {n}")

    team_text = "\n".join(lines)
    st.text_area("📋 Teams (copy/paste to WhatsApp)", value=team_text, height=300)
    st.download_button("⬇️ Download as TXT", data=team_text, file_name="teams.txt")

if __name__ == "__main__":
    main()
