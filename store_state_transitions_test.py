import pymysql
from markov_functions import (
    get_opponent)
from markov_states import (
    one_of_several_ft,
    states,
    flipped_column_orientations,
    skippables)

con = pymysql.connect(host='localhost', 
                      unix_socket='/tmp/mysql.sock', 
                      user='root', passwd="", db='NBA')
mysql = con.cursor(pymysql.cursors.DictCursor)

home = 'San Antonio Spurs'
away = 'Oklahoma City Thunder'

game_id = '/boxscores/201503250SAS.html' 
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

# Store home state transitions      
for starting_state, future_states in transition_states.items():
    for future_state, frequency in future_states.items():
        starting_state = starting_state.replace(away,"Opponent").replace(home,"Team")
        future_state = future_state.replace(away,"Opponent").replace(home,"Team")
        mysql.execute("""insert into post_game_markov(game_id, team, start_state, end_state, frequency) values("{game_id}","{team}","{start_state}","{end_state}","{frequency}")""".format(game_id=game_id,team=home,start_state=starting_state,end_state=future_state,frequency=frequency))
        con.commit()

# Store away state transitions
for starting_state, future_states in transition_states.items():
    #print(str(starting_state)+" "+str(future_states))
    for future_state, frequency in future_states.items():
        starting_state = starting_state.replace(home,"Opponent").replace(away,"Team")
        future_state = future_state.replace(home,"Opponent").replace(away,"Team")
        mysql.execute("""insert into post_game_markov(game_id, team, start_state, end_state, frequency) values("{game_id}","{team}","{start_state}","{end_state}","{frequency}")""".format(game_id=game_id,team=away,start_state=starting_state,end_state=future_state,frequency=frequency))
        con.commit()
    
print('Finished.')


