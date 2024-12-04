import random
import json
import multiprocessing
from functools import partial


# Load the initial team data from a JSON file
with open("teams.json", "r", encoding="utf-8") as f:
    teams = json.load(f)

# Initialize statistics
statistics = {team: {"3-0": 0, "3-1_or_2": 0, "0-3": 0,"1_or_2-3":0} for team in teams}

def reset_teams():
    """Reset the team statistics for a new tournament iteration."""
    for team in teams:
        teams[team]["win_count"] = 0
        teams[team]["lose_count"] = 0
        teams[team]["opponents"] = []
        teams[team]["swiss_score"] = 0

def match(battlevalueA, battlevalueB):
    if battlevalueA > battlevalueB:
        return 1
    elif battlevalueA < battlevalueB:
        return -1
    else:
        return random.choice([1, -1])

def matchmatch(teamlist):
    unmatched_teams = set(teamlist)
    while len(unmatched_teams) > 1:
        # Pick the first team to match
        team_a = unmatched_teams.pop()
        # Find the best opponent that hasn't been faced yet
        possible_opponents = [t for t in unmatched_teams if t not in teams[team_a]["opponents"]]
        if not possible_opponents:  # If no "new" opponents, fallback to any opponent
            possible_opponents = list(unmatched_teams)
        team_b = min(possible_opponents, key=lambda t: teams[t]["seed"])
        unmatched_teams.remove(team_b)
        # Simulate the match
        battlevalueA = teams[team_a]["battle_value"] * random.uniform(1-teams[team_a]["random_factor"], 1+teams[team_a]["random_factor"])
        battlevalueB = teams[team_b]["battle_value"] * random.uniform(1-teams[team_b]["random_factor"], 1+teams[team_b]["random_factor"])
        result = match(battlevalueA, battlevalueB)
        if result == 1:
            teams[team_a]["win_count"] += 1
            teams[team_b]["lose_count"] += 1
        elif result == -1:
            teams[team_a]["lose_count"] += 1
            teams[team_b]["win_count"] += 1
        teams[team_a]["opponents"].append(team_b)
        teams[team_b]["opponents"].append(team_a)

def swiss_round():
    for team in teams:
        swiss_score = 0
        for opponent in teams[team]["opponents"]:
            opponent_score = teams[opponent]["win_count"] - teams[opponent]["lose_count"]
            swiss_score += opponent_score
        teams[team]["swiss_score"] = swiss_score

def find_opponents(win_count,lose_count):
    global teams
    all_opps = []
    for team in teams:
        if teams[team]["win_count"] == win_count and teams[team]["lose_count"] == lose_count:
            all_opps.append(team)
    if all_opps == []:
        return None
    else:
        return all_opps

def swissmatch(win_score, lose_score):
    teamlist = find_opponents(win_score, lose_score)
    if teamlist !=None:
        teamlist = sorted(teamlist, key=lambda x: (teams[x]["swiss_score"], teams[x]["seed"]))
        matchmatch(teamlist)

