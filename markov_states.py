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
        'makes flagrant free throw 1 of 1':'makes last FT',
        'makes free throw 2 of 2':'makes last FT',
        'makes free throw 3 of 3':'makes last FT',
        'makes flagrant free throw 2 of 2':'makes last FT',
        'makes clear path free throw 2 of 2':'makes last FT',
        'makes free throw 1 of 2':'makes free throw 1 of 2',
        'makes free throw 1 of 3':'makes free throw 1 of 3',
        'makes free throw 2 of 3':'makes free throw 2 of 3',
        'makes clear path free throw 1 of 2':'makes clear path free throw 1 of 2',
        'makes flagrant free throw 1 of 2':'makes flagrant free throw 1 of 2',
        'misses technical free throw':'misses last FT',
        'misses flagrant free throw 1 of 1':'misses last FT',
        'misses clear path free throw 1 of 2':'misses clear path free throw 1 of 2',
        'misses free throw 1 of 1':'misses last FT',
        'misses free throw 2 of 2':'misses last FT',
        'misses free throw 3 of 3':'misses last FT',
        'misses flagrant free throw 2 of 2':'misses last FT',
        'misses clear path free throw 2 of 2':'misses last FT',
        'misses free throw 1 of 2':'misses free throw 1 of 2',
        'misses free throw 1 of 3':'misses free throw 1 of 3',
        'misses free throw 2 of 3':'misses free throw 2 of 3',
        'misses flagrant free throw 1 of 2':'misses flagrant free throw 1 of 2',
        'turnover':'turnover',
        'offensive foul':'offensive foul',
        'technical foul':'technical foul',
        'shooting foul':'shooting foul',
        'foul':'foul'
        }

# States that lead to a chance in score
scorable_states = {
       'makes 2-pt shot':2,
       'makes 3-pt shot':3,
       'makes last FT':1,
       'makes free throw 1 of 2':1,
       'makes free throw 1 of 3':1,
       'makes free throw 2 of 3':1,
       'makes flagrant free throw 1 of 2':1,
       'makes flagrant free throw 2 of 2':2,
       'makes technical free throw':1,
       'makes flagrant free throw 1 of 2':1,
       'makes flagrant free throw 2 of 2':1}

# A regular foul is not the same as a shooting foul
complicated_states = {
       'foul':'shooting foul'
                      }
# States that count as a possession
possession_states = [
       'defensive rebound',
       'makes 2-pt shot',
       'makes 3-pt shot',
       'misses last FT',
       'makes last FT',
       'turnover']


skippables = [
              'enters the game',
              'violation',
              'timeout',
              'defensive three seconds',
              'ejected from game']

flipped_column_orientations = ['shooting foul']

# For skipping stupid cases where team records OREB after FT
one_of_several_ft = [
     '{team} makes free throw 1 of 2',
     '{team} makes free throw 1 of 3',
     '{team} makes free throw 2 of 3',
     '{team} misses free throw 1 of 2',
     '{team} misses free throw 1 of 3',
     '{team} misses free throw 2 of 3',
     '{team} makes flagrant free throw 1 of 2',
     '{team} misses flagrant free throw 1 of 2',
     '{team} makes clear path free throw 1 of 2',
     '{team} misses clear path free throw 1 of 2']

