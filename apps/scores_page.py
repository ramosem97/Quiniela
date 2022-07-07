### Imports
import pandas as pd
import numpy as np

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
# from app import df, USER_LIST, user_df, df_teams


########## building score tables ################
def get_curr_score(week, season, user_df, USER_LIST):
    curr_user = user_df.loc[((user_df.season==season) & (user_df.week_num==week))]

    curr_user = pd.concat([
                curr_user[[x+'_correct' for x in USER_LIST]].rename(columns={x+'_correct':x for x in USER_LIST}).T,
                curr_user[[x+'_score' for x in USER_LIST]].rename(columns={x+'_score':x for x in USER_LIST}).T,
            ], axis=1)
    curr_user.columns = ['Week Score', 'Season Score']
    curr_user = curr_user.T.reset_index(drop=False)
    curr_user = curr_user.rename(columns={'index':''})

    ### Create Table Figure
    user_table = dt.DataTable(
        curr_user.to_dict('records'), [{"name": i, "id": i} for i in curr_user.columns],
        style_cell={
            'textAlign': 'left', 
            'padding': '5px',
            'fontSize':'70%',
            'width': 'auto',
            'height': 'auto',
            'maxWidth': 0,
            'textAlign':'center',  
            'border': 'none'  
        },
        style_header={
            'backgroundColor': 'transparent',
            'fontWeight': 'bold',
            'fontSize':'70%',
            'border': 'none',
        },
        style_table = {
            'border': 'none',
            'overflowX': 'auto'
        },
        style_cell_conditional=[
            {'if': {'column_id': ''},
            'width': '35%'},
        ],
    )
    return [
                dbc.Row(html.H3('Season {season} Week {week} Scoreboard'.format(season=season, week=week))),
                dbc.Row([user_table], 
                    style={'width':'60%', 'textAlign':'center', 'display':'inline-block'}
                ),
                html.Br(),
                html.Br(),
            ]

################ BORDER IF WINNER #############
def border_if_winner(team, winner, final=True):
    
    if final == True:
        if team == winner:
            return {'border':"2px MediumSeaGreen solid", 'borderRadius': '60%',
                     
                    }
        elif winner == 'TIE':
            return {'border':"2px GoldenRod solid", 'borderRadius': '60%',
                    
                }
        else:
            return {}
    else:
        return {}

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

####################################################
################# HELPER FUNCTIONS #################
####################################################

def team_stats(team, df_teams, season=None, week=None):

    loc = 1
    if week==1:
        season=season-1
        week = df_teams.loc[df_teams['season']==season].week_num.max()
        loc = 0

    team_df = df_teams.loc[df_teams['team']==team].reset_index(drop=True)

    if len(team_df) > 0:
        team_df = team_df.loc[team_df['season']==season].reset_index(drop=True)

    if len(team_df) > 0:
        team_df = team_df.loc[team_df['week_num']<=week].reset_index(drop=True)

    ## Previous Three Games
    last_3_games = team_df.sort_values(['game_time'], ascending=False).iloc[loc:].loc[team_df['phase']!=''].head(3)[['phase', 'week_type', 'week_num', 'against_team', 'team', 'team_score', 'against_team_score', 'points_overtime_total','against_points_overtime_total', 'home_or_away']]
    
    last_3_gamesL = [html.P('Last Games:')]
    for idx, game in last_3_games.iterrows():
        if game['home_or_away'] == 'home':
            last_3_gamesL.append(html.P("{} {} - Week {} ".format(season, game['week_type'], str(game['week_num']))  + \
                game['against_team'] + \
                '\t {} at {} '.format(int(game['against_team_score']+game['against_points_overtime_total']), 
                int(game['team_score']+game['points_overtime_total'])) + game['team']))
        else:
            last_3_gamesL.append(html.P("{} {} - Week {} ".format(season, game['week_type'], str(game['week_num'])) + \
                game['team'] + \
                '\t {} at {} '.format(int(game['team_score']+game['points_overtime_total']), 
                int(game['against_team_score']+game['against_points_overtime_total'])) + game['against_team']))

    ## Win Streak
    last_5_games = team_df.sort_values(['game_time'], ascending=False).iloc[loc:].loc[team_df['phase']!=''].head(5)[['phase', 'against_team', 'team', 'winner', 'home_or_away']]
    win_streak = "Streak: "
    for idx, game in last_5_games.iterrows():
        if game['winner'] == game['team']:
            win_streak += 'W'
        else:
            win_streak += 'L'

    ## Off. Yard Rank
    ## Def. Yard Rank

    # return team_df.groupby(['team']).sum().reset_index(drop=False).drop(['season', 'week', 'week_num', 'week_type_ord',
    #                                                                     'week_quin'], axis=1)

    return last_3_gamesL +   [html.P(win_streak)]

