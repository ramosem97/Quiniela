# import dash_bootstrap_components as dbc
# import plotly.graph_objs as go
# from dash import dcc, html
# from dash.dependencies import Input, Output
# from dash_extensions.enrich import Input, Output, State
# import dash
# import os
# import dash_bootstrap_components as dbc
# from apps import navbar, scores_page
# from app import app, df, preds, df_teams, user_df, USER_LIST, USER_ABBV_DICT

# ####################################################
# ################ DEFINE APP LAYOUT #################
# ####################################################

# app.layout = html.Div([
#     dcc.Location(id='url', refresh=False),
#     navbar.layout,
#     html.Div(children=[], id='page',
#     style={'width':'95%', 'textAlign':'center', 'justify':'center'})
# ])

# @app.callback([Output('page-content', 'children'), Output('url', 'pathname')],
#               [Input('url', 'pathname')
#                ])
# def display_page(pathname):
    
#     if pathname == '/scores':
#         return scores_page.layout
#     # elif pathname == '/display-plant':
#     #     return display_plant.layout
#     # elif pathname == '/edit-plant':
#     #     return edit_plant.layout
#     else:
#         return scores_page.layout, '/scores'


# @app.callback([Output("page", "children"), Output("week", "options"),],
# [Input("season", "value"), Input("week", "value")])
# def print_df(season, week):

#     ## Get Score Children
#     children = scores_page.display_scores(season=season, 
#                                             week=week,
#                                             user='Emilio',
#                                             df=df.copy(),
#                                             df_teams=df_teams.copy(),
#                                             user_df=user_df.copy(),
#                                             USER_LIST=USER_LIST,
#                                             USER_ABBV_DICT=USER_ABBV_DICT)

#     ### Update Week Options
#     week_options = [{'label':"{week_type} - {week}".format(week=week_num, week_type=week_type), 'value':week_num} \
#                             for week_num, week, week_type in df.loc[df['season']==season]\
#                             .sort_values('week_num', ascending=True).groupby(['week_num', 'week', 'week_type']).size()\
#                                 .reset_index(drop=False)[['week_num', 'week', 'week_type']].values]


#     ## Get Table of Scores


#     return children, week_options
    
# if __name__ == '__main__':

#     debug=True
#     if debug:
#             app.run_server(debug=debug, port=8060)
#     else:
#         app.run_server(debug=debug, host='0.0.0.0', port=8060)
