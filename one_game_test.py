import pymysql
from random import uniform as random
import pandas as pd
con = pymysql.connect(host='localhost', 
                      unix_socket='/tmp/mysql.sock', 
                      user='root', passwd="", db='NBA')
mysql = con.cursor(pymysql.cursors.DictCursor)

def calculate_transition_probabilities(states,current_state):
    transition_states = states[current_state]
    total_transitions = 0
    for count in transition_states.values():
        total_transitions += count
    transition_probs = {}
    for state, count in transition_states.items():
        transition_probs[state] = count / total_transitions
    return transition_probs

def change_state(state, transition_states):
    random_number = random(0,1)
    for transition_state, bounds in transition_states[state].items():
        if random_number >= bounds['lower_bound'] and random_number < bounds['upper_bound']:
            state = transition_state
            break
    return state

def evaluate_scores(state,scorable_states,scores):
    for scorable_state, points in scorable_states.items():
        if scorable_state in state:
            for team in scores.keys():
                if team in state:
                    scores[team] += points
    return scores
    
home = 'San Antonio Spurs'
away = 'Oklahoma City Thunder'

mysql.execute("""
    select team_column, text from play_by_play_text 
    where game_id = '/boxscores/201503250SAS.html' 
    order by play_index asc""")

# The key is text matching state, and the value is generalized state
states = {
        'offensive rebound':'offensive rebound',
        'defensive rebound':'defensive rebound',
        'makes 2-pt shot':'makes 2-pt shot',
        'makes 3-pt shot':'makes 3-pt shot',
        'misses 2-pt shot':'misses 2-pt shot',
        'misses 3-pt shot':'misses 3-pt shot',
        'makes free throw 1 of 1':'makes last FT',
        'makes technical free throw':'makes last FT',
        'makes free throw 2 of 2':'makes last FT',
        'makes free throw 3 of 3':'makes last FT',
        'makes free throw 1 of 2':'makes free throw 1 of 2',
        'makes free throw 1 of 3':'makes free throw 1 of 3',
        'makes free throw 2 of 3':'makes free throw 2 of 3',
        'misses technical free throw':'misses last FT',
        'misses free throw 1 of 1':'misses last FT',
        'misses free throw 2 of 2':'misses last FT',
        'misses free throw 3 of 3':'misses last FT',
        'misses free throw 1 of 2':'misses free throw 1 of 2',
        'misses free throw 1 of 3':'misses free throw 1 of 3',
        'misses free throw 2 of 3':'misses free throw 2 of 3',
        'turnover':'turnover',
        'offensive foul':'offensive foul',
        'technical foul':'technical foul',
        'shooting foul':'shooting foul',
        'foul':'foul'
        }

scorable_states = {
       'makes 2-pt shot':2,
       'makes 3-pt shot':3,
       'makes last FT':1,
       'makes free throw 1 of 2':1,
       'makes free throw 1 of 3':1,
       'makes free throw 2 of 3':1}

# A regular foul is not the same as a shooting foul
complicated_states = {
       'foul':'shooting foul'
                      }

possession_states = [
       'defensive rebound',
       'makes 2-pt shot',
       'makes 3-pt shot',
       'misses last FT',
       'makes last FT',
       'turnover']

flipped_column_orientations = ['shooting foul']

# For skipping stupid cases where team records OREB after FT
one_of_several_ft = [
     '{team} makes free throw 1 of 2',
     '{team} makes free throw 1 of 3',
     '{team} makes free throw 2 of 3',
     '{team} misses free throw 1 of 2',
     '{team} misses free throw 1 of 3',
     '{team} misses free throw 2 of 3']

skippables = ['enters the game','violation','timeout']
transition_states = {}
previous_state = None
current_state = None
for row_counter, row in enumerate(mysql.fetchall()): 
    team = row['team_column']
    opp_team = get_opponent(team,home,away)
    text = row['text'].lower()
    if any(skippable in text for skippable in skippables):
        continue
    is_new_state = True
    for state, state_family in states.items():
        if state in text:
            is_new_state = False
            if state not in flipped_column_orientations:
                current_state = team+" "+state_family
            else:
                current_state = opp_team+" "+state_family
            break
    if is_new_state:
        print("New state: " + text)
        exit(1)
    # Do stuff once the state has been identified
    if row_counter > 0:
        # Logic for skipping stupid cases where team records OREB after a non-final FT
        if any(state.format(team=team) in previous_state for state in one_of_several_ft) and \
            "offensive rebound" in current_state:
            continue
        # Record the state transition
        if current_state in transition_states[previous_state]:
            transition_states[previous_state][current_state]+=1
        else:
            transition_states[previous_state][current_state]=1
    previous_state = current_state
    if previous_state not in transition_states:
        transition_states[previous_state]={}
        
for starting_state, future_states in transition_states.items():
    #print(str(starting_state)+" "+str(future_states))
    for future_state, frequency in future_states.items():
        print(str(starting_state)+" "+str(future_state)+" "+str(frequency))
 
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
simulation_results = pd.DataFrame(columns=['Oklahoma City Thunder','San Antonio Spurs'])
state = 'Oklahoma City Thunder turnover' # Randomly picked this hard-coded state
for game in range(games):
    scores = {'Oklahoma City Thunder':0,'San Antonio Spurs':0}
    for possession in range(possessions):
        state = change_state(state, transition_state_probabilities)
        scores = evaluate_scores(state,scorable_states,scores)
        while not any(possession_state in state for possession_state in possession_states):
            state = change_state(state, transition_state_probabilities)
            scores = evaluate_scores(state,scorable_states,scores)
    simulation_result = pd.DataFrame(scores,index=[game])
    simulation_results = simulation_results.append(simulation_result)
       
home = 'San Antonio Spurs'
away = 'Oklahoma City Thunder'

simulation_results['net_score'] = simulation_results[home] - simulation_results[away]
print(simulation_results['net_score'].mean())
print('Finished')