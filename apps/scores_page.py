### Imports
import pandas as pd
import numpy as np
from datetime import datetime
from dash import dash_table as dt
from dash import html as html
import plotly.graph_objects as go
from dash import dcc as dcc
import dash_bootstrap_components as dbc
import plotly.express as px
# from dash.dependencies import Input, Output, State
from dash_extensions.enrich import Dash, ServersideOutput, Output, Input, Trigger
# from PIL import Image

## App Import
# from app import df, USER_LIST, user_df, df_teams, USER_ABBV_DICT

team_width = '25%'
min_team_width = '20%'
vs_width = '15%'
preds_width = '25%'
min_preds_width = '20%'
margin_padding = '1%'

header_size = '12px'
pred_font_size = '2vw'
score_font_size = '2.5vw'
dt_table_font_size = '9px'
logo_size = '8vw'
team_name_size='2vw'

table_css=[{
            'selector': '.dash-spreadsheet td div',
            'rule': '''
                line-height: 10px;
                max-height: 15px; min-height: 15px; height: 15px;
                display: block;
                overflow-y: hidden;
            '''
        }]

####################################################
################# CONFIG FUNCTIONS #################
####################################################

########## BORDER SEP ###########################
def end_row():
    return [dbc.Row(
            [
                html.Div('', style={'width':'10%'}), 
                html.Div('', style={'textAlign':'center', 'height':'1vw', 'justify':'center', 'borderBottom':".5px outset rgba(255,255,255,.2)", 'width':'80%', 'borderBottomWidth':'light'}),
                html.Div('', style={'width':'10%'}), 
            ]),
            html.Br()]

################ BORDER IF WINNER #############
def border_if_winner(team, winner, final=True):
    
    if final == True:
        if team == winner:
            return {'border':"2px MediumSeaGreen solid", 'borderRadius': '20%',
                     
                    }
        elif winner == 'TIE':
            return {'border':"2px GoldenRod solid", 'borderRadius': '10%',
                    
                }
        else:
            return {}
    else:
        return {}

####################################################
################# HELPER FUNCTIONS #################
####################################################

################ TEAM RANKINGS #############
def team_rankings(df_teams, week, season):

    ## Get Data For Current Week and Season
    curr_teams = df_teams.loc[df_teams['season']==season].loc[df_teams['week_num']<week].reset_index(drop=True)

    ## Against Cols
    # against_cols = ['against_passing_yards','against_passing_touchdowns', 'against_rushing_yards','against_rushing_touchdowns', 'total_against_score', 'against_total_yards']
    against_cols = ['total_against_score', 'against_total_yards']

    ## For Cols
    # for_cols = ['passing_yards', 'passing_touchdowns', 'rushing_yards', 'rushing_touchdowns', 'total_score', 'total_yards']
    for_cols = ['total_score', 'total_yards']

    ## Div or Conf Cols
    curr_teams['game'] = 1
    curr_teams['win'] = [1 if x==y else 0 for x,y in curr_teams[['team', 'winner']].values]
    other_cols = ['win', 'game', 'conf_game', 'div_game']

    ## Team Overall Summary
    team_summ = curr_teams.groupby(['team', 'division', 'conference'])[against_cols + for_cols].agg('sum')
    team_summ = team_summ.merge(curr_teams.groupby(['team', 'division', 'conference'])[other_cols].agg('sum'),
                            left_index=True, right_index=True).reset_index(drop=False)

    ########## Rankings ###############
    rankings = {}

    ## Division Ranking
    rankings['div'] = pd.concat([
                            team_summ[['team', 'div_game', 'win']], 
                            team_summ.groupby(['division'])[for_cols + ['win']].rank(ascending=False, method='min').rename(columns={'win':'RANK'}),
                            team_summ.groupby(['division'])[against_cols].rank(ascending=True, method='min'), 
                            ], axis=1).rename(columns={'div_game':'game'})
    rankings['div']['SET'] = 'DIV'


    ## Conference Ranking
    rankings['conf'] = pd.concat([
                            team_summ[['team', 'conf_game', 'win']], 
                            team_summ.groupby(['conference'])[for_cols + ['win']].rank(ascending=False, method='min').rename(columns={'win':'RANK'}),
                            team_summ.groupby(['conference'])[against_cols].rank(ascending=True, method='min'), 
                    ], axis=1).rename(columns={'conf_game':'game'})
    rankings['conf']['SET'] = 'CONF'


    ## Overall Ranking
    rankings['all'] = pd.concat([
                            team_summ[['team', 'game', 'win']], 
                            team_summ[for_cols + ['win']].rank(ascending=False, method='min').rename(columns={'win':'RANK'}),
                            team_summ[against_cols].rank(ascending=True, method='min'), 
                            ], axis=1)
    rankings['all']['SET'] = 'ALL'

    ## Concat 
    rankings = pd.concat(rankings.values())
    rankings.columns = ['TEAM', 'GP', 'W','OFF-PTS', 'OFF-YRD','RANK', 'DEF-PTS', 'DEF-YRD', 'SET']
    for col in ['GP', 'W',  'OFF-PTS', 'OFF-YRD', 'DEF-PTS', 'DEF-YRD', 'RANK']:
        rankings[col] = rankings[col].astype(int)
    rankings = rankings[['TEAM', 'SET', 'RANK', 'GP', 'W',  'OFF-PTS', 'OFF-YRD', 'DEF-PTS', 'DEF-YRD']]

    ########## AVG YARD AND SCORE ###############
    team_avg = curr_teams.groupby(['team'])[against_cols + for_cols].mean()
    team_avg = team_avg.apply(np.round)
    team_avg = team_avg.reset_index(drop=False)
    team_avg.columns = ['TEAM',  'OFF-PTS', 'OFF-YRD', 'DEF-PTS', 'DEF-YRD']

    return rankings, team_avg

