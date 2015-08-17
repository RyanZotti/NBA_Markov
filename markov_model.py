import pymysql
import multiprocessing as mp
import os
import argparse
# Steps to run:
# cd /Users/ryanzotti/Documents/workspace/NBApython/markov
# python markov_model.py --playoffyear 2003

# This person was able to get multiprocessing to work on a Mac with all cores used
# http://stackoverflow.com/questions/21031372/python-multiprocessing-troubleshooting

from markov_functions import (
    calculate_transition_probabilities,
    change_state,
    evaluate_scores,
    get_transition_states,
    reverse_team_orientation,
    get_unioned_state_transitions,
    check_probs_sum_to_one)
from markov_states import (
    scorable_states,
    possession_states)

def get_matches(mysql,playoff_year):
    matches = []
    mysql.execute('''
        select game_id, game_date, home, away, vegas_pred, target from matches 
        where playoffyear = {playoff_year}
        and not exists (select * from markov_results where markov_results.target_gameid = matches.game_id)
        and exists (select * from SRS_Build_Injury_Test_March_8_2015 where 
        SRS_Build_Injury_Test_March_8_2015.game_id = matches.game_id)
        order by game_date asc
    '''.format(playoff_year=playoff_year))
    for row in mysql.fetchall():
        matches.append({
            'game_id':row['game_id'],
            'home':row['home'],
            'away':row['away'],
            'vegas_pred':row['vegas_pred'],
            'target':row['target']})
    return matches

def simulate_game(possessions,transition_state_probabilities,games):
    state = 'Opponent turnover' # Randomly picked this hard-coded state
    scores = {'Team':0,'Opponent':0}
    for possession in range(possessions):
        state = change_state(state, transition_state_probabilities)
        scores = evaluate_scores(state,scorable_states,scores)
        while not any(possession_state in state for possession_state in possession_states):
            state = change_state(state, transition_state_probabilities)
            scores = evaluate_scores(state,scorable_states,scores)
    net_score = scores['Team'] - scores['Opponent']
    # Weighted so that I don't have to use numpy or pandas to get average
    # Numpy and Pandas don't work with the multiprocessing library on Macs
    weighted_net_score = (1 / games) * net_score
    return weighted_net_score

if __name__ == '__main__':
    # This line sets the number of CPUs because of a multiprocessing bug
    # The first argument should be 0 to mean this script, and the second
    # argument should be the number of cores
    
    #os.sched_setaffinity(0, 4)
    parser = argparse.ArgumentParser()
    parser.add_argument('--playoffyear', help='foo help')
    args = parser.parse_args()
    con = pymysql.connect(
      host='localhost', 
      unix_socket='/tmp/mysql.sock', 
      user='root', passwd="", db='NBA')
    mysql = con.cursor(pymysql.cursors.DictCursor)
    pool = mp.Pool(processes=100)
    for playoff_year in range(2003,2004):    
    #for playoff_year in range(int(args.playoffyear),int(args.playoffyear)+1):
        matches = get_matches(mysql,playoff_year)
        for match in matches:
            game_id = match['game_id']
            home = match['home']
            away = match['away']
            target = match['target']
            vegas_pred = match['vegas_pred']
            
            # Combine the home and away states
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
                probs = check_probs_sum_to_one(mysql,probs,starting_state)
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
            simulation_results = []
            simulation_results = [pool.apply(simulate_game,args=(possessions,transition_state_probabilities,games)) for x in range(games)]
            
            markov_pred = 0
            for simulation_result in simulation_results:
                #print(str(markov_pred)+" "+str(simulation_result))
                markov_pred += simulation_result
            mysql.execute("""insert into markov_results(target_gameid, playoffyear, home, away, target, vegas_pred, markov_pred) 
                values("{target_gameid}","{playoffyear}","{home}","{away}","{target}","{vegas_pred}","{markov_pred}")""".format(
                target_gameid=game_id,playoffyear=playoff_year,home=home,away=away,target=target,vegas_pred=vegas_pred,markov_pred=markov_pred))
            con.commit()
            print(game_id)
    print('Finished')