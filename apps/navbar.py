from dash.dependencies import Input, Output
from dash import Dash, dcc, html, dash_table
import dash_bootstrap_components as dbc
from dash_extensions.enrich import Dash, ServersideOutput, Output, Input, Trigger, State
from dash.exceptions import PreventUpdate
import plotly.graph_objs as go
import pandas as pd 
import numpy as np

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
        # in_navbar = True,
        # label = "Season",
    )

    dropdown_week = dcc.Dropdown(
        options=[
            
            {'label':"{week_type} - {week}".format(week=week, week_type=week_type), 'value':week} for week_num, week, week_type in df.loc[df['season']==preds['season'].max()]\
                                .sort_values('week_num', ascending=True).groupby(['week_num', 'week', 'week_type']).size()\
                                    .reset_index(drop=False)[['week_num', 'week', 'week_type']].values
            
        ],
        value=1,
        placeholder="Week",
        id='week',
        clearable = False,
        # in_navbar = True,
        # label = "Week",
    )
    return dropdown_season, dropdown_week

def dropdowns_lay(dropdown_season, dropdown_week):
    return dbc.Row([
                html.Div([
                    dbc.Col([html.H5('Season: ', style={'color':'white', 'fontSize':'3vw', 'textAlign':'left', })]), 
                    dbc.Col([dropdown_season], style={'fontSize':'2.5vw', 'textAlign':'center'}),
                    ], style={'width':'50%'}), 
                html.Div([
                    dbc.Col([html.H5('Week: ', style={'color':'white', 'fontSize':'3vw', 'textAlign':'left', })]), 
                    dbc.Col([dropdown_week], style={'fontSize':'2.5vw', 'textAlign':'center'}),
                    ], style={'width':'50%'}),
            ],
            style={'width':'100%', 'justify':"left", 'verticalAlign':'center'},
            )


def create_navbar(df, preds):

    dropdown_season, dropdown_week = create_dropdowns(df, preds)

    layout = dbc.Navbar(

            # Use row and col to control vertical alignment of logo / brand
            html.Div(
                [   
                
                dbc.Row([
                    dbc.Col([html.Img(src=r'assets\\nfl_logo.jpg', style={'width':'15vw'})], 
                    style={'textAlign':'left', 'justify':"left", 'verticalAlign':'center'}),
                    # dbc.Col(html.Div(''), style={'width':'5%'}),
                    dbc.Col([dbc.NavbarBrand("Quiniela Ramos", style={'fontSize':'3vw', 'height':'5vw'})], 
                    style={'textAlign':'left', 'justify':"center", 'verticalAlign':'center'}),
                    # dbc.Col(html.Div(''), style={'width':'50%'}),
                ],
                style={'width':'100%', 'minWidth':'100%', 'textAlign':'left', 'justify':"center", 'verticalAlign':'center'},
                ),
                dropdowns_lay(dropdown_season, dropdown_week),

                ], style={'width':'95%', 'padding':'2.5%'}),

        color="dark",
        dark=True,
    )

    return layout