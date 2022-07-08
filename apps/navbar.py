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
        value=df.loc[df['winner'].notnull()]['season'].max(),
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


def create_navbar(df, preds):

    dropdown_season, dropdown_week = create_dropdowns(df, preds)

    layout = dbc.Navbar(
        
        dbc.Container(
            [
                # Use row and col to control vertical alignment of logo / brand
                html.Div(
                    [   
                        dbc.Row([
                            dbc.Col([html.Img(src=r'assets\\nfl_logo.jpg', height='50px')], style={'width':'25%', 'maxWidth':'25%', 'minWidth':'25%'}),
                            # dbc.Col(html.Div(''), style={'width':'5%'}),
                            dbc.Col([dbc.NavbarBrand("Quiniela Ramos")], style={'width':'25%'}),
                            dbc.Col(html.Div(''), style={'width':'50%'}),
                        ],
                        style={'width':'100%', 'textAlign':'left', 'justify':"center", 'verticalAlign':'center'},
                        ),
                        html.Br(),
                        dbc.Row([
                            dbc.Col([
                                dbc.Row(html.Div('Season: ', style={'color':'white'})), 
                                dbc.Row(dropdown_season)
                            ], style={'width':'20%'}),
                            dbc.Col([
                                dbc.Row(html.Div('Week: ', style={'color':'white'})), 
                                dbc.Row(dropdown_week)
                            ], style={'width':'20%'}),
                        ]),
                    ],
                    style={'width':'100%'},
                ),
            ],style={'width':'100%'}
        ),
        color="dark",
        dark=True,
        className="mb-4",
    )

    return layout