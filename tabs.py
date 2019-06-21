import dash
import dash_core_components as dcc
from dash.dependencies import Input, Output, State
import dash_html_components as html
# import dash_table_experiments as dt
# import plotly.graph_objs as go
# from plotly import tools

import datetime
today = datetime.datetime.today().date()

from config import Config
config = Config()

TABS = [
    dcc.Tab(label='Main', children=[
        html.Div([html.Label('Attribution date range')],
                 style={'width': '20%', 'marginTop': 20, 'font-weight': 'bold', 'font-size': 20}),
        html.Div([dcc.DatePickerRange(id='main/date_range',
                                      start_date=today - datetime.timedelta(30), end_date=today,
                                      max_date_allowed=today, display_format='MMM DD, Y')],
                 style={'marginTop': 5}),

        html.Div([
            html.Label('App Name', style={'font-weight': 'bold', 'font-size': 20}),
            dcc.Dropdown(id='main/app',
                         options=[{'label': name, 'value': name} for name in config.APP_NAMES])
        ], style={'width': '20%', 'marginTop': 20}),

        html.Div([
            html.Label('Platform', style={'font-weight': 'bold', 'font-size': 20}),
            dcc.Dropdown(id='main/plat',
                         options=[{'label': plat, 'value': plat} for plat in config.PLATFORMS])
        ], style={'width': '20%', 'marginTop': 20}),

        html.Div([
            html.Label('Media Source', style={'font-weight': 'bold', 'font-size': 20}),
            dcc.Dropdown(id='main/media')
        ], style={'width': '20%', 'marginTop': 20})
    ]),
    dcc.Tab(label='Dynamics', children=[
        html.H3('Dynamics')
    ])
]