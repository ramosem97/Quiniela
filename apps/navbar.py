from dash.dependencies import Input, Output
from dash import Dash, dcc, html, dash_table
import dash_bootstrap_components as dbc
from dash_extensions.enrich import Dash, ServersideOutput, Output, Input, Trigger, State
from dash.exceptions import PreventUpdate
import plotly.graph_objs as go
import pandas as pd 
import numpy as np
from dash import dash_table as dt

## App Import
# from app import app, df, USER_LIST, user_df, df_teams, preds

########## building the dropdowns ################
def create_dropdowns(df, season, week):
    dropdown_season = dcc.Dropdown(
        options=[
            
            {'label':"{season}".format(season=season), 'value':season} for season in df.sort_values('season', ascending=False).season.unique()

        ],
        value=season,
        placeholder="Season",
        id='season',
        clearable = False,
        # style={'fontSize':'1vw'},
        # in_navbar = True,
        # label = "Season",
    )

    dropdown_week = dcc.Dropdown(
        options=[
            
            {'label':"{week_type} - {week}".format(week=week_num, week_type=week_type), 'value':week_num} if week_type=='REG' else \
                                {'label':"{week_type}".format(week=week_num, week_type=week_type), 'value':week_num} \
                                for week_num, week, week_type in df.loc[df['season']==df.loc[df['winner']!='']['season'].max()]\
                                .sort_values('week_num', ascending=True).groupby(['week_num', 'week', 'week_type']).size()\
                                    .reset_index(drop=False)[['week_num', 'week', 'week_type']].values
            
        ],
        value=week,
        placeholder="Week",
        id='week',
        clearable = False,
        # style={'fontSize':'1vw'},
        # in_navbar = True,
        # label = "Week",
    )
    return dropdown_season, dropdown_week

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
        css=[{
            'selector': '.dash-spreadsheet td div',
            'rule': '''
                line-height: 15px;
                max-height: 30px; min-height: 30px; height: 30px;
                display: block;
                overflow-y: hidden;
            '''
        }],
        # fill_width=False,
    )
    return [
                    
                html.Div([user_table], 
                    style={
                        'color':'white',
                        'alignItems':"center",
                        # 'width':'80%', 
                        'height':'100px',
                        'textAlign':'center', 
                        'justify':'center', 
                        # 'display':'inline-block', 
                        'padding':'4px',
                        'fontFamily':"arial",
                    }, 
                ),
                html.Br(),
            ]

def dropdowns_lay(dropdown_season, dropdown_week):
    return dbc.Row([
                html.Div([
                    dbc.Col([html.H6('Season: ', style={'color':'white','textAlign':'left','padding':'2px'})]), 
                    dbc.Col([dropdown_season], style={'textAlign':'center','padding':'2px'}),
                    ], style={'width':'40%'}), 
                html.Div([
                    dbc.Col([html.H6('Week: ', style={'color':'white', 'textAlign':'left','padding':'2px'})]), 
                    dbc.Col([dropdown_week], style={'textAlign':'center','padding':'2px'}),
                    ], style={'width':'40%'}),
            ],
            style={'width':'100%','justify':"center", 'verticalAlign':'center', 'textAlign':'center'},
            )


def create_navbar(df, user_df, USER_LIST, USER_ABBV_DICT, auth):

    ## Create Dropdowns
    season = df.loc[df['winner']!='']['season'].max()
    week = df.loc[df['season']==df.loc[df['winner']!='']['season'].max()].loc[(df['winner']!='')].week_num.max()
    dropdown_season, dropdown_week = create_dropdowns(df, season, week)

    ## Get Current Scores Table
    score_table = get_curr_score(week, season, user_df, USER_LIST, USER_ABBV_DICT)


    ## Create Layout
    nav_lay = []
    layout = dbc.Navbar(

            # Use row and col to control vertical alignment of logo / brand
            html.Div(
                [   
                
                dbc.Row([
                    dbc.Col(
                    [
                        html.Img(src=r'assets\\nfl_logo.jpg', style={'height':'6vw', 'padding':'1px'}),
                        html.H5("Quiniela Ramos", style={'color':'white','padding':'1px'})
                    ], 
                    style={'width':'50%', 'textAlign':'left', 'verticalAlign':'center'}
                    ),

                    dbc.Col(\
                    [
                        html.H6("", id='username', style={'textAlign':'right', \
                            'verticalAlign':'top', 'justify':'right', 'color':'white', 'paddingRight':'0%'}),
                    ], style={'paddingRight':'0%'}
                    )
                ],
                style={'width':'95%', 'minWidth':'95%', 'textAlign':'left', 'justify':"center", 'verticalAlign':'center'},
                ),
                
                dbc.Row(
                [
                    html.Div('', style={'width':'10%'}), 
                    html.Div('', style={'textAlign':'center', 
                        'height':'1vw', 'justify':'center', 
                        'borderBottom':".5px outset rgba(255,255,255,.2)", 
                        'width':'80%', 'borderBottomWidth':'light'}),
                    html.Div('', style={'width':'10%'}), 
                ]),
                dropdowns_lay(dropdown_season, dropdown_week),
                
                dbc.Row(
                [
                    html.Div('', style={'width':'10%'}), 
                    html.Div('', style={'textAlign':'center', 
                        'height':'1vw', 'justify':'center', 
                        'borderBottom':".5px outset rgba(255,255,255,.2)", 
                        'width':'80%', 'borderBottomWidth':'light'}),
                    html.Div('', style={'width':'10%'}), 
                ]),
                dbc.Row(
                    score_table, 
                    style={'paddingLeft':'5%', 'paddingRight':'5%', 'textAlign':'center', 'justify':'center'},
                    id='score_table'
                ),
            ], 
            style={'width':'95%', 'padding':'2.5%', 'paddingRight':'2.5%'}),

        sticky="fixed",
        color="dark",
        dark=True,
    )

    return layout

####################################################
################ DEFINE PAGE LAYOUT ################
####################################################
 
# layout = create_navbar(df=df.copy(), preds=preds.copy())