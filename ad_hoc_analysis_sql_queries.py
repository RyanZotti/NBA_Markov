'''
# Prints my average error for all of the games where each team has played at least 12 games
select 
avg(abs(markov_pred +3 - a.target)) - avg(abs(a.vegas_pred - a.target)) as net_abs,
avg(abs(a.vegas_pred - a.target)) as vegas_pred_error, 
avg(abs(markov_pred +3 - a.target)) as markov_pred_error,
avg(model_abs_error) - avg(vegas_abs_error) as net_abs_gbm,
count(*) as count
from markov_results as a
inner join SRS_Build_Injury_Test_March_8_2015 as b on
a.target_gameid = b.game_id
'''