################# USER STATS ########################
def user_team_stats(user, home_team, away_team, season, week, game_date, df_teams):

    from sklearn.metrics import confusion_matrix

    min_date = df_teams.loc[df_teams['season']== season].loc[df_teams['week_num'] == week].game_date.min()
    curr_teams = df_teams.loc[df_teams['team'].isin([home_team, away_team])].loc[df_teams['season']==season].loc[df_teams['game_date']<min_date].reset_index(drop=True)

    user_acc = pd.DataFrame([], columns=['Team', 'PRED W', 'PRED L', 'LAST 5'])

    count = 0
    for team, vals in curr_teams.groupby(['team'])[[user, 'winner', 'game_date']]:

        vals = vals.sort_values(['game_date'], ascending=False).head(10)

        actual = [x if x == team else 'other' for x in vals['winner']]
        user_pred = [x if x == team else 'other' for x in vals[user]]

        cm = confusion_matrix(actual, user_pred, labels=['other', team]).ravel()

        if len(cm) == 1:
            if np.unique(actual)[0] == 'other':
                tn, fp, fn, tp = len(actual),0,0,0
                if_chosen_rate = 0
                if_not_chosen = 1
            else:
                tn, fp, fn, tp = 0,0,0,len(actual)
                if_chosen_rate = 1
                if_not_chosen = 0
        else:
            tn, fp, fn, tp = cm
            if tp + fp == 0:
                if_chosen_rate = str(0) + '/' + str(0)
            else:
                if_chosen_rate = str(tp) + '/' + str(tp+fp)
            
            if fn+tn == 0:
                if_not_chosen = str(0) + '/' + str(0)
            else:
                if_not_chosen = str(tn) + '/' + str(fn+tn)

        acc = ""
        for act, pred in zip(actual[:5][::-1], user_pred[:5][::-1]):
            if act == pred:
                acc += 'T'
            else:
                acc += 'F'

        user_acc.loc[count] = [team, if_chosen_rate, if_not_chosen, acc]

        count += 1

    ## Create Table Figure

    user_stat_table = html.Div([

                html.H6("{user}'s Historical Accuracy".format(user=user)),

                html.Div("Accuracy per Team",
                    style={'fontWeight':'bold', 'textAlign':'center'}),

                dt.DataTable(
                    user_acc.to_dict('records'), 
                    [{"name": i, "id": i} for i in user_acc.columns],
                    tooltip_header =None,
                    style_cell={
                        'textAlign':'center',  
                        'border': 'none',
                        'backgroundColor': 'transparent',
                    },
                    style_header={
                        'textAlign':'center',  
                        'border': 'none',
                        'backgroundColor': 'transparent',
                        'fontWeight':'bold',
                    },
                    style_table = {
                        'border': 'none',
                        'height':'300px',
                    },
                    style_cell_conditional=[
                        {'if': {'column_id': 'index'},
                        'width': '25%',
                        'fontWeight':'bold',
                        'textAlign':'left'},
                    ],
                    css = table_css,
                ),
    ],
    style={'color':'white','whiteSpace': 'normal', 'fontFamily':"arial", 'fontSize':'11px', 'lineHeight':'1.5'})


    ## Get Final Result
    # res = [html.P(line) for line in user_acc.to_string(index=False).split('\n')]

    return user_stat_table

