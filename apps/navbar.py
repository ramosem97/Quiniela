from dash.dependencies import Input, Output
from dash import Dash, dcc, html, dash_table
import dash_bootstrap_components as dbc
from dash_extensions.enrich import Dash, ServersideOutput, Output, Input, Trigger, State
from dash.exceptions import PreventUpdate
import plotly.graph_objs as go
import pandas as pd 
import numpy as np

## App Import
# from app import app, df, USER_LIST, user_df, df_teams, preds


########## building the dropdowns ################
def create_dropdowns(df, preds):
    dropdown_season = dcc.Dropdown(
        options=[
            
            {'label':"{season}".format(season=season), 'value':season} for season in df.sort_values('season', ascending=False).season.unique()

        ],
        value=df.loc[df['winner']!='']['season'].max(),
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
        value=df.loc[df['season']==df.loc[df['winner']!='']['season'].max()].loc[(df['winner']!='')].week_num.max(),
        placeholder="Week",
        id='week',
        clearable = False,
        # style={'fontSize':'1vw'},
        # in_navbar = True,
        # label = "Week",
    )
    return dropdown_season, dropdown_week

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


def create_navbar(df, preds, auth):

    dropdown_season, dropdown_week = create_dropdowns(df, preds)

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
                dropdowns_lay(dropdown_season, dropdown_week),

                ], style={'width':'95%', 'padding':'2.5%', 'paddingRight':'1%'}),
        sticky="fixed",
        color="dark",
        dark=True,
    )

    return layout

####################################################
################ DEFINE PAGE LAYOUT ################
####################################################
 
# layout = create_navbar(df=df.copy(), preds=preds.copy())