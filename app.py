import dash
import dash_auth
import dash_core_components as dcc
import dash_html_components as html

from config import Config
config = Config()

import datetime
today = datetime.datetime.today().date()

app = dash.Dash(__name__)
auth = dash_auth.BasicAuth(app, config.USERS)

from tabs import TABS

app.layout = html.Div([
    html.Div([
        html.Label('Attribution date range', style={'font-weight': 'bold', 'font-size': 20}),
        html.Br(),
        dcc.DatePickerRange(id='date_range',
                            start_date=today - datetime.timedelta(30), end_date=today,
                            max_date_allowed=today, display_format='MMM DD, Y'),
    ], style={'marginTop': 5}),

    html.Div([
        html.Label('App Name', style={'font-weight': 'bold', 'font-size': 20}),
        html.Br(),
        dcc.Dropdown(id='app',
                     options=[{'label': name, 'value': name} for name in config.APP_NAMES])
    ], style={'width': '15%', 'marginTop': 20}),

    html.Div([
        html.Label('Platform', style={'font-weight': 'bold', 'font-size': 20}),
        html.Br(),
        dcc.Dropdown(id='plat',
                     options=[{'label': plat, 'value': plat} for plat in config.PLATFORMS])
    ], style={'width': '15%', 'marginTop': 20}),

    html.Div([
        html.Label('Media Source', style={'font-weight': 'bold', 'font-size': 20}),
        html.Br(),
        dcc.Dropdown(id='media')
    ], style={'width': '15%', 'marginTop': 20, 'marginBottom': 20}),


    dcc.Tabs(id="tabs", value='Main', children=TABS),
])


from callbacks import *

if __name__ == '__main__':
    app.run_server(debug=True)