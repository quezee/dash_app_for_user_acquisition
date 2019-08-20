import plotly.graph_objs as go
from plotly.subplots import make_subplots
from dash.dependencies import Input, Output, State
import datetime
from utils import *
ch = CHHandler(config.DB_HOST, config.DB_PORT)
from app import app
import pandas as pd


@app.callback(Output('media', 'options'),
              [Input('date_range', 'start_date'), Input('date_range', 'end_date'),
               Input('app_name', 'value'), Input('plat', 'value')])
def set_media_options(dt_start, dt_end, app_name, plat):
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
        opts = config.GROUPERS['Intersection']
    elif media in config.SPECIAL_MEDIAS:
        opts = config.GROUPERS[media]
    else:
        opts = config.GROUPERS['All']
    return [{'label': opt, 'value': opt} for opt in opts]


@app.callback([Output('main_table', 'data'), Output('main_table', 'columns')],
              [Input('main_submit', 'n_clicks')],
              [State('date_range', 'start_date'), State('date_range', 'end_date'),
               State('app_name', 'value'), State('plat', 'value'), State('media', 'value'),
               State('sql_filter', 'value'), State('cohort', 'value'), State('camptype', 'value'),
               State('rtg', 'value'), State('whales', 'value'), State('dup_payments', 'value'),
               State('main_groupby', 'value'), State('ad_metrics', 'value')])
def update_main_table(n_clicks, dt_start, dt_end, app_name, plat, media, sql_filter, cohort,
                      camptype, rtg, whales, dup_payments, groupby, ad_metrics):
    if not groupby:
        return [], []
    groupby = preproc_groupby(groupby)

    constructor = QueryConstructor(dt_start, dt_end, app_name, plat, media, sql_filter, cohort,
                                   camptype, rtg, whales, dup_payments, groupby, ad_metrics)

    installs_query = constructor.combined_installs_query()
    payments_query = constructor.payments_query()

    select =  \
    '\n{},' \
    '\nROUND(Cost, 1) as Cost, ROUND(CostTaxed, 1) as CostTaxed, ROUND(Cost/Installs, 2) as CPI,' \
    '\nInstalls, ROUND(Gross, 1) as Gross, ROUND(GrossClean, 1) as GrossClean,' \
    '\nPayers, ROUND(100*Payers/Installs, 1) as PayingShare,' \
    '\nROUND(Gross/Installs, 2) as ARPU, ROUND(GrossClean/Installs, 2) as ARPUClean,' \
    '\nROUND(100*GrossClean/CostTaxed, 1) as ROI' \
    .format(groupby)

    if ad_metrics:
        select += ',\n' + ', '.join([col for col in constructor.ad_cols])
        if 'Impressions' in constructor.ad_cols:
            select += ', ' + 'ROUND(1000*Installs/Impressions, 2) as IPM,' \
                             'ROUND(1000*Cost/Impressions, 2) as CPM'
        if 'Clicks' in constructor.ad_cols:
            select += ', ' + 'ROUND(100*Installs/Clicks, 1) as IR'
        if ('Impressions' in constructor.ad_cols) and ('Clicks' in constructor.ad_cols):
            select += ', ' + 'ROUND(100*Clicks/Impressions, 1) as CTR'
        if ('Impressions' in constructor.ad_cols) and ('Views' in constructor.ad_cols):
            select += ', ' + 'ROUND(100*Views/Impressions, 1) as ViewImp'

    resulting_query = constructor.join(installs_query, payments_query, select)

    data, cols = ch.simple_query(resulting_query, True)
    return data, cols


@app.callback(Output('dynamics_graph', 'figure'),
              [Input('dynamics_submit', 'n_clicks')],
              [State('date_range', 'start_date'), State('date_range', 'end_date'),
               State('app_name', 'value'), State('plat', 'value'), State('media', 'value'),
               State('sql_filter', 'value'), State('cohort', 'value'), State('camptype', 'value'),
               State('rtg', 'value'), State('whales', 'value'), State('dup_payments', 'value'),
               State('dynamics_groupby', 'value'), State('ad_metrics', 'value'), State('dynamics_ts_break', 'value')])
