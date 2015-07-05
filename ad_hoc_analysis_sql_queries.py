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

# one-time fix for Bobcats to Hornets name change
create temporary table updates
select game_id from matches where (home = 'Charlotte Hornets' or away = 'Charlotte Hornets');
update play_by_play_text set team_column = 'Charlotte Hornets' 
where team_column = 'Charlotte Bobcats' and exists (select * from updates where updates.game_id = play_by_play_text.game_id)
# related fix
delete from markov where exists (select * from matches where matches.playoffyear = 2015 and markov.game_id = matches.game_id)


create table markov_global_end_state_frequencies
select start_state, end_state, sum(frequency) as frequency from markov_consolidated group by start_state, end_state

create table markov_global_start_state_frequencies
select start_state, sum(frequency) as frequency from markov_consolidated group by start_state

create table markov_global_probs
select a.start_state, a.end_state, a.frequency / b.frequency as probability
from markov_global_end_state_frequencies as a
left join markov_global_start_state_frequencies as b on
a.start_state = b.start_state


'''