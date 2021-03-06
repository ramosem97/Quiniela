import dash
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd

data = pd.read_csv("results_stacked.csv", index_col=0)
data.sort_values(["season", 'week'], inplace=True)

import plotly.graph_objs as go
fig = go.Figure(data=[go.Scatter(x=data["season"].values, y=data["week"].values, mode='markers')])

app = dash.Dash(__name__)

app.layout = html.Div(
    children=[
        html.H1(children="Quiniela Analytics",),
        html.P(
            children="Analyze Football Predictions"
            " and the number of avocados sold in the US"
            " from 2003 to present",
        ),
        dcc.Graph(
            figure={
                "data": [
                    {
                        "x": data["season"],
                        "y": data["week"],
                        "type": "scatter",
                    },
                ],
                "layout": {"title": "Average Price of Avocados"},
            },
        ),
        dcc.Graph(
            id='example-graph-2',
            figure=fig
    )
    ]
)

if __name__ == "__main__":
    app.run_server(debug=True)