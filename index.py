# import dash_bootstrap_components as dbc
# import numpy as np
# import pandas as pd
# import plotly.graph_objs as go
# from dash import Dash, dash_table, dcc, html
# from dash.dependencies import Input, Output
# from dash.exceptions import PreventUpdate
# from dash_extensions.enrich import (Dash, Input, Output, ServersideOutput,
#                                     State, Trigger)

# from app import app, df
# from apps import navbar, scores_page, stats_page


# ####################################################
# ################ DEFINE DEFAULT LAYOUT #############
# ####################################################

# app.layout = html.Div([
#     dcc.Location(id='url', refresh=False),
#     navbar.layout,
#     html.Div(children=[], id='page',
#     style={'width':'100%', 'textAlign':'center', 'justify':'center', 'display':'inline-block'})
# ])





# @app.callback([Output("page", "children"), Output("week", "options"),],
# [Input("season", "value"), Input("week", "value")])
# def print_df(season, week):

#     ## Get Score Children
#     children = scores_page.display_scores(season=season, 
#                                             week=week,
#                                             user='Emilio')

#     ### Update Week Options
#     week_options = [{'label':"{week_type} - {week}".format(week=week_num, week_type=week_type), 'value':week_num} \
#                             for week_num, week, week_type in df.loc[df['season']==season]\
#                             .sort_values('week_num', ascending=True).groupby(['week_num', 'week', 'week_type']).size()\
#                                 .reset_index(drop=False)[['week_num', 'week', 'week_type']].values]


#     ## Get Table of Scores


#     return children, week_options
    
# # if __name__ == '__main__':

# #     debug=False
# #     if debug:
# #             app.run_server(debug=debug, port=8060)
# #     else:
# #         app.run_server(debug=debug, host='0.0.0.0', port=8060)