################# TEAM STATS ########################

def team_stats(team, df_teams, full_name, season=None, week=None, game_date=None, rankings=None, team_summ=None):

    if week==1:
        season=season-1
        week = df_teams.loc[df_teams['season']==season].week_num.max()
        game_date = df_teams.loc[df_teams['season']==season].game_date.max()

    team_df = df_teams.loc[df_teams['team']==team].loc[df_teams['game_date']<game_date].reset_index(drop=True)

    ## Get Last Few Games
    imp_cols = ['phase', 'game_date', 'week_type', 'week_num', 'against_team', 'team', 'winner', 'home_or_away',
                'team_score', 'points_overtime_total', 'against_team_score', 'against_points_overtime_total']
    last_few_games = team_df.sort_values(['game_time'], ascending=False).loc[team_df['phase']!=''].head(5)[imp_cols]

    ## Previous Three Games
    last_3_gamesL = []
    for idx, game in last_few_games.head(3).iterrows():
        if game['home_or_away'] == 'home':
            last_3_gamesL.append([ datetime.strptime(game['game_date'], "%Y-%m-%d").strftime("%m/%d/%y"),
                                "{} {} at {} {}".format(game['against_team'], 
                                                        int(game['against_team_score']+game['against_points_overtime_total']), 
                                                        int(game['team_score']+game['points_overtime_total']), 
                                                        game['team'])
                                ])
        else:
            last_3_gamesL.append([ datetime.strptime(game['game_date'], "%Y-%m-%d").strftime("%m/%d/%y"),
                                "{} {} at {} {}".format(game['team'], 
                                                        int(game['team_score']+game['points_overtime_total']), 
                                                        int(game['against_team_score']+game['against_points_overtime_total']), 
                                                        game['against_team'])
                                ])

    ## Win Streak
    win_streak = ""
    for idx, game in last_few_games.head(5).iloc[::-1].iterrows():
        if game['winner'] == game['team']:
            win_streak += 'W'
        else:
            win_streak += 'L'
    ## Get Team Week Ranking Summary
    team_week_ranking = rankings.loc[rankings['TEAM']==team].drop(['TEAM'], axis=1).set_index(['SET'])

    ## Get Team Week Summary
    team_week_summ = team_summ.loc[team_summ['TEAM']==team].drop(['TEAM'], axis=1)
    team_week_summ.index = ['ACT']
    team_week_summ = pd.concat([team_week_summ, team_week_ranking[team_week_summ.columns]])
    team_week_cols = team_week_summ.copy()
    team_week_summ = team_week_summ.reset_index(drop=False).rename(columns={'index':''})
    team_week_cols.columns = pd.MultiIndex.from_product([['OFF','DEF'], ['PTS','YRD']],names=['',''])
    team_week_cols = team_week_cols.reset_index(drop=False).rename(columns={'index':''})

    ## Get Rankings Only
    team_week_ranking = team_week_ranking[['RANK', 'GP', 'W']].reset_index(drop=False).rename(columns={'SET':''})

    ## Create Final Data Frame
    team_stats_df = pd.DataFrame(last_3_gamesL, columns=['Date', 'Game'])

    ## Create Table Figure
    team_stat_table = html.Div([

                html.H6("{team}".format(team=full_name)),

                html.Div("{div}".format(div=team_df['division'].max().replace('_', ' ')), style={'fontWeight':'bold'}),
                html.Br(),

                html.Div("Rankings" , style={'fontWeight':'bold'}),
                dt.DataTable(
                    team_week_ranking.to_dict('records'), 
                    [{"name": i, "id": i} for i in team_week_ranking.columns],
                    style_cell={
                        'border': 'none',
                        'backgroundColor': 'transparent',
                        'fontSize':'8px',
                    },
                    style_header={
                        'border': 'none',
                        'backgroundColor': 'transparent',
                        'fontWeight':'bold',
                        'fontSize':'9px',
                        'textAlign':'center',
                    },
                    style_table = {
                        'border': 'none',
                        'overflowX': 'auto',
                        'overflowY': 'auto',
                        'verticalAlign':'center',
                        'textAlign':'center',
                    },
                    style_cell_conditional=[
                        {'if': {'column_id': ''},
                            'fontWeight':'bold',
                            'textAlign':'left',
                            'width':'15%',
                            'maxWidth':'15%',
                        },
                    ],
                    css = table_css,
                ),

                html.Div("Statistics" , style={'fontWeight':'bold'}),
                dt.DataTable(
                    team_week_summ.to_dict('records'), 
                    [{"name": [x,y], "id": x+'-'+y} if x != '' else {"name": [x,y], "id":''} for x,y in team_week_cols.columns],
                    style_cell={
                        'border': 'none',
                        'backgroundColor': 'transparent',
                        'fontSize':'8px',
                        'padding':0,
                        'width':'20%',
                    },
                    style_header={
                        'border': 'none',
                        'backgroundColor': 'transparent',
                        'fontWeight':'bold',
                        'fontSize':'9px',
                        'textAlign':'center',
                    },
                    style_table = {
                        'border': 'none',
                        'overflowX': 'auto',
                        'overflowY': 'auto',
                        'verticalAlign':'center',
                        'textAlign':'center',
                    },
                    style_cell_conditional=[
                        {'if': {'column_id': ''},
                            'fontWeight':'bold',
                            'textAlign':'left',
                            'width':'15%',
                            'maxWidth':'15%',
                        },
                    ],
                    merge_duplicate_headers=True,
                    fixed_rows={ 'headers': True, 'data': 0 },
                    css = table_css,
                ),
                
                html.Div("Last 3 Games" , style={'fontWeight':'bold'}),
                dt.DataTable(
                    team_stats_df.to_dict('records'), 
                    [{"name": i, "id": i} for i in team_stats_df.columns],
                    style_cell={
                        'padding':'1px',
                        'verticalAlign':'center',
                        'border': 'none',
                        'backgroundColor': 'transparent',
                        'fontSize':'8px',
                    },
                    style_header={
                        'verticalAlign':'center',
                        'border': 'none',
                        'backgroundColor': 'transparent',
                        'fontWeight':'bold',
                        'fontSize':'9px',
                    },
                    style_table = {
                        'border': 'none',
                        'overflowX': 'auto',
                        'overflowY': 'auto',
                        'verticalAlign':'center',
                        'textAlign':'center',
                    },
                    style_cell_conditional=[
                        {'if': {'column_id': 'Date'},
                            'textAlign':'left',
                        },
                        {'if': {'column_id': 'Game'},
                            'textAlign':'center', 
                        }
                    ],
                    css = table_css,
                ),
                html.Br(),
                html.Div("Winning Streak",
                    style={'fontWeight':'bold', 'textAlign':'center'}),
                html.Div("{streak}".format(streak=win_streak),)
    ],
    style={'color':'white', 'whiteSpace': 'normal', 'fontFamily':"arial", 'fontSize':'10px'})

    return team_stat_table

