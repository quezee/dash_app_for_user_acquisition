import dash
import dash_core_components as dcc
from dash.dependencies import Input, Output, State
import dash_html_components as html
# import plotly.graph_objs as go
# from plotly import tools
import datetime

from config import Config
config = Config()
from utils import *
ch = CHHandler(config.DB_HOST, config.DB_PORT)

from app import app




@app.callback(Output('media', 'options'),
              [Input('date_range', 'start_date'), Input('date_range', 'end_date'),
               Input('app', 'value'), Input('plat', 'value')])
def set_media_options(dt_start, dt_end,
                      app, plat):
    dt_start, dt_end = preproc_dt_range(dt_start, dt_end)
    query = '''
    SELECT DISTINCT MediaSource FROM appsflyer.installs
    WHERE AttributedTouchTime BETWEEN {} AND {}'''.format(dt_start, dt_end)
    if app:
        query += ' AND AppName = {}'.format(repr(app))
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
               State('app', 'value'), State('plat', 'value'), State('media', 'value'),
               State('main_cohort', 'value'), State('main_camptype', 'value'),
               State('main_rtg', 'value'), State('main_groupby', 'value')])
def update_main_table(n_clicks, dt_start, dt_end, app,
                      plat, media, cohort, camptype, rtg, groupby):
    if not groupby:
        return [], []
    if isinstance(groupby, list):
        groupby = ', '.join(groupby)

    constructor = QueryConstructor(dt_start, dt_end, app, plat,
                                   media, cohort, camptype, rtg, groupby)

    installs_query = constructor.installs_query()

    if (not media) | (media in config.SPECIAL_MEDIAS):
        select = '''
        {}, Installs, (Cost + MediaCost) as Cost, (CostTaxed + MediaCostTaxed) as CostTaxed
        '''.format(groupby)

        if not media:
            for media_source in config.SPECIAL_MEDIAS:
                media_query = constructor.media_query(media_source)
                installs_query = constructor.join(installs_query, media_query, select)

        elif media in config.SPECIAL_MEDIAS:
            media_query = constructor.media_query(media)
            installs_query = constructor.join(installs_query, media_query, select)

    inapps_query = constructor.inapps_query()

    select = '''
        {},
        ROUND(Cost, 1) as Cost, ROUND(CostTaxed, 1) as CostTaxed, ROUND(Cost/Installs, 2) as CPI,
        Installs, Payers, ROUND(100*Payers/Installs, 1) as Paying, ROUND(Gross, 1) as Gross,
        ROUND(GrossClean, 1) as GrossClean,
        ROUND(100*GrossClean/CostTaxed, 1) as ROI
    '''.format(groupby)
    resulting_query = constructor.join(installs_query, inapps_query, select)

    print(resulting_query)

    data, cols = ch.simple_query(resulting_query, True)
    return data, cols