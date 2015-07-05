import pymysql
import pandas as pd
from markov_functions import (
    calculate_transition_probabilities,
    change_state,
    evaluate_scores,
    get_transition_states,
    reverse_team_orientation,
    get_unioned_state_transitions)
from markov_states import (
    scorable_states,
    possession_states)

con = pymysql.connect(host='localhost', 
                      unix_socket='/tmp/mysql.sock', 
                      user='root', passwd="", db='NBA')
mysql = con.cursor(pymysql.cursors.DictCursor)

home = 'Phoenix Suns'
away = 'Utah Jazz'
game_id = '/boxscores/200611030PHO.html'
               
unioned_state_transitions = get_unioned_state_transitions(mysql,game_id)
transition_states = {}
transition_states_home = get_transition_states(game_id,mysql,home)
transition_states_away = get_transition_states(game_id,mysql,away)
for start_state, end_states in unioned_state_transitions.items():
    transition_states[start_state] = {}
    opp_start_state = reverse_team_orientation(start_state)
    if start_state not in transition_states_home:
        transition_states_home[start_state] = []
    if opp_start_state not in transition_states_away:
        transition_states_away[opp_start_state] = []
    for end_state in end_states:
        opp_end_state = reverse_team_orientation(end_state)
        home_count = 0
        away_count = 0
        if end_state in transition_states_home[start_state]:
            home_count = transition_states_home[start_state][end_state]
        if opp_end_state in transition_states_away[opp_start_state]:
            away_count = transition_states_away[opp_start_state][opp_end_state]
        count_avg = (home_count + away_count) / 2
        transition_states[start_state][end_state] = count_avg
        
# Calculate bins to be used for state transition selection during random number generation
transition_state_probabilities = {}
for starting_state in transition_states.keys():
    probs = calculate_transition_probabilities(transition_states,starting_state)
    lower_bound = 0
    upper_bound = 0
    for transition_state, prob in probs.items():
        lower_bound = upper_bound
        upper_bound = lower_bound + prob
        probs[transition_state] = {'lower_bound':lower_bound,'upper_bound':upper_bound,'prob':prob}
    transition_state_probabilities[starting_state] = probs

# Now it's time to run the simulations
games = 1000
possessions = 188
simulation_results = pd.DataFrame(columns=['Team','Opponent'])
state = 'Opponent turnover' # Randomly picked this hard-coded state
for game in range(games):
    scores = {'Team':0,'Opponent':0}
    for possession in range(possessions):
        state = change_state(state, transition_state_probabilities)
        scores = evaluate_scores(state,scorable_states,scores)
        while not any(possession_state in state for possession_state in possession_states):
            state = change_state(state, transition_state_probabilities)
            scores = evaluate_scores(state,scorable_states,scores)
    simulation_result = pd.DataFrame(scores,index=[game])
    simulation_results = simulation_results.append(simulation_result)
    
# Success if team wins by about 39 point (give or take a point)
simulation_results['net_score'] = simulation_results['Team'] - simulation_results['Opponent']
print(simulation_results['net_score'].mean())
print('Finished')