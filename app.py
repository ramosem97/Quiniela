import dash
import os
import dash_bootstrap_components as dbc
import pandas as pd
import numpy as np
import nflapi
from dash import Dash, dash_table, dcc, html
from dash_extensions.enrich import (Dash, Input, Output, ServersideOutput,
                                    State, Trigger)
from apps import navbar, scores_page, stats_page

############# GLOBAL VARS ###################
USER_LIST = ['Gel','Hector','Emilio','Sonny']
nfl = nflapi.NFL(ua="nflapi_quiniela")

HOME_COLS = {}
HOME_COLS['id'] = ['home_team', 'abbreviation_home', 'nick_name_home',
       'full_name_home', 'conference_home', 'division_home', 'city_state_region_home', 'venue_home', ]
HOME_COLS['val_for'] =  ['home_points_q1', 'home_points_q2',
       'home_points_q3', 'home_points_q4', 'home_points_overtime_total', 'home_team_score', 'home_passing_yards',
       'home_passing_touchdowns', 'home_rushing_yards',
       'home_rushing_touchdowns']

AWAY_COLS = {}
AWAY_COLS['id'] = ['away_team', 'abbreviation_away','nick_name_away',
       'full_name_away', 'conference_away', 'division_away', 'city_state_region_away', 'venue_away',]
AWAY_COLS['val'] = ['visitor_points_q1', 'visitor_points_q2',
       'visitor_points_q3', 'visitor_points_q4', 'visitor_points_overtime_total',  'away_team_score', 
       'visitor_passing_yards', 'visitor_passing_touchdowns', 'visitor_rushing_yards','visitor_rushing_touchdowns']

############## READ IN QUINIELA DATA ########
preds = pd.read_csv('data/quiniela_res.csv').sort_values(['season', 'week'], ascending=True)
preds['season'] = preds['season'].astype(int)
preds['week'] = preds['week'].astype(int)
preds = preds.rename(columns={'Home Team': 'home_team', 'Away Team':'away_team'})

############# READ IN TEAMS DATA ############
teams = pd.read_csv('data/nfl_team_info_all.csv', index_col=0)
teams['season'] = teams['season'].astype(int)
team_dec = teams.groupby(['full_name', 'abbreviation']).size().reset_index(drop=False).set_index(['full_name'])['abbreviation'].to_dict()


############# READ IN SCORES DATA ###########
scores = pd.read_csv('data/nfl_scores_all.csv', index_col=0)
scores['season'] = scores['season'].astype(int)
scores['week'] = scores['week'].astype(int)
scores['home_team'] = scores['home_team'].apply(lambda x: team_dec[x])
scores['away_team'] = scores['away_team'].apply(lambda x: team_dec[x])
scores['winner'] = [None if((pd.isnull(home_score)) | (pd.isnull(away_score))) else \
                    home_team if home_score + home_ot_score > away_score + away_ot_score else \
                    away_team if away_score + away_ot_score > home_score + home_ot_score else \
                    'TIE' for home_ot_score, away_ot_score, home_score, away_score, home_team, away_team in \
                    scores[['home_team_score', 'away_team_score', 
                            'home_points_overtime_total', 'visitor_points_overtime_total', 
                            'home_team', 'away_team']].values]

############# CREATE FULL DATASET ###########
## Merge Home Team Info
df = scores.merge(teams.rename(columns={x:x+'_home' for x in teams.columns if x != 'season'}),
                    left_on=['home_team', 'season'], 
                    right_on=['abbreviation_home', 'season'], 
                    suffixes=['', '_home'],
                    how='left')

## Merge Away Team Info
df = df.merge(teams.rename(columns={x:x+'_away' for x in teams.columns if x != 'season'}), 
                    left_on=['away_team', 'season'], 
                    right_on=['abbreviation_away', 'season'], 
                    suffixes=['', '_away'],
                    how='left')
## Create New Week Num Column
week_type_order = {'REG':1, 'WC':2, 'DIV':3, 'CONF':4, 'SB':5}
df['week_type_ord'] = df['week_type'].apply(lambda x: week_type_order[x])
week_dec = df.sort_values(['game_date', 'week_type_ord', 'season'], ascending=True).reset_index(drop=True).groupby(['season', 'week_type_ord', 'week']).size().reset_index(drop=False)
week_dec['week_num'] = week_dec.groupby(['season'])['season'].cumcount()+1
df = df.merge(week_dec.drop(0, axis=1), 
                    left_on=['season', 'week', 'week_type_ord'],
                    right_on=['season', 'week', 'week_type_ord'],
                    how='left')

