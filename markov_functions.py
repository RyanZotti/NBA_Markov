#import pymysql
from random import uniform as random

def calculate_transition_probabilities(states,current_state):
    transition_states = states[current_state]
    total_transitions = 0
    for count in transition_states.values():
        total_transitions += count
    transition_probs = {}
    for state, count in transition_states.items():
        if total_transitions > 0:
            transition_probs[state] = count / total_transitions
        else:
            transition_probs[state] = 0
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

# All probabilities should some to 1 or at least be a lot more than 0
# or else you'll get stuck in an infinite loop
def check_probs_sum_to_one(mysql,probs,start_state):
    new_probs = {}
    prob_total = 0
    for prob in probs.values():
        prob_total += prob
    if prob_total < 0.1:
        new_prob_total = 0 # For normalization, since new probs might not sum to 1
        prob = 0
        for end_state in probs.keys():
            mysql.execute('''
                select probability from markov_global_probs where start_state = '{start_state}' and
                end_state = '{end_state}'
            '''.format(start_state=start_state,end_state=end_state))
            for row in mysql.fetchall():
                prob = row['probability']
                new_prob_total += prob # For normalization, since new probs might not sum to 1
            new_probs[end_state]=prob
        # Normalize the probs, since new probs might not sum to 1
        for end_state, prob in new_probs.items():
            new_probs[end_state] = prob / new_prob_total
    else:
        new_probs = probs
    return new_probs
        
            
def get_transition_states(game_id,mysql,team):
    transition_states = {}
    mysql.execute("""select start_state, end_state, frequency 
        from markov_consolidated where target_gameid = '{game_id}' and 
        team = '{team}'""".format(team=team,game_id=game_id))
    for row in mysql.fetchall():
        start_state = row['start_state']
        end_state = row['end_state']
        frequency = row['frequency']
        if start_state in transition_states:
            transition_states[start_state][end_state]=frequency
        else:
            transition_states[start_state]={}
            transition_states[start_state][end_state]=frequency
    return transition_states

# Ex: Convert "Team does ABC" to "Opponent does ABC"
def reverse_team_orientation(state):
    reversed_state = None
    if "Team" in state:
        reversed_state = state.replace("Team","Opponent")
    elif "Opponent" in state:
        reversed_state = state.replace("Opponent","Team")
    return reversed_state

def get_opponent(team,home,away):
    opp = None
    if team in home:
        opp = away
    elif team in away:
        opp = home
    return opp

def get_unioned_state_transitions(mysql,game_id):
    mysql.execute('''
        select start_state, end_state 
        from markov_consolidated 
        where target_gameid = "{game_id}" 
        group by start_state, end_state
    '''.format(game_id=game_id))
    unioned_state_transitions = {}
    for row in mysql.fetchall():
        start_state = row['start_state']
        end_state = row['end_state']
        if start_state not in unioned_state_transitions:
            unioned_state_transitions[start_state] = []
        unioned_state_transitions[start_state].append(end_state)    
    return unioned_state_transitions
