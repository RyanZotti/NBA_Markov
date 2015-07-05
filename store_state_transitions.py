import pymysql
import argparse
from markov_functions import (
    get_opponent)
from markov_states import (
    one_of_several_ft,
    states,
    flipped_column_orientations,
    skippables)
parser = argparse.ArgumentParser()
parser.add_argument('--playoffyear', help='foo help')
args = parser.parse_args()

# Steps to run:
# cd /Users/ryanzotti/Documents/workspace/NBApython/markov
# python store_state_transitions.py --playoffyear 2015

con = pymysql.connect(host='localhost', 
                      unix_socket='/tmp/mysql.sock', 
                      user='root', passwd="", db='NBA')
mysql = con.cursor(pymysql.cursors.DictCursor)

def get_matches(mysql,playoff_year):
    matches = []
    mysql.execute('''
    select home, away, game_id 
    from matches
    where playoffyear = {playoff_year} and not exists 
    (select * from markov where markov.game_id = matches.game_id)
    order by game_date asc
    '''.format(playoff_year=playoff_year))
    for row in mysql.fetchall():
        matches.append({'game_id':row['game_id'],
                'home':row['home'],
                'away':row['away']})
    return matches

for playoff_year in range(int(args.playoffyear),int(args.playoffyear)+1):
    matches = get_matches(mysql,playoff_year)
    for match in matches:
        game_id = match['game_id']
        home = match['home']
        away = match['away']
        mysql.execute("""
            select team_column, text from play_by_play_text 
            where game_id = '{game_id}' 
            order by play_index asc""".format(game_id=game_id))
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
                print("New state: "+text+" "+game_id)
                exit(1)
            # Do stuff once the state has been identified
            if row_counter > 0 and previous_state is not None:
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
        
        # Store home state transitions      
        for starting_state, future_states in transition_states.items():
            for future_state, frequency in future_states.items():
                starting_state = starting_state.replace(away,"Opponent").replace(home,"Team")
                future_state = future_state.replace(away,"Opponent").replace(home,"Team")
                mysql.execute("""insert into markov(
                    game_id, team, start_state, end_state, frequency) 
                    values("{game_id}","{team}","{start_state}","{end_state}","{frequency}")"""
                    .format(game_id=game_id,team=home,start_state=starting_state,
                    end_state=future_state,frequency=frequency))
                con.commit()
        
        # Store away state transitions
        for starting_state, future_states in transition_states.items():
            #print(str(starting_state)+" "+str(future_states))
            for future_state, frequency in future_states.items():
                starting_state = starting_state.replace(home,"Opponent").replace(away,"Team")
                future_state = future_state.replace(home,"Opponent").replace(away,"Team")
                mysql.execute("""insert into markov(
                    game_id, team, start_state, end_state, frequency) 
                    values("{game_id}","{team}","{start_state}","{end_state}","{frequency}")"""
                    .format(game_id=game_id,team=away,start_state=starting_state,
                    end_state=future_state,frequency=frequency))
                con.commit()
        print('Inserted ' + game_id)
    
print('Finished.')