def update_dynamics(n_clicks, dt_start, dt_end, app_name, plat, media, sql_filter, cohort,
                      camptype, rtg, whales, dup_payments, groupby, ad_metrics, ts_break):

    if ad_metrics:
        metrics = ['Installs', 'Cost', 'CPI', 'Gross', 'PayingShare', 'ARPU',
                   'ROI', 'IPM', 'CPM', 'IR', 'CTR', 'ViewImp']
        nrows = 4
    else:
        metrics = ['Installs', 'Cost', 'CPI', 'Gross', 'PayingShare', 'ARPU', 'ROI']
        nrows = 3

    fig = make_subplots(rows=nrows, cols=3, specs=[[{}, {}, {}]] * nrows,
                        subplot_titles=['<b>{}</b>'.format(metric) for metric in metrics],
                        horizontal_spacing=0.04, vertical_spacing=0.1)
    if not ts_break:
        return fig

    constructor = QueryConstructor(dt_start, dt_end, app_name, plat, media, sql_filter, cohort,
                                   camptype, rtg, whales, dup_payments, groupby, ad_metrics, ts_break)

    installs_query = constructor.combined_installs_query()
    payments_query = constructor.payments_query()

    select = \
    '\n{},' \
    '\nInstalls, Cost, (Cost/Installs) as CPI, Gross, (100*Payers/Installs) as PayingShare,' \
    '\n(Gross/Installs) as ARPU, (100*GrossClean/CostTaxed) as ROI' \
    .format(', '.join([ts_break, groupby]) if groupby else ts_break)

    if ad_metrics:
        if 'Impressions' in constructor.ad_cols:
            select += ', ' + '(1000*Installs/Impressions) as IPM,' \
                             '(1000*Cost/Impressions) as CPM'
        if 'Clicks' in constructor.ad_cols:
            select += ', ' + '(100*Installs/Clicks) as IR'
        if ('Impressions' in constructor.ad_cols) and ('Clicks' in constructor.ad_cols):
            select += ', ' + '(100*Clicks/Impressions) as CTR'
        if ('Impressions' in constructor.ad_cols) and ('Views' in constructor.ad_cols):
            select += ', ' + '(100*Views/Impressions) as ViewImp'

    resulting_query = constructor.join(installs_query, payments_query, select, order_col=ts_break)
    data, cols = ch.simple_query(resulting_query, True)

    data_df = pd.DataFrame(data)
    metrics = [col for col in metrics if col in data_df]

    if groupby:
        data_df = data_df.set_index([ts_break, groupby]).unstack()
        for i, metric in enumerate(metrics):
            row_pos = (i // 3) + 1
            col_pos = (i % 3) + 1
            for level in data_df.columns.levels[1]:
                df = data_df[metric, level]
                trace = go.Scatter(x=df.index, y=df, mode='lines+markers', name=level)
                fig.append_trace(trace, row_pos, col_pos)
        fig['layout'].update({'showlegend': True})

    else:
        data_df = data_df.set_index(ts_break)
        for i, metric in enumerate(metrics):
            row_pos = (i // 3) + 1
            col_pos = (i % 3) + 1
            df = data_df[metric]
            trace = go.Scatter(x=df.index, y=df, mode='lines+markers', name='')
            fig.append_trace(trace, row_pos, col_pos)
        fig['layout'].update({'showlegend': False})

    fig['layout'].update({'height': 850})
    for n in range(1, 8):
        fig['layout']['xaxis{}'.format(n)].update(tickfont={'size': 11}, showticklabels=True)
        fig['layout']['yaxis{}'.format(n)].update(rangemode='tozero')

    return fig

