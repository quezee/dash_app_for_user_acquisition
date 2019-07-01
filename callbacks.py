import dash
import dash_core_components as dcc
from dash.dependencies import Input, Output, State
import dash_html_components as html
# import plotly.graph_objs as go
# from plotly import tools

from config import Config
config = Config()
from ch_handler import CHHandler
ch = CHHandler(config.DB_HOST, config.DB_PORT)

from app import app


@app.callback(Output('media', 'options'),
              [Input('date_range', 'start_date'), Input('date_range', 'end_date'),
               Input('app', 'value'), Input('plat', 'value')])
def set_media_options(start_date, end_date,
                      app, plat):
    start_date = start_date + ' 00:00:00'
    end_date = end_date + ' 23:59:59'
    query = '''
    SELECT DISTINCT MediaSource FROM appsflyer.installs
    WHERE AttributedTouchTime BETWEEN {} AND {}'''.format(repr(start_date), repr(end_date))
    if app:
        query += ' AND AppName = {}'.format(repr(app))
    if plat:
        query += ' AND Platform = {}'.format(repr(plat))
    data = ch.simple_query(query)
    return data


@app.callback([Output("main_table", "data"), Output("main_table", "columns")],
              [Input('main_submit', 'n_clicks')],
              [State('date_range', 'start_date'), State('date_range', 'end_date'),
               State('app', 'value'), State('plat', 'value'), State('media', 'value'),
               State('main_groupby', 'value')])
def update_main_table(n_clicks, start_date, end_date,
                      app, plat, media, groupby):
    if not groupby:
        return [], []
    start_date = start_date + ' 00:00:00'
    end_date = end_date + ' 23:59:59'
    if isinstance(groupby, list):
        groupby = ', '.join(groupby)
    query = '''
    SELECT {}, COUNT(AppsFlyerID) as Installs
    FROM appsflyer.installs
    WHERE AttributedTouchTime BETWEEN {} AND {}
    '''.format(groupby, repr(start_date), repr(end_date))
    if app:
        query += ' AND AppName = {}'.format(repr(app))
    if plat:
        query += ' AND Platform = {}'.format(repr(plat))
    if media:
        query += ' AND MediaSource = {}'.format(repr(media))
    query += ' GROUP BY {}'.format(groupby)
    data, cols = ch.simple_query(query, True)
    return data, cols