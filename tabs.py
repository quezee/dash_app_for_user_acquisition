import dash
import dash_core_components as dcc
from dash.dependencies import Input, Output, State
import dash_html_components as html
import dash_table
# import plotly.graph_objs as go
# from plotly import tools

from config import Config
config = Config()

TABS = [
    dcc.Tab(label='Main', children=[
        html.Div([html.Label('Performance by breakdown', style={'font-weight': 'bold', 'font-size': 25})],
                 style={'marginTop': 20}),

        html.Div([
            html.Label('Group by', style={'font-weight': 'bold', 'font-size': 17}),
            html.Br(),
            dcc.Dropdown(id='main_groupby', multi=True)
        ], style={'width': '500px', 'marginTop': 20}),

        html.Button(id='main_submit', n_clicks=0, children='Submit'),
        dash_table.DataTable(id='main_table', style_data={'whiteSpace': 'normal'},
                             filter_action="native", sort_action="native",
                             css=[{'selector': '.dash-cell div.dash-cell-value',
                                   'rule': 'display: inline; white-space: inherit;'
                                           'overflow: inherit; text-overflow: inherit;'}])


    ]),
    dcc.Tab(label='Dynamics', children=[
        html.H3('Dynamics')
    ])
]