################# DISPLAY TEAM  ########################

def display_team(row, home_or_away, df_teams, width, rankings, team_summ):

    if home_or_away == 'away':
        logo = 'logo_away'
        team= 'away_team'
        team_name = 'full_name_away'
        score_ot = 'visitor_points_overtime_total'
        score_col = 'away_team_score'
    else:
        logo = 'logo_home'
        team= 'home_team'
        team_name = 'full_name_home'
        score_ot = 'home_points_overtime_total'
        score_col = 'home_team_score'
    
    ## Return Layout
    return dbc.Col(
        [
        
            dbc.Row(
            [
                html.Div(
                    html.Img(
                        src='/assets/teams/{logo}'.format(logo=row[logo]), 
                        id = row[team] + '_logo',
                        style={
                            'height':logo_size,
                            # 'width':width,
                        }
                    ),style={'textAlign': 'center',}
                ),
                dbc.Tooltip(
                    team_stats(row[team], full_name=row[team_name], season=row['season'], week=row['week_num'], game_date=row['game_date'], df_teams=df_teams, rankings=rankings, team_summ=team_summ),
                    target=row[team] + '_logo',
                )
            ],
            # style=border_if_winner(team=row[team], winner=row['winner'],),
            ),

            dbc.Row([
                html.Div("{name}"\
                    .format(name=row[team_name].title(),
                    style={
                        'fontSize':team_name_size,
                        'fontWeight':'bold',
                        # 'height':'1vw',
                    })),
            ]),
            html.Br(),

        ],
        style={
            'width':width,
            'maxWidth':width,
            'minWidth':width,
            'fontSize':team_name_size,
            'height':"15vw",
            'justify':"center",
            'textAlign':'center',
            'verticalAlign':'center',
            'display': 'inline-block', 
            # 'fontSize':'80%',
        }
        )

