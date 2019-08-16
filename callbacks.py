# import dash
# import dash_core_components as dcc
# import plotly.graph_objs as go
# from plotly import tools
# import dash_html_components as html
from dash.dependencies import Input, Output, State
import datetime
from utils import *
ch = CHHandler(config.DB_HOST, config.DB_PORT)
from app import app


@app.callback(Output('media', 'options'),
              [Input('date_range', 'start_date'), Input('date_range', 'end_date'),
               Input('app_name', 'value'), Input('plat', 'value')])
def set_media_options(dt_start, dt_end,
                      app_name, plat):
    dt_start, dt_end = preproc_dt_range(dt_start, dt_end)
    query = \
    '\nSELECT DISTINCT MediaSource FROM appsflyer.installs' \
    '\nWHERE AttributedTouchTime BETWEEN {} AND {}' \
    "\n AND MediaSource != ''" \
    .format(dt_start, dt_end)
    if app_name:
        query += ' AND AppName = {}'.format(repr(app_name))
    if plat:
        query += ' AND Platform = {}'.format(repr(plat))
    data = ch.simple_query(query)
    return data


@app.callback(Output('main_groupby', 'options'),
              [Input('media', 'value')])
def set_groupby_options(media):
    if not media:
        opts = config.GROUPERS['Special']
    elif media in config.SPECIAL_MEDIAS:
        opts = config.GROUPERS[media]
    else:
        opts = config.GROUPERS['All']
    return [{'label': opt, 'value': opt} for opt in opts]


@app.callback([Output("main_table", "data"), Output("main_table", "columns")],
              [Input('main_submit', 'n_clicks')],
              [State('date_range', 'start_date'), State('date_range', 'end_date'),
               State('app_name', 'value'), State('plat', 'value'), State('media', 'value'),
               State('cohort', 'value'), State('camptype', 'value'), State('rtg', 'value'),
               State('whales', 'value'), State('dup_payments', 'value'), State('main_groupby', 'value')])
def update_main_table(n_clicks, dt_start, dt_end, app_name, plat, media,
                      cohort, camptype, rtg, whales, dup_payments, groupby):
    if not groupby:
        return [], []
    if isinstance(groupby, list):
        groupby = ', '.join(groupby)

    constructor = QueryConstructor(dt_start, dt_end, app_name, plat, media,
                                   cohort, camptype, rtg, whales, dup_payments, groupby)

    installs_query = constructor.combined_installs_query()
    payments_query = constructor.payments_query()

    select =  \
    '\n{},' \
    '\nROUND(Cost, 1) as Cost, ROUND(CostTaxed, 1) as CostTaxed, ROUND(Cost/Installs, 2) as CPI,' \
    '\nInstalls, Payers, ROUND(100*Payers/Installs, 1) as Paying, ROUND(Gross, 1) as Gross,' \
    '\nROUND(GrossClean, 1) as GrossClean,' \
    '\nROUND(100*GrossClean/CostTaxed, 1) as ROI' \
    .format(groupby)
    resulting_query = constructor.join(installs_query, payments_query, select)

    data, cols = ch.simple_query(resulting_query, True)
    return data, cols