## Merge Users Pred Info
df = df.merge(preds, 
                    left_on=['home_team', 'away_team', 'season'], 
                    right_on=['home_team', 'away_team', 'season'],
                    how='left',
                    suffixes=['', '_quin'])

## Remove Duplicate Entries
dup_games = scores.groupby(['home_team', 'away_team', 'season']).size()
dup_games = dup_games[dup_games>1].reset_index(drop=False)
drop_idxL = []
for idx, dup_game in dup_games.iterrows():
    temp_dup = df.loc[((df['home_team'] == dup_game['home_team']) & (df['away_team'] == dup_game['away_team']) &  (df['season'] == dup_game['season']))].reset_index(drop=False)
    temp_dup['week_num_diff'] = abs(temp_dup['week_quin'] - temp_dup['week_num'])
    drop_idxL = drop_idxL + temp_dup.sort_values(['week_num_diff'], ascending=False).drop_duplicates(['game_id'], keep='first')['index'].values.tolist()
df = df.loc[~df.index.isin(drop_idxL)].reset_index(drop=True)

######### CREATE TEAM DATASET ###############
df_home = df.copy()

df_home = df_home.drop([x for x in AWAY_COLS['id'] if x != 'away_team'][0], axis=1)
df_home = df_home.rename(columns={x:x.replace('visitor', 'against').replace('away', 'against').replace('_home', '').replace('home_', '') for x in df_home.columns})
df_home['home_or_away'] = 'home'

df_away = df.copy()
df_away = df_away.drop([x for x in HOME_COLS['id'] if x != 'home_team'][0], axis=1)
df_away = df_away.rename(columns={x:x.replace('home', 'against').replace('_away', '').replace('away_', '').replace('visitor_', '') \
    for x in df_away.columns})
df_away['home_or_away'] = 'away'

df_teams = pd.concat([df_home, df_away]).sort_values(['season', 'week', 'game_time']).reset_index(drop=True)

############ CREATE USER SCORE DF ############
USER_LIST = ['Gel','Hector','Emilio','Sonny']
userL=USER_LIST

user_df = df.copy()[USER_LIST+['winner', 'season', 'week_num']]

for user in userL:

    user_df.loc[user_df[user] == user_df['winner'], user+'_correct'] = 1
    user_df.loc[user_df[user] != user_df['winner'], user+'_correct'] = 0

user_df = user_df.groupby(['season', 'week_num'])[[x+'_correct' for x in userL]].sum()
user_df[[x+'_score' for x in userL]] = user_df.groupby(['season'])[[x+'_correct' for x in userL]].cumsum()
user_df = user_df.reset_index(drop=False)

############# START APP ######################
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app = dash.Dash(external_stylesheets=[dbc.themes.BOOTSTRAP])

server = app.server
app.config.suppress_callback_exceptions = True
# app.css.config.serve_locally = True
# app.scripts.config.serve_locally = True


############## LOGGING #####################
import logging, sys

app.logger.addHandler(logging.StreamHandler(sys.stdout))
app.logger.setLevel(logging.ERROR)

####################################################
################ DEFINE DEFAULT LAYOUT #############
####################################################

app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    navbar.layout,
    html.Div(children=[], id='page',
    style={'width':'100%', 'textAlign':'center', 'justify':'center', 'display':'inline-block'})
])





@app.callback([Output("page", "children"), Output("week", "options"),],
[Input("season", "value"), Input("week", "value")])
def print_df(season, week):

    ## Get Score Children
    children = scores_page.display_scores(season=season, 
                                            week=week,
                                            user='Emilio')

    ### Update Week Options
    week_options = [{'label':"{week_type} - {week}".format(week=week_num, week_type=week_type), 'value':week_num} \
                            for week_num, week, week_type in df.loc[df['season']==season]\
                            .sort_values('week_num', ascending=True).groupby(['week_num', 'week', 'week_type']).size()\
                                .reset_index(drop=False)[['week_num', 'week', 'week_type']].values]


    ## Get Table of Scores


    return children, week_options

if __name__ == '__main__':

    debug=True
    if debug:
            app.run_server(debug=debug, port=8060)
    else:
        app.run_server(debug=debug, host='0.0.0.0', port=8060)
