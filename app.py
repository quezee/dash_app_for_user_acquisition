import dash
import dash_auth
import dash_core_components as dcc
import dash_html_components as html

from config import Config
config = Config()

import logging
import datetime
today = datetime.datetime.today().date()

app = dash.Dash(__name__)
auth = dash_auth.BasicAuth(app, config.USERS)

from tabs import TABS

LABEL_SIZE = 18

app.layout = html.Div([
    html.Div([
        html.Label('Attribution date range', style={'font-weight': 'bold', 'font-size': LABEL_SIZE}),
        html.Br(),
        dcc.DatePickerRange(id='date_range',
                            start_date=today - datetime.timedelta(30), end_date=today,
                            max_date_allowed=today + datetime.timedelta(1),
                            display_format='MMM DD, Y'),
    ], style={'marginTop': 5}),

    html.Div([
        html.Label('App Name', style={'font-weight': 'bold', 'font-size': LABEL_SIZE}),
        html.Br(),
        dcc.Dropdown(id='app_name',
                     options=[{'label': name, 'value': name} for name in config.APP_NAMES])
    ], style={'marginTop': 20, 'width': '300px', 'display': 'inline-block'}),

    html.Div([
        html.Label('Platform', style={'font-weight': 'bold', 'font-size': LABEL_SIZE}),
        html.Br(),
        dcc.Dropdown(id='plat',
                     options=[{'label': plat, 'value': plat} for plat in config.PLATFORMS])
    ], style={'width': '300px', 'display': 'inline-block'}),

    html.Div([
        html.Label('Media Source', style={'font-weight': 'bold', 'font-size': LABEL_SIZE}),
        html.Br(),
        dcc.Dropdown(id='media')
    ], style={'width': '300px', 'display': 'inline-block'}),

    html.Br(),
    html.Div([
        html.Label('Days cohort', style={'font-weight': 'bold', 'font-size': LABEL_SIZE}),
        html.Br(),
        dcc.RadioItems(id='cohort', value='7', style={'font-size': 17},
                       options=[{'label': coh, 'value': coh} for coh in config.COHORTS])
    ], style={'width': '300px', 'display': 'inline-block', 'marginTop': 20, 'marginBottom': 20}),

    html.Div([
        html.Label('Campaign Type', style={'font-weight': 'bold', 'font-size': LABEL_SIZE}),
        html.Br(),
        dcc.RadioItems(id='camptype', value='0', style={'font-size': 17},
                       options=[{'label': 'All', 'value': 'All'},
                                {'label': 'UA', 'value': '0'},
                                {'label': 'RTG', 'value': '1'}])
    ], style={'width': '300px', 'display': 'inline-block'}),

    html.Div([
        html.Label('Retarget effect', style={'font-weight': 'bold', 'font-size': LABEL_SIZE}),
        html.Br(),
        dcc.RadioItems(id='rtg', value='Exclude', style={'font-size': 17},
                       options=[{'label': 'Exclude', 'value': 'Exclude'},
                                {'label': 'Include', 'value': 'Include'}])
    ], style={'width': '300px', 'display': 'inline-block'}),

    html.Div([
        html.Label('Whales', style={'font-weight': 'bold', 'font-size': LABEL_SIZE}),
        html.Br(),
        dcc.RadioItems(id='whales', value='Include', style={'font-size': 17},
                       options=[{'label': 'Exclude', 'value': 'Exclude'},
                                {'label': 'Include', 'value': 'Include'}])
    ], style={'width': '300px', 'display': 'inline-block'}),


    dcc.Tabs(id="tabs", value='Main', children=TABS),
])


from callbacks import *

if __name__ == '__main__':
    logging.basicConfig(filename=config.LOGPATH, level=logging.DEBUG)
    logging.info('_________________Started_________________')

    app.run_server(debug=True)

    logging.info('_________________Finished_________________')