def display_team(row, home_or_away, df_teams):

    if home_or_away == 'away':
        team= 'away_team'
        team_name = 'full_name_away'
    else:
        team= 'home_team'
        team_name = 'full_name_home'

    ## Return Layout
    return dbc.Col(
        [
        
            dbc.Row(
            [
                html.Img(
                    src='/assets/teams/{team}_logo.webp'.format(team=row[team].upper()), 
                    id = row[team] + '_logo',
                    style={
                        # 'height':"50%",
                        # 'width':"50%",
                        # 'verticalAlign':'center',
                        # 'justify':"center",
                        # 'textAlign':'center',
                    }
                ),
                dbc.Tooltip(
                    team_stats(row[team], season=row['season'], week=row['week_num'], df_teams=df_teams),
                    target=row[team] + '_logo',
                )
            ],
            style=border_if_winner(team=row[team], winner=row['winner'],),
            ),

            dbc.Row([
                html.H5("{name}"\
                    .format(name=row[team_name].title())),
            ]),

        ],
        style={
            'width':'15%',
            # 'height':"5px",
            # 'justify':"center",
            # 'textAlign':'center',
            # 'verticalAlign':'center',
            # 'display': 'inline-block', 
            # 'fontSize':'80%',
        }
        )


def display_scores(season, week, user, df, user_df, df_teams, USER_LIST):

    def display_upcoming_week(scores, season=season, week=week, user_df=user_df, df_teams=df_teams, USER_LIST=USER_LIST):

        score_layout = [dbc.Row([

                            ### Left Margin
                            dbc.Col(html.Div(''), style={'width':'5%'}),

                            ## Away Team
                            dbc.Col(html.H4("Away"), 
                                style={'width':'15%',
                                    'textAlign':'center', 
                                    'justify':"center",
                                    'verticalAlign':'center',
                                    }
                                ),


                            ## vs
                            dbc.Col(html.Div(""),
                                style= {'width':'5%'}
                            ),

                            ## Home Team
                            dbc.Col(html.H4("Home"), 
                                style={'width':'15%',
                                    'textAlign':'center', 
                                    'justify':"center",
                                    'verticalAlign':'center'
                                    }
                                ),
                            
                            dbc.Col(html.Div(''), style={'width':'1%'}),


                            dbc.Col([

                                ## Predictions
                                html.Div([
                                    html.H4("Predictions"),
                                ]),
                            ],
                            style={
                                'width':'10%',
                                'textAlign':'center', 
                                'justify':"center", 
                                'verticalAlign':'center',
                            }
                            ),

                            
                            ### Right Margin
                            dbc.Col(html.Div(''), style={'width':'5%'}),

                        ],
                        style={
                            'width':'100%',
                            'textAlign':'center', 
                            'justify':"center", 
                            'verticalAlign':'center',
                        },
                        ),
                        
                    ]
        
        for idx, row in scores.iterrows():
            
            curr_game_layout =   dbc.Row([
                                    ### Left Margin
                                    dbc.Col(html.Div(''), style={'width':'5%'}),

                                    ### Away Team
                                    display_team(row=row, home_or_away='away', df_teams=df_teams),

                                    ## vs
                                    dbc.Col([
                                        html.H6("VS"),
                                    ],
                                    style={
                                        'fontWeight':'bold',
                                        'width':'5%',
                                        # 'textAlign':'center',
                                        # 'display': 'inline-block', 
                                        'marginTop':'6%',
                                    },
                                    ),

                                    ## Home Team
                                    display_team(row=row, home_or_away='home', df_teams=df_teams),                              
                                    
                                    dbc.Col(html.Div(''), style={'width':'1%'}),

                                    dbc.Col([

                                        ## Predictions
                                        html.Div([

                                            dbc.Row([

                                                dbc.Col([

                                                    html.Div(user + '', style={'fontWeight':'bold'}), 
                                                    html.Div(row[user],
                                                        style=border_if_winner(team=row[user], winner=row['winner']))
                                                ], 
                                                style={'width':'{}%'.format((100)//len(USER_LIST))*2}
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
                                        'width':'10%',
                                        'textAlign':'center', 
                                        'justify':"center", 
                                        'verticalAlign':'center',
                                        'fontSize':'80%',
                                    },
                                    ),

                                    dbc.Col(html.Div(''), style={'width':'5%'}),

                                ], 
                                style={
                                    # 'leftMargin':'5%',
                                    # 'rightMargin':'1%',
                                    # 'height':'10%',
                                    # 'display': 'inline-block', 
                                    'justify':"center",
                                    'textAlign':'center',
                                    'verticalAlign':'center',
                                    'width':'100%', 
                                })

            curr_game_info_layout = [
                                    dbc.Row([
                                        dbc.Col(html.Div(''), style={'width':'5%'}),
                                        dbc.Col(html.Div(''), style={'width':'15%'}),
                                        dbc.Col([
                                            dbc.Row([
                                                html.Div(
                                                    '{date}'.format(date=str(row['game_date']).replace('-', '/'))),
                                            ]),
                                            dbc.Row([
                                                    html.Div(
                                                    '{venue}'.format(venue=row['venue_home'],)),
                                            ]),
                                        ], style={'width':'15%','textAlign':'center','verticalAlign':'center', 'display':'inline-block'}),
                                        dbc.Col(html.Div(''), style={'width':'15%'}),
                                        dbc.Col(html.Div(''), style={'width':'1%'}),
                                        dbc.Col(html.Div(''), style={'width':'10%'}),
                                        dbc.Col(html.Div(''), style={'width':'5%'}),
                                    ],
                                    style={
                                        'justify':"center",
                                        'textAlign':'center',
                                        'verticalAlign':'center', 
                                        'width':'100%',
                                    }),
                                 ]

            score_layout = score_layout + [curr_game_layout] + curr_game_info_layout + [html.Br()]

        return score_layout

    def display_historical_week(scores, season=season, week=week, user_df=user_df, df_teams=df_teams, USER_LIST=USER_LIST):

        score_layout = [dbc.Row([

                            ### Left Margin
                            dbc.Col(html.Div(''), style={'width':'5%'}),

                            ## Away Team
                            dbc.Col(html.H4("Away"), 
                                style={'width':'15%',
                                    'textAlign':'center', 
                                    'justify':"center",
                                    'verticalAlign':'center',
                                    }
                                ),

                            dbc.Col(html.Div(''), style={'width':'5%'}),


                            ## vs
                            dbc.Col(html.Div(""),
                                style= {'width':'5%'}
                            ),

                            dbc.Col(html.Div(''), style={'width':'5%'}),

                            ## Home Team
                            dbc.Col(html.H4("Home"), 
                                style={'width':'15%',
                                    'textAlign':'center', 
                                    'justify':"center",
                                    'verticalAlign':'center'
                                    }
                                ),
                            
                            dbc.Col(html.Div(''), style={'width':'1%'}),


                            dbc.Col([

                                ## Predictions
                                html.Div([
                                    html.H4("Scores"),
                                ]),
                            ],
                            style={
                                'width':'10%',
                                'textAlign':'center', 
                                'justify':"center", 
                                'verticalAlign':'center',
                            }
                            ),

                            
                            ### Right Margin
                            dbc.Col(html.Div(''), style={'width':'5%'}),

                        ],
                        style={
                            'width':'100%',
                            'textAlign':'center', 
                            'justify':"center", 
                            'verticalAlign':'center',
                        },
                        ),
                        
                    ]
        
        for idx, row in scores.iterrows():
            
            curr_game_layout =   dbc.Row([
                                    ### Left Margin
                                    dbc.Col(html.Div(''), style={'width':'5%'}),

                                    ### Away Team
                                    display_team(row=row, home_or_away='away', df_teams=df_teams),

                                    ## Away Team Score
                                    dbc.Col([
                                        html.H4("{score}".format(score=int(row['away_team_score'] + row['visitor_points_overtime_total']))),
                                    ],
                                    style={
                                        'fontWeight':'bold',
                                        'width':'5%',
                                        # 'textAlign':'center',
                                        # 'display': 'inline-block', 
                                        'marginTop':'2%',
                                    },
                                    ),

                                    ## vs
                                    dbc.Col([
                                        html.H6("VS"),
                                    ],
                                    style={
                                        'fontWeight':'bold',
                                        'width':'5%',
                                        # 'textAlign':'center',
                                        # 'display': 'inline-block', 
                                        'marginTop':'6%',
                                    },
                                    ),

                                    ## Home Team Score
                                    dbc.Col([
                                        html.H4("{score}".format(score=int(row['home_team_score'] + row['home_points_overtime_total']))),
                                    ],
                                    style={
                                        'fontWeight':'bold',
                                        'width':'5%',
                                        # 'textAlign':'center',
                                        # 'display': 'inline-block', 
                                        'marginTop':'2%',
                                    },
                                    ),

                                    ## Home Team
                                    display_team(row=row, home_or_away='home', df_teams=df_teams),                              
                                    
                                    dbc.Col(html.Div(''), style={'width':'1%'}),

                                    dbc.Col([

                                        ## Predictions
                                        html.Div([

                                            dbc.Row([

                                                dbc.Col([

                                                    html.Div(user + '', style={'fontWeight':'bold'}), 
                                                    html.Div(row[user],
                                                        style=border_if_winner(team=row[user], winner=row['winner']))
                                                ], 
                                                style={'width':'{}%'.format((100)//len(USER_LIST))*2}
                                                ) for user in USER_LIST[user_vals*2:user_vals*2+2]
                                            ],
                                            style={
                                            },
                                            ) for user_vals in np.arange(len(USER_LIST)//2 + len(USER_LIST)%2)
                                        ],
                                        )
                                    ],
                                    style={
                                        
                                        'display': 'inline-block', 
                                        'width':'10%',
                                        'textAlign':'center', 
                                        'justify':"center", 
                                        'verticalAlign':'center',
                                        'fontSize':'80%',
                                    },
                                    ),

                                    dbc.Col(html.Div(''), style={'width':'5%'}),

                                ], 
                                style={
                                    # 'leftMargin':'5%',
                                    # 'rightMargin':'1%',
                                    # 'height':'10%',
                                    # 'display': 'inline-block', 
                                    'justify':"center",
                                    'textAlign':'center',
                                    'verticalAlign':'center',
                                    'width':'100%', 
                                })

                                
            curr_game_info_layout = [
                                    dbc.Row([
                                        dbc.Col(html.Div(''), style={'width':'5%'}),
                                        dbc.Col(html.Div(''), style={'width':'15%'}),
                                         dbc.Col(html.Div(''), style={'width':'5%'}),

                                        dbc.Col([
                                            dbc.Row([
                                                html.Div(
                                                    '{date}'.format(date=str(row['game_date']).replace('-', '/'))),
                                            ]),
                                            dbc.Row([
                                                    html.Div(
                                                    '{venue}'.format(venue=row['venue_home'],)),
                                            ]),
                                        ], style={'width':'5%','textAlign':'center','verticalAlign':'center', 'display':'inline-block'}),    
                                        dbc.Col(html.Div(''), style={'width':'5%'}),
                                        dbc.Col(html.Div(''), style={'width':'15%'}),
                                        dbc.Col(html.Div(''), style={'width':'1%'}),
                                        dbc.Col(html.Div(''), style={'width':'10%'}),
                                        dbc.Col(html.Div(''), style={'width':'5%'}),
                                    ],
                                    style={
                                        'justify':"center",
                                        'textAlign':'center',
                                        'verticalAlign':'center',
                                        'width':'100%',
                                    }),
                                 ]
            score_layout = score_layout + [curr_game_layout] + curr_game_info_layout + [html.Br()]

        return score_layout

    ## Get Subsets of Scores
    curr_scores = df.loc[df['week_num']==week].loc[df['season']==season].reset_index(drop=True)
    min_date_week = curr_scores.game_date.min()

    ## Get Current Time
    today = np.datetime64('today')

    ## Check if Week has results or is upcoming
    if today > pd.to_datetime(min_date_week):
        layout = get_curr_score(season=season, week=week, user_df=user_df, USER_LIST=USER_LIST) + display_historical_week(scores=curr_scores, user_df=user_df, USER_LIST=USER_LIST)
    else:
        layout = get_curr_score(season=season, week=week, user_df=user_df, USER_LIST=USER_LIST)   + display_upcoming_week(scores=curr_scores, user_df=user_df, USER_LIST=USER_LIST)   

    return layout

# @app.callback(Output("parent", "children"), Input("plants", "data"))
# def print_df(plants):
#     return home_layout(pd.read_json(plants))  # do something with the data