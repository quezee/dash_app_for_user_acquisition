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
            html.Label('Days cohort', style={'font-weight': 'bold', 'font-size': 17}),
            html.Br(),
            dcc.RadioItems(id='main/cohort', value='7', style={'font-size': 17},
                           options=[{'label': coh, 'value': coh} for coh in config.COHORTS])
        ], style={'marginTop': 20}),

        html.Div([
            html.Label('Retarget effect', style={'font-weight': 'bold', 'font-size': 17}),
            html.Br(),
            dcc.RadioItems(id='main/rtg', value='Exclude', style={'font-size': 17},
                           options=[{'label': 'Exclude', 'value': 'Exclude'},
                                    {'label': 'Include', 'value': 'Include'}])
        ], style={'marginTop': 20}),

        html.Div([
            html.Label('Others threshold', style={'font-weight': 'bold', 'font-size': 17}),
            html.Br(),
            dcc.Input(id='main/others', value=100, type='number')
        ], style={'marginTop': 20}),

        html.Div([
            html.Label('Breakdown', style={'font-weight': 'bold', 'font-size': 17}),
            html.Br(),
            dcc.Dropdown(id='main/break', value='Campaign', multi=True,
                         options=[{'label': by, 'value': by} for by in config.GROUPERS])
        ], style={'width': '35%', 'marginTop': 20}),

        html.Div([dash_table.DataTable(id='main/table')]),





    ]),
    dcc.Tab(label='Dynamics', children=[
        html.H3('Dynamics')
    ])
]