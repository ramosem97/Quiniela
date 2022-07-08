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
# from app import df, USER_LIST, user_df, df_teams

team_width = '25%'
min_team_width = '25%'
vs_width = '12%'
scores_width = '1%'
preds_width = '25%'

margin_padding = '.5px'
header_size = '4vw'
pred_font_size = '2vw'
score_font_size = '4vw'
dt_table_font_size = '3vw'

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
            'fontSize':dt_table_font_size,
            'width': 'auto',
            'height': 'auto',
            'maxWidth': 0,
            'textAlign':'center',  
            'border': 'none'  
        },
        style_header={
            'backgroundColor': 'transparent',
            'fontWeight': 'bold',
            'fontSize':dt_table_font_size,
            'border': 'none',
        },
        style_table = {
            'border': 'none',
            'overflowX': 'auto'
        },
        style_cell_conditional=[
            {'if': {'column_id': ''},
            'width': '35%',
            'fontWeight':'bold'},
        ],
    )
    return [
                dbc.Row(html.H3('Season {season} Week {week} Scoreboard'.format(season=season, week=week))),
                dbc.Row([user_table], 
                    style={'width':'80%', 'textAlign':'center', 'display':'inline-block'}
                ),
                html.Br(),
                html.Br(),
            ]

################ BORDER IF WINNER #############
def border_if_winner(team, winner, final=True):
    
    if final == True:
        if team == winner:
            return {'border':"2px MediumSeaGreen solid", 'borderRadius': '50%',
                     
                    }
        elif winner == 'TIE':
            return {'border':"2px GoldenRod solid", 'borderRadius': '50%',
                    
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

def display_team(row, home_or_away, df_teams, width):

    if home_or_away == 'away':
        team= 'away_team'
        team_name = 'full_name_away'
        score_ot = 'visitor_points_overtime_total'
        score_col = 'away_team_score'
    else:
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
                        src='/assets/teams/{team}_logo.webp'.format(team=row[team].upper()), 
                        id = row[team] + '_logo',
                        style={
                            'height':'8vw',
                            # 'width':width,
                        }
                    ),style={'textAlign': 'center',}
                ),
                dbc.Tooltip(
                    team_stats(row[team], season=row['season'], week=row['week_num'], df_teams=df_teams),
                    target=row[team] + '_logo',
                )
            ],
            # style=border_if_winner(team=row[team], winner=row['winner'],),
            ),

            dbc.Row([
                html.Div("{name}"\
                    .format(name=row[team_name].title(),
                    style={
                        # 'fontSize':'1vw',
                        'fontWeight':'bold',
                        'height':'1em',
                    })),
            ]),
            html.Br(),

        ],
        style={
            'width':width,
            'maxWidth':width,
            'minWidth':width,
            'fontSize':'2vw',
            # 'height':"5px",
            'justify':"center",
            'textAlign':'center',
            'verticalAlign':'center',
            'display': 'inline-block', 
            # 'fontSize':'80%',
        }
        )


