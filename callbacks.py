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
from ch_handler import CHHandler
ch = CHHandler(config.DB_HOST, config.DB_PORT)

from app import app

@app.callback(Output('main/media', 'options'),
              [Input('main/date_range', 'start_date'), Input('main/date_range', 'end_date'),
               Input('main/app', 'value'), Input('main/plat', 'value')])
def set_media_options(start_date, end_date,
                      app, plat):
    query = '''
    SELECT DISTINCT MediaSource FROM appsflyer.installs
    WHERE AttributedTouchTime BETWEEN {} AND {}
    AND AppName = {} AND Platform = {}
    '''.format(start_date, end_date, app, plat)
    response = ch.simple_query(query)
    return [{'label': row[0], 'value': row[0]} for row in response]