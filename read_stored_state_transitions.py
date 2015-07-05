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

con = pymysql.connect(
      host='localhost', 
      unix_socket='/tmp/mysql.sock', 
      user='root', passwd="", db='NBA')
mysql = con.cursor(pymysql.cursors.DictCursor)

def get_matches(mysql,playoff_year):
    matches = []
    mysql.execute('''
        select game_id, game_date, home, away, vegas_pred, target from matches 
        left join (select target_gameid, count(*) as count from (
        select target_gameid, team from markov_consolidated group by target_gameid, team) as t1
        group by target_gameid) as t2 on
        matches.game_id = t2.target_gameid
        where playoffyear = {playoff_year} and count = 2
        and not exists (select * from markov_results where markov_results.target_gameid = matches.game_id)
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

for playoff_year in range(2003,2004):   
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
            lower_bound = 0
            upper_bound = 0
            for transition_state, prob in probs.items():
                lower_bound = upper_bound
                upper_bound = lower_bound + prob
                probs[transition_state] = {'lower_bound':lower_bound,'upper_bound':upper_bound,'prob':prob}
            transition_state_probabilities[starting_state] = probs
            
            # Fixes a rare bug where state is "technical foul' and there is only 1 end state and it 
            # has 0 probability (Opponent misses last FT)
            if len(transition_state_probabilities[starting_state].items()) == 1:
                for ending_state in transition_state_probabilities[starting_state].values():
                    probs[transition_state] = {'lower_bound':lower_bound,'upper_bound':1,'prob':1}
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
        markov_pred = simulation_results['net_score'].mean()
        mysql.execute("""insert into markov_results(target_gameid, playoffyear, home, away, target, vegas_pred, markov_pred) 
            values("{target_gameid}","{playoffyear}","{home}","{away}","{target}","{vegas_pred}","{markov_pred}")""".format(
            target_gameid=game_id,playoffyear=playoff_year,home=home,away=away,target=target,vegas_pred=vegas_pred,markov_pred=markov_pred))
        con.commit()
        print(game_id+" "+str(markov_pred))
print('Finished')