################# DISPLAY SCORES ########################

def display_scores(season, week, user, df, user_df, df_teams, USER_LIST, USER_ABBV_DICT):

    def display_game(row, idx, rankings, team_summ):
        game_date = datetime.strptime(row['game_date'], "%Y-%m-%d").strftime("%m/%d/%Y")
        # game_time = pd.to_datetime(row['game_time']).tz_convert('US/Eastern').strftime("%I:%M %p %Z")
        game_time = pd.to_datetime(row['game_time']).tz_convert('US/Eastern').strftime("%I:%M")

        curr_game_layout =   dbc.Row([
                                ### Left Margin
                                dbc.Col(html.Div(''), style={'width':margin_padding,'maxWidth':margin_padding,'minWidth':margin_padding}),

                                ### Away Team
                                display_team(row=row, home_or_away='away', df_teams=df_teams, width=team_width,
                                            rankings=rankings, team_summ=team_summ),           

                                ## vs
                                dbc.Col([
                                    dbc.Row([
                                        html.Div(
                                            '{date}'.format(date=game_date)),
                                    ]),
                                    dbc.Row([
                                        html.Div(
                                            '{time}'.format(time=game_time)),
                                    ]),
                                    dbc.Row([
                                            html.Div(
                                            '{venue}'.format(venue=row['venue_home'],)),
                                    ]),
                                ],
                                style={
                                    'width':vs_width,
                                    'maxWidth':vs_width,
                                    # 'textAlign':'center',
                                    'height': '1em', 
                                    'marginTop':'1%',
                                    'fontSize':'1.5vw',
                                },
                                ),

                                ## Home Team
                                display_team(row=row, home_or_away='home', df_teams=df_teams, width=team_width,
                                            rankings=rankings, team_summ=team_summ),                                      
                                

                                dbc.Col([

                                    ## Predictions
                                    html.Div([

                                        dbc.Row([

                                            dbc.Col([

                                                html.Div(USER_ABBV_DICT[user] + '', style={'fontWeight':'bold'}), 
                                                html.Div(row[user],
                                                    style=border_if_winner(team=row[user], winner=row['winner'])),
                                            ], 
                                            id='game_{game}_user_{user}'.format(game=idx, user=user),
                                            # style={'width':'{}%'.format((100)//(len(USER_LIST))*2)}
                                            ) for user in USER_LIST[user_vals*2:user_vals*2+2]
                                        ],
                                        style={
                                        },
                                        ) for user_vals in np.arange(len(USER_LIST)//2 + len(USER_LIST)%2)
                                    
                                    ]
                                ),
                                    html.Div([
                                        dbc.Tooltip(
                                            user_team_stats(user=user, home_team=row['home_team'], 
                                                away_team=row['away_team'], season=season, week=week, game_date=row['game_date'], df_teams=df_teams),
                                            target='game_{game}_user_{user}'.format(game=idx, user=user),
                                            style={
                                                # "fontSize": "3.5vw",
                                                'minWidth': '700px',
                                                # 'width': '500px',
                                                # 'height': '10vw',
                                            }
                                        ) for user in USER_LIST
                                    ],
                                    )
                                ],
                                style={
                                    'display': 'inline-block', 
                                    'width':preds_width, 'maxWidth':preds_width,
                                    'textAlign':'center', 
                                    'justify':"center", 
                                    'verticalAlign':'center',
                                    'fontSize':'1.5vw',
                                    'minWidth':min_preds_width,
                                },
                                ),

                                # dbc.Col(html.Div(''), style={'width':margin_padding, 'maxWidth':margin_padding,'minWidth':margin_padding}),

                            ], 
                            style={
                                # 'height':'10%',
                                # 'display': 'inline-block', 
                                'justify':"center",
                                'textAlign':'center',
                                'verticalAlign':'center',
                                # 'width':'95%', 
                            })
        return curr_game_layout

    def get_current_game_info(row):
        curr_game_info_layout = [
                                    dbc.Row([
                                        dbc.Col(html.Div(''), style={'width':margin_padding,'maxWidth':margin_padding,'minWidth':margin_padding}),
                                        dbc.Col([
                                            html.H4(
                                                "{score}".format(score=int(row['away_team_score'] + row['visitor_points_overtime_total'])),
                                            style={
                                                'fontSize':score_font_size,
                                            }
                                            ),
                                        ], style={'justify':"center", 'textAlign':'center','verticalAlign':'center','width':team_width,'maxWidth':team_width,'minWidth':min_team_width}),

                                        dbc.Col(html.Div(""), style= {'width':vs_width,'maxWidth':vs_width,'minWidth':vs_width,}),

                                        dbc.Col([
                                            html.H4(
                                                "{score}".format(score=int(row['home_team_score'] + row['home_points_overtime_total'])),
                                            style={
                                                'fontSize':score_font_size,
                                            },
                                            ),
                                        ], style={'justify':"center", 'textAlign':'center','verticalAlign':'center','width':team_width,'maxWidth':team_width,'minWidth':min_team_width}),

                                        dbc.Col(html.Div(''), 
                                        style={
                                            'width':preds_width,
                                            'maxWidth':preds_width,
                                            'minWidth':min_preds_width,
                                        }),
                                    ],
                                    style={
                                        'justify':"center",
                                        'textAlign':'center',
                                        'verticalAlign':'center',
                                        # 'width':'95%', 
                                    }),
                                 ]
        return curr_game_info_layout

    def display_upcoming_week(scores, season=season, week=week, user_df=user_df, df_teams=df_teams, USER_LIST=USER_LIST):
        
        # Start Layout
        score_layout = end_row()

        ## Get Rankings
        rankings, team_summ = team_rankings(df_teams, week=week, season=season)
        
        for idx, row in scores.iterrows():
            
            curr_game_layout = display_game(row=row, idx=idx, rankings=rankings, team_summ=team_summ)

            score_layout = score_layout + [curr_game_layout] + end_row()

        return score_layout

    def display_historical_week(scores, season=season, week=week, user_df=user_df, df_teams=df_teams, USER_LIST=USER_LIST):

        # Start Layout
        score_layout = end_row()

        ## Get Rankings
        rankings, team_summ = team_rankings(df_teams, week=week, season=season)
        
        for idx, row in scores.iterrows():
            
            curr_game_layout = display_game(row=row, idx=idx, rankings=rankings, team_summ=team_summ)
                                
            curr_game_info_layout = get_current_game_info(row=row)

            score_layout = score_layout + [curr_game_layout] + curr_game_info_layout + end_row()

        return score_layout

    ## Get Subsets of Scores
    curr_scores = df.loc[df['week_num']==week].loc[df['season']==season].reset_index(drop=True)
    min_date_week = curr_scores.game_date.min()

    ## Get Current Time
    today = np.datetime64('today')

    ## Check if Week has results or is upcoming
    if today > pd.to_datetime(min_date_week):
        layout = display_historical_week(scores=curr_scores, user_df=user_df, USER_LIST=USER_LIST)
    else:
        layout = display_upcoming_week(scores=curr_scores, user_df=user_df, USER_LIST=USER_LIST)  

    return layout


####################################################
################ DEFINE DEFAULT LAYOUT #############
####################################################

# Create App
layout = \
    html.Div(id = 'parent-home', children = [
    
        # Hidden div inside the app that stores the intermediate value
        dcc.Store(id="current_scores"),  # this is the store that holds the data
        html.Div(id="onload"),  # this div is used to trigger the current scores
        html.Div(id="log"),
        
    ])

# ####################################################
# ################ DEFINE PAGE LAYOUT ################
# ####################################################
 
# layout = scores_page.display_scores(season=season, 
#                                             week=week,
#                                             user='Emilio',
#                                             df=df.copy(),
#                                             df_teams=df_teams.copy(),
#                                             user_df=user_df.copy(),
#                                             USER_LIST=USER_LIST,
#                                             USER_ABBV_DICT=USER_ABBV_DICT)