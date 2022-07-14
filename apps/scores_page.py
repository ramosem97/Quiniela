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

########## building score tables ################
def get_curr_score(week, season, user_df, USER_LIST, USER_ABBV_DICT):
    curr_user = user_df.loc[((user_df.season==season) & (user_df.week_num==week))]

    curr_user = pd.concat([
                curr_user[[x+'_correct' for x in USER_LIST]].rename(columns={x+'_correct':x for x in USER_LIST}).T,
                curr_user[[x+'_score' for x in USER_LIST]].rename(columns={x+'_score':x for x in USER_LIST}).T,
            ], axis=1)
    curr_user.columns = ['Week', 'Season']
    curr_user = curr_user.T.reset_index(drop=False)
    curr_user = curr_user.rename(columns={'index':''}).rename(columns=USER_ABBV_DICT)

    ### Create Table Figure
    user_table = dt.DataTable(
        curr_user.to_dict('records'), [{"name": i, "id": i} for i in curr_user.columns],
        fixed_rows={'headers': True},
        style_cell={
            'padding': 0,
            'textAlign':'center',  
            # 'minHeight': .1, 'maxHeight': .1, 'height': .1,
            'border': 'none',
            'backgroundColor': 'transparent',
            'minWidth': 5, 'maxWidth': 5, 'width': 5,
        },
        style_header={
            'padding': 0,
            'textAlign': 'center', 
            # 'height': .5, 
            'backgroundColor': 'transparent',
            'fontWeight': 'bold',
            'border': 'none',
        },
        style_table = {
            # 'fontSize':dt_table_font_size,
            'border': 'none',
            'overflowX': 'auto',
            'overflowY': 'auto',
        },
        style_cell_conditional=[
            {'if': {'column_id': ''},
                'width': '35%',
                'fontWeight':'bold',
                'textAlign':'left'\
            },
        ],
    )
    return [
                    
                html.Div([user_table], 
                    style={
                        # 'display':'flex',
                        'alignItems':"center",
                        # 'width':'80%', 
                        'height':'100px',
                        'textAlign':'center', 
                        'justify':'center', 
                        # 'display':'inline-block', 
                        'padding':'4px',
                        'fontFamily':"arial",
                    }
                ),
                html.Br(),
            ] + end_row()

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
    rankings.columns = ['TEAM', 'GP', 'W', 'OPts', 'OYrds','RANK', 'DPts', 'DYrds', 'SET']
    for col in ['GP', 'W', 'OPts', 'OYrds', 'DPts', 'DYrds', 'RANK']:
        rankings[col] = rankings[col].astype(int)
    rankings = rankings[['TEAM', 'SET', 'RANK', 'GP', 'W', 'OPts', 'OYrds', 'DPts', 'DYrds']]

    ########## AVG YARD AND SCORE ###############
    team_avg = curr_teams.groupby(['team'])[against_cols + for_cols].mean()
    team_avg = team_avg.apply(np.round)
    team_avg = team_avg.reset_index(drop=False)
    team_avg.columns = ['TEAM', 'OPts', 'OYrds', 'DPts', 'DYrds']

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
                    },
                    style_cell_conditional=[
                        {'if': {'column_id': 'index'},
                        'width': '25%',
                        'fontWeight':'bold',
                        'textAlign':'left'},
                    ],
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
    team_week_summ = pd.concat([team_week_summ, team_week_ranking[team_week_summ.columns]]).reset_index(drop=False).rename(columns={'index':''})
    
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
                        'padding':'2px',
                        'verticalAlign':'center',
                        'border': 'none',
                        'backgroundColor': 'transparent',
                        'lineHeight':'1px',
                    },
                    style_header={
                        'padding':'.5px',
                        'verticalAlign':'center',
                        'border': 'none',
                        'backgroundColor': 'transparent',
                        'fontWeight':'bold',
                        'fontSize':'12px',
                    },
                    style_table = {
                        'verticalAlign':'center',
                        'border': 'none',
                        'padding':'0px',
                    },
                    style_cell_conditional=[
                        {'if': {'column_id': ''},
                            'width': '20%',
                            'maxWidth': '15%',
                            'fontWeight':'bold',
                            'textAlign':'left',
                            'borderRight':'.2px solid white'},
                    ],
                ),

                html.Div("Statistics" , style={'fontWeight':'bold'}),
                dt.DataTable(
                    team_week_summ.to_dict('records'), 
                    [{"name": i, "id": i} for i in team_week_summ.columns],
                    style_cell={
                        'padding':'2px',
                        'verticalAlign':'center',
                        'border': 'none',
                        'backgroundColor': 'transparent',
                        'lineHeight':'1px',
                        'fontSize':'8px',
                    },
                    style_header={
                        'padding':'.5px',
                        'verticalAlign':'center',
                        'border': 'none',
                        'backgroundColor': 'transparent',
                        'fontWeight':'bold',
                        'fontSize':'9px',
                    },
                    style_table = {
                        'verticalAlign':'center',
                        'border': 'none',
                        'padding':'0px',
                    },
                    style_cell_conditional=[
                        {'if': {'column_id': ''},
                            'width': '20%',
                            'maxWidth': '15%',
                            'fontWeight':'bold',
                            'textAlign':'left',
                            'borderRight':'.2px solid white'},
                    ],
                ),
                
                html.Div("Last 3 Games" , style={'fontWeight':'bold'}),
                dt.DataTable(
                    team_stats_df.to_dict('records'), 
                    [{"name": i, "id": i} for i in team_stats_df.columns],
                    style_cell={
                        'padding':'2px',
                        'verticalAlign':'center',
                        'border': 'none',
                        'backgroundColor': 'transparent',
                        'lineHeight':'1px',
                    },
                    style_header={
                        'padding':'.5px',
                        'verticalAlign':'center',
                        'border': 'none',
                        'backgroundColor': 'transparent',
                        'fontWeight':'bold',
                        'fontSize':'12px',
                    },
                    style_table = {
                        'verticalAlign':'center',
                        'border': 'none',
                        'padding':'0px',
                    },
                    style_cell_conditional=[
                        {'if': {'column_id': 'Date'},
                            'width': '20%',
                            'maxWidth': '15%',
                            # 'fontWeight':'bold',
                            'textAlign':'left',
                            'borderRight':'.2px solid white'},
                        {'if': {'column_id': 'Game'},
                            'textAlign':'center', 
                        }
                    ],
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

    def score_head_layout():
        score_layout = [dbc.Row([

                            ### Left Margin
                            dbc.Col(html.Div(''), style={'width':margin_padding,'maxWidth':margin_padding,'minWidth':margin_padding}),

                            ## Away Team
                            dbc.Col(html.H6("Away",
                                    # style={'fontSize':header_size}
                                    ), 
                                style={'width':team_width,'maxWidth':team_width,
                                    'fontWeight':'bold',
                                    'textAlign':'center', 
                                    'justify':"center",
                                    'verticalAlign':'center',
                                    'minWidth':team_width,
                                    }
                                ),

                            ## vs
                            dbc.Col(html.Div(""),
                                style= {'width':vs_width,'maxWidth':vs_width,'minWidth':vs_width,}
                            ),

                            ## Home Team
                            dbc.Col(html.H6("Home",
                                    # style={'fontSize':header_size}
                                    ), 
                                style={'width':team_width,'maxWidth':team_width,
                                    'fontWeight':'bold',
                                    'textAlign':'center', 
                                    'justify':"center",
                                    'verticalAlign':'center',
                                    'minWidth':team_width,
                                    }
                                ),

                            dbc.Col([

                                ## Predictions
                                html.H6("Predictions",
                                # style={'fontSize':header_size}
                                ),
                            ],
                            style={
                                'width':preds_width,'maxWidth':preds_width,\
                                'fontWeight':'bold',
                                'minWidth':min_preds_width,
                                'textAlign':'center', 
                                'justify':"center", 
                                'verticalAlign':'center',
                            }
                            ),

                            
                            ### Right Margin
                            # dbc.Col(html.Div(''), style={'width':margin_padding,'maxWidth':margin_padding,'minWidth':margin_padding}),

                        ],
                        style={
                            'width':'95%',
                            'textAlign':'center', 
                            'justify':"center", 
                            'verticalAlign':'center',
                        },
                        ),
                        
                    ]

        return score_layout + end_row()


    def display_upcoming_week(scores, season=season, week=week, user_df=user_df, df_teams=df_teams, USER_LIST=USER_LIST):
        
        score_layout = score_head_layout()

        ## Get Previous Games
        min_date = scores.game_date.min()
        curr_df_teams = df_teams.loc[df_teams['game_date'] < min_date].reset_index(drop=True)

        ## Get Rankings
        rankings, team_summ = team_rankings(df_teams, week=week, season=season)
        
        for idx, row in scores.iterrows():
            
            game_date = datetime.strptime(row['game_date'], "%Y-%m-%d").strftime("%m/%d/%Y")
            # game_time = pd.to_datetime(row['game_time']).tz_convert('US/Eastern').strftime("%I:%M %p %Z")
            game_time = pd.to_datetime(row['game_time']).tz_convert('US/Eastern').strftime("%I:%M")

            curr_game_layout =   dbc.Row([
                                    ### Left Margin
                                    dbc.Col(html.Div(''), style={'width':margin_padding,'maxWidth':margin_padding,'minWidth':margin_padding,}),

                                    ### Away Team
                                    display_team(row=row, home_or_away='away', df_teams=curr_df_teams, width=team_width,
                                                rankings=rankings, team_summ=team_summ),

                                    ### Left Margin
                                    # dbc.Col(html.Div(''), style={'width':margin_padding,'maxWidth':margin_padding,'minWidth':margin_padding}),

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
                                        'minWidth':vs_width,
                                        # 'textAlign':'center',
                                        'height': '1em', 
                                        'marginTop':'2%',
                                        'fontSize':'1.5vw',
                                    },
                                    ),
                                    
                                    ### Left Margin
                                    # dbc.Col(html.Div(''), style={'width':margin_padding,'maxWidth':margin_padding,'minWidth':margin_padding}),

                                    ## Home Team
                                    display_team(row=row, home_or_away='home', df_teams=curr_df_teams, width=team_width,
                                                rankings=rankings, team_summ=team_summ),                              
                                    
                                    dbc.Col([

                                        ## Predictions
                                        html.Div([

                                            dbc.Row([

                                                dbc.Col([

                                                    html.Div(USER_ABBV_DICT[user] + '', style={'fontWeight':'bold'}), 
                                                    html.Div(row[user],
                                                        style=border_if_winner(team=row[user], winner=row['winner']))
                                                ], 
                                                style={'width':'.5vw'}
                                                ) for user in USER_LIST[user_vals*2:user_vals*2+2] if pd.notnull(row[user])
                                            ],
                                            style={
                                            },
                                            ) for user_vals in np.arange(len(USER_LIST)//2 + len(USER_LIST)%2)
                                        ],
                                        )
                                    ],
                                    style={
                                        
                                        'display': 'inline-block', 
                                        'width':preds_width,
                                        'maxWidth':preds_width,
                                        'textAlign':'center', 
                                        'justify':"center", 
                                        'verticalAlign':'center',
                                        'fontSize':'2vw',
                                        'minWidth':min_preds_width,
                                    },
                                    ),

                                    # dbc.Col(html.Div(''), style={'width':margin_padding,'maxWidth':margin_padding,'minWidth':margin_padding}),

                                ], 
                                style={
                                    # 'leftMargin':'5%',
                                    # 'rightMargin':'1%',
                                    # 'height':'10%',
                                    # 'display': 'inline-block', 
                                    'justify':"center",
                                    'textAlign':'center',
                                    'verticalAlign':'center',
                                    'width':'95%', 
                                    'padding':'2%',
                                })

            score_layout = score_layout + [curr_game_layout] + end_row()

        return score_layout

    def display_historical_week(scores, season=season, week=week, user_df=user_df, df_teams=df_teams, USER_LIST=USER_LIST):

        score_layout = score_head_layout()

        ## Get Previous Games
        min_date = scores.game_date.min()
        curr_df_teams = df_teams.loc[df_teams['game_date'] < min_date].reset_index(drop=True)
        
        
        ## Get Rankings
        rankings, team_summ = team_rankings(df_teams, week=week, season=season)

        for idx, row in scores.iterrows():
            
            game_date = datetime.strptime(row['game_date'], "%Y-%m-%d").strftime("%m/%d/%Y")
            # game_time = pd.to_datetime(row['game_time']).tz_convert('US/Eastern').strftime("%I:%M %p %Z")
            game_time = pd.to_datetime(row['game_time']).tz_convert('US/Eastern').strftime("%I:%M")

            curr_game_layout =   dbc.Row([
                                    ### Left Margin
                                    dbc.Col(html.Div(''), style={'width':margin_padding,'maxWidth':margin_padding,'minWidth':margin_padding}),

                                    ### Away Team
                                    display_team(row=row, home_or_away='away', df_teams=curr_df_teams, width=team_width,
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
                                    display_team(row=row, home_or_away='home', df_teams=curr_df_teams, width=team_width,
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
                                    'width':'95%', 
                                })

                                
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
                                        'width':'95%', 
                                    }),
                                 ]

            score_layout = score_layout + [curr_game_layout] + curr_game_info_layout + end_row()

        return score_layout

    ## Get Subsets of Scores
    curr_scores = df.loc[df['week_num']==week].loc[df['season']==season].reset_index(drop=True)
    min_date_week = curr_scores.game_date.min()

    ## Get Current Time
    today = np.datetime64('today')

    ## Check if Week has results or is upcoming
    if today > pd.to_datetime(min_date_week):
        layout = get_curr_score(season=season, week=week, user_df=user_df, USER_LIST=USER_LIST, USER_ABBV_DICT=USER_ABBV_DICT) + display_historical_week(scores=curr_scores, user_df=user_df, USER_LIST=USER_LIST)
    else:
        layout = get_curr_score(season=season, week=week, user_df=user_df, USER_LIST=USER_LIST, USER_ABBV_DICT=USER_ABBV_DICT)   + display_upcoming_week(scores=curr_scores, user_df=user_df, USER_LIST=USER_LIST)   

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