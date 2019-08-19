import dash_core_components as dcc
import dash_html_components as html
import dash_table
# import dash
# from dash.dependencies import Input, Output, State
# import plotly.graph_objs as go
# from plotly import tools

from config import Config
config = Config()
TABS = [
    dcc.Tab(label='Main metrics', children=[
        html.Div([
            html.Label('Group by', style={'font-weight': 'bold', 'font-size': 17}),
            html.Br(),
            dcc.Dropdown(id='main_groupby', multi=True)
        ], style={'width': '500px', 'marginTop': 20}),

        html.Button(id='main_submit', n_clicks=0, children='Submit'),
        dash_table.DataTable(id='main_table', style_data={'whiteSpace': 'normal'},
                             filter_action="native", sort_action="native", page_size=40,
                             css=[{'selector': '.dash-cell div.dash-cell-value',
                                   'rule': 'display: inline; white-space: inherit;'
                                           'overflow: inherit; text-overflow: inherit;'}])
    ]),

    dcc.Tab(label='Dynamics', children=[
        html.Div([
            html.Label('Time series breakdown', style={'font-weight': 'bold', 'font-size': 17}),
            dcc.RadioItems(id='dynamics_ts_break', value='Day', style={'font-size': 17},
                           options=[{'label': opt, 'value': opt} for opt in config.GROUPERS['dynamics_dt']]),
            html.Br(),
            html.Label('Group by', style={'font-weight': 'bold', 'font-size': 17}),
            html.Br(),
            dcc.Dropdown(id='dynamics_groupby', multi=True,
                         options=[{'label': opt, 'value': opt} for opt in config.GROUPERS['dynamics_graph']])
        ], style={'width': '500px', 'marginTop': 20}),

        html.Button(id='dynamics_submit', n_clicks=0, children='Submit'),
        dcc.Graph(id='dynamics_graph')
    ])
]