def run_tournament():
    """Simulate one iteration of the tournament."""
    global teams

    # Round 1
    winnergroup = []
    losergroup = []
    for i in range(1, 9):
        team_a = f"team_{i}"
        team_b = f"team_{i + 8}"
        battlevalueA = teams[team_a]["battle_value"]* random.uniform(1-teams[team_a]["random_factor"], 1+teams[team_a]["random_factor"])
        battlevalueB = teams[team_b]["battle_value"]* random.uniform(1-teams[team_b]["random_factor"], 1+teams[team_b]["random_factor"])
        result = match(battlevalueA, battlevalueB)
        if result == 1:
            teams[team_a]["win_count"] += 1
            teams[team_b]["lose_count"] += 1
            winnergroup.append(team_a)
            losergroup.append(team_b)
        elif result == -1:
            teams[team_a]["lose_count"] += 1
            teams[team_b]["win_count"] += 1
            winnergroup.append(team_b)
            losergroup.append(team_a)
        teams[team_a]["opponents"].append(team_b)
        teams[team_b]["opponents"].append(team_a)

    # Round 2
    winnergroup = sorted(winnergroup, key=lambda x: teams[x]["seed"])
    losergroup = sorted(losergroup, key=lambda x: teams[x]["seed"])
    matchmatch(winnergroup)
    matchmatch(losergroup)

    # Rounds 3-5 (Swiss Rounds)
    for round in range(3, 6):
        swiss_round()  # Update Swiss scores
        swissmatch(2, round - 3)  # 2-win group
        if round-2 < 3:
            swissmatch(1, round - 2)  # 1-win group
        if round-1 < 3:
            swissmatch(0, round - 1)  # 0-win group
        #print("round",round)

    # Update statistics after the tournament
    for team in teams:
        win_count = teams[team]["win_count"]
        lose_count = teams[team]["lose_count"]
        if win_count == 3 and lose_count == 0:
            statistics[team]["3-0"] += 1
        elif win_count == 3 and lose_count > 0:
            statistics[team]["3-1_or_2"] += 1
        elif win_count == 0 and lose_count == 3:
            statistics[team]["0-3"] += 1
        elif win_count < 3 and lose_count == 3:
            statistics[team]["1_or_2-3"] += 1



from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import ProcessPoolExecutor, as_completed

# Load the initial team data from a JSON file
with open("teams.json", "r", encoding="utf-8") as f:
    teams = json.load(f)

statistics = {team: {"3-0": 0, "3-1_or_2": 0, "0-3": 0, "1_or_2-3": 0} for team in teams}

# Functions as in the original code, unchanged (e.g., reset_teams, match, matchmatch, swiss_round, etc.)

def simulate_tournament_chunk(chunk_size):
    """Simulate a chunk of tournaments and return partial statistics."""
    local_statistics = {team: {"3-0": 0, "3-1_or_2": 0, "0-3": 0, "1_or_2-3": 0} for team in teams}
    for _ in range(chunk_size):
        reset_teams()
        run_tournament()
        for team in teams:
            win_count = teams[team]["win_count"]
            lose_count = teams[team]["lose_count"]
            if win_count == 3 and lose_count == 0:
                local_statistics[team]["3-0"] += 1
            elif win_count == 3 and lose_count > 0:
                local_statistics[team]["3-1_or_2"] += 1
            elif win_count == 0 and lose_count == 3:
                local_statistics[team]["0-3"] += 1
            elif win_count < 3 and lose_count == 3:
                local_statistics[team]["1_or_2-3"] += 1
    return local_statistics

def merge_statistics(global_stats, partial_stats):
    """Merge partial statistics into the global statistics."""
    for team, stats in partial_stats.items():
        for key in stats:
            global_stats[team][key] += stats[key]

# Main simulation with ProcessPoolExecutor
def main():
    simulate_time = 100000000
    total_chunks = 640  # Number of chunks to process
    chunk_size = simulate_time // total_chunks  # Divide work into x chunks

    completed_chunks = 0

    with ProcessPoolExecutor() as executor:
        futures = [executor.submit(simulate_tournament_chunk, chunk_size) for _ in range(total_chunks)]
        for future in as_completed(futures):  # Track completion of each chunk
            partial_stats = future.result()
            merge_statistics(statistics, partial_stats)
            completed_chunks += 1
            print(f"Progress: {completed_chunks}/{total_chunks} chunks completed ({(completed_chunks / total_chunks) * 100:.2f}%).")

    # Print statistics
    for team, stats in statistics.items():
        prob30 = stats["3-0"] / simulate_time * 100
        prob31or32 = stats["3-1_or_2"] / simulate_time * 100
        prob03 = stats["0-3"] / simulate_time * 100
        prob13or23 = stats["1_or_2-3"] / simulate_time * 100
        print(f"{teams[team]['name']}: \n3-0: {prob30:.2f}%, 3-1/2: {prob31or32:.2f}%, 0-3: {prob03:.2f}%, 1/2-3: {prob13or23:.2f}%")

if __name__ == "__main__":
    main()
