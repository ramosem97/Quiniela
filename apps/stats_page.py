# from dash.dependencies import Input, Output
# import dash.html as html
# import dash.dcc as dcc
# import dash.dash_table as dt

# from app import app

# layout = html.Div([
# html.H3('Historical Statistics'),
# dcc.Dropdown(
#     id='stats-dropdown',
#     options=[
#         {'label': 'Statistics - {}'.format(i), 'value': i} for i in [
#             'NYC', 'MTL', 'LA'
#         ]
#     ]
# ),
# html.Div(id='stats-display-value'),
# ])

# def return_Layout(dfCountry, country):
#     return html.Div([
#         html.H5(country+' GPD Time Series Table', style={'textAlign': 'center'}),
#         dt.DataTable(
#                 dfCountry.to_dict('records'),

#                 # optional - sets the order of columns
#                 columns=sorted(dfCountry.columns),

#                 row_selectable=True,
#                 # filterable=True,
#                 # sortable=True,
#                 # selected_row_indices=[],
#                 id='datatable-gdpCountry'
#             ),
#     ])    