def display_scores(season, week, user, df, user_df, df_teams, USER_LIST):


    def display_upcoming_week(scores, season=season, week=week, user_df=user_df, df_teams=df_teams, USER_LIST=USER_LIST):

        score_layout = [dbc.Row([

                            ### Left Margin
                            dbc.Col(html.Div(''), style={'width':margin_padding,'maxWidth':margin_padding,
                                    'maxWidth':margin_padding}),

                            ## Away Team
                            dbc.Col(html.H4("Away",
                                    style={'fontSize':header_size}), 
                                style={
                                    'fontWeight':'bold',
                                    'width':team_width,
                                    'maxWidth':team_width,
                                    'textAlign':'center', 
                                    'justify':"center",
                                    'verticalAlign':'center',
                                    'minWidth':min_team_width,
                                    }
                                ),
                            
                            ### Left Margin
                            # dbc.Col(html.Div(''), style={'width':margin_padding,'maxWidth':margin_padding,
                            #         'minWidth':margin_padding,}),

                            ## vs
                            dbc.Col(html.Div(""),
                                style= {'width':vs_width, 'maxWidth':vs_width,'minWidth':vs_width,}
                            ),

                            ### Left Margin
                            # dbc.Col(html.Div(''), style={'width':margin_padding,'maxWidth':margin_padding,
                            #         'minWidth':margin_padding}),

                            ## Home Team
                            dbc.Col(html.H4("Home",
                                    style={'fontSize':header_size}), 
                                style={
                                    'fontWeight':'bold',
                                    'width':team_width,
                                    'maxWidth':team_width,
                                    'textAlign':'center', 
                                    'justify':"center",
                                    'verticalAlign':'center',
                                    'minWidth':min_team_width,
                                    }
                                ),
                            
                            dbc.Col(html.Div(''), style={'width':margin_padding,'maxWidth':margin_padding,
                                    'minWidth':margin_padding}),


                            dbc.Col([

                                ## Predictions
                                html.Div([
                                    html.H4("Predictions",
                                    style={'fontSize':header_size}),
                                ]),
                            ],
                            style={
                                'fontWeight':'bold',
                                'width':preds_width,
                                'maxWidth':preds_width,
                                'minWidth':preds_width,
                                'textAlign':'center', 
                                'justify':"center", 
                                'verticalAlign':'center',
                            }
                            ),

                            
                            ### Right Margin
                            # dbc.Col(html.Div(''), style={'width':margin_padding, 'maxWidth':margin_padding,'minWidth':margin_padding}),

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
            
            game_date = datetime.strptime(row['game_date'], "%Y-%m-%d").strftime("%m/%d/%Y")
            game_time = pd.to_datetime(row['game_time']).tz_convert('US/Eastern').strftime("%I:%M %p %Z")

            curr_game_layout =   dbc.Row([
                                    ### Left Margin
                                    dbc.Col(html.Div(''), style={'width':margin_padding,'maxWidth':margin_padding,'minWidth':margin_padding,}),

                                    ### Away Team
                                    display_team(row=row, home_or_away='away', df_teams=df_teams, width=team_width),

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
                                    display_team(row=row, home_or_away='home', df_teams=df_teams, width=team_width),                              
                                    
                                    dbc.Col(html.Div(''), style={'width':margin_padding, 'maxWidth':margin_padding,'minWidth':margin_padding}),

                                    dbc.Col([

                                        ## Predictions
                                        html.Div([

                                            dbc.Row([

                                                dbc.Col([

                                                    html.Div(user + '', style={'fontWeight':'bold'}), 
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
                                        'minWidth':preds_width,
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
                                    'width':'100%', 
                                })

            score_layout = score_layout + [curr_game_layout] + [html.Br()]

        return score_layout

    def display_historical_week(scores, season=season, week=week, user_df=user_df, df_teams=df_teams, USER_LIST=USER_LIST):

        score_layout = [dbc.Row([

                            ### Left Margin
                            dbc.Col(html.Div(''), style={'width':margin_padding,'maxWidth':margin_padding,'minWidth':margin_padding}),

                            ## Away Team
                            dbc.Col(html.H4("Away",
                                    style={'fontSize':header_size}), 
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
                            dbc.Col(html.H4("Home",
                                    style={'fontSize':header_size}), 
                                style={'width':team_width,'maxWidth':team_width,
                                    'fontWeight':'bold',
                                    'textAlign':'center', 
                                    'justify':"center",
                                    'verticalAlign':'center',
                                    'minWidth':team_width,
                                    }
                                ),
                            
                            dbc.Col(html.Div(''), style={'width':margin_padding,'maxWidth':margin_padding,'minWidth':margin_padding}),


                            dbc.Col([

                                ## Predictions
                                html.Div([
                                    html.H4("Predictions",
                                    style={'fontSize':header_size}),
                                ]),
                            ],
                            style={
                                'width':preds_width,'maxWidth':preds_width,\
                                'fontWeight':'bold',
                                'minWidth':preds_width,
                                'textAlign':'center', 
                                'justify':"center", 
                                'verticalAlign':'center',
                            }
                            ),

                            
                            ### Right Margin
                            # dbc.Col(html.Div(''), style={'width':margin_padding,'maxWidth':margin_padding,'minWidth':margin_padding}),

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
            
            game_date = datetime.strptime(row['game_date'], "%Y-%m-%d").strftime("%m/%d/%Y")
            game_time = pd.to_datetime(row['game_time']).tz_convert('US/Eastern').strftime("%I:%M %p %Z")

            curr_game_layout =   dbc.Row([
                                    ### Left Margin
                                    dbc.Col(html.Div(''), style={'width':margin_padding,'maxWidth':margin_padding,'minWidth':margin_padding}),

                                    ### Away Team
                                    display_team(row=row, home_or_away='away', df_teams=df_teams, width=team_width),

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
                                    display_team(row=row, home_or_away='home', df_teams=df_teams, width=team_width),                              
                                    
                                    dbc.Col(html.Div(''), style={'width':margin_padding,'maxWidth':margin_padding,'minWidth':margin_padding}),

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
                                        'width':preds_width, 'maxWidth':preds_width,
                                        'textAlign':'center', 
                                        'justify':"center", 
                                        'verticalAlign':'center',
                                        'fontSize':'1.5vw',
                                        'minWidth':preds_width,
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
                                    'width':'100%', 
                                })

                                
            curr_game_info_layout = [
                                    dbc.Row([
                                        dbc.Col(html.Div(''), style={'width':margin_padding,'maxWidth':margin_padding}),
                                        dbc.Col([
                                            html.H4(
                                                "{score}".format(score=int(row['away_team_score'] + row['visitor_points_overtime_total'])),
                                            style={
                                                'fontWeight':'bold',
                                                'fontSize':score_font_size,
                                            },
                                            ),
                                        ], style={'justify':'center','textAlign':'center','verticalAlign':'center','width':team_width,'maxWidth':team_width,'minWidth':team_width,}),

                                        dbc.Col(html.Div(''), style={'width':vs_width,'maxWidth':vs_width}),

                                        dbc.Col([
                                            html.H4(
                                                "{score}".format(score=int(row['home_team_score'] + row['home_points_overtime_total'])),
                                            style={
                                                'fontWeight':'bold',
                                                'fontSize':score_font_size,
                                            },
                                            ),
                                        ], style={'justify':'center','textAlign':'center','verticalAlign':'center','width':team_width,'maxWidth':team_width,'minWidth':team_width,}),

                                        dbc.Col(html.Div(''), style={'width':margin_padding,'maxWidth':margin_padding}),
                                        dbc.Col(html.Div(''), style={'width':preds_width, 'maxWidth':preds_width}),
                                    ],
                                    style={
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