import pymysql
import argparse
parser = argparse.ArgumentParser()
parser.add_argument('--playoffyear', help='foo help')
args = parser.parse_args()

# Steps to run:
# cd /Users/ryanzotti/Documents/workspace/NBApython/markov
# python driver_preprocessing.py --playoffyear 2015

con = pymysql.connect(
    host='localhost', 
    unix_socket='/tmp/mysql.sock', 
    user='root', passwd="", db='NBA')
mysql = con.cursor(pymysql.cursors.DictCursor)

def get_teams(mysql,playoff_year):
    teams = []
    mysql.execute('''
        select home as team from matches 
        where playoffyear = {playoff_year} group by 
        team order by team asc
    '''.format(playoff_year=playoff_year))
    for row in mysql.fetchall():
        teams.append(row['team'])
    return teams

def get_matches(mysql,playoff_year,team):
    matches = []
    mysql.execute('''
        select game_id from matches where playoffyear = {playoff_year} 
        and (home = '{team}' or away = '{team}') 
        order by game_date
    '''.format(playoff_year=playoff_year,team=team))
    for row in mysql.fetchall():
        matches.append(row['game_id'])
    return matches

def incorporate_new_state_transitions(mysql,team,game_id,state_transitions):
    mysql.execute('''
        select start_state, end_state, frequency from markov 
        where game_id = '{game_id}' and team = '{team}'
    '''.format(game_id=game_id,team=team))
    for row in mysql.fetchall():
        start_state = row['start_state']
        end_state = row['end_state']
        frequency = row['frequency']
        if start_state in state_transitions:
            if end_state in state_transitions[start_state]:
                state_transitions[start_state][end_state]+=frequency
            else:
                state_transitions[start_state][end_state]=frequency
        else: 
            state_transitions[start_state]={end_state:frequency}
    return state_transitions
            
def save_state_transitions_to_mysql(con,mysql,team,target_gameid,playoff_year,state_transitions):
    for start_state, end_states in state_transitions.items():
        for end_state in end_states:
            frequency = state_transitions[start_state][end_state]
            mysql.execute("""
                insert into markov_consolidated(target_gameid, playoffyear, team, start_state, 
                end_state, frequency) values("{target_gameid}","{playoffyear}","{team}",
                "{start_state}","{end_state}","{frequency}")""".format(
                target_gameid=target_gameid,playoffyear=playoff_year,team=team,
                start_state=start_state,end_state=end_state,frequency=frequency))
            con.commit()
    
for playoff_year in range(int(args.playoffyear),int(args.playoffyear)+1):
    teams = get_teams(mysql,playoff_year)
    for team in teams:
        state_transitions = {}
        matches = get_matches(mysql,playoff_year,team)
        for match_count, match in enumerate(matches):
            if match_count > 0:
                save_state_transitions_to_mysql(con,mysql,team,match,playoff_year,state_transitions)
                print(match)
            state_transitions = incorporate_new_state_transitions(
                mysql,team,match,state_transitions)
            
    
print('Finished')