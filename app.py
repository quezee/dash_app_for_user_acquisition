import dash
import dash_auth
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

from core.layouts import LAYOUTS
from config import Config
config = Config()


app = dash.Dash(__name__)
auth = dash_auth.BasicAuth(
    app,
    config.USERS
)

app.layout = html.Div([
    html.H1('Doshique'),
    dcc.Tabs(id="tabs", value='Main', children=[
        dcc.Tab(label='Main', value='Main'),
        dcc.Tab(label='Dynamics', value='Dynamics'),
    ]),
    html.Div(id='tab-content')
])

@app.callback(Output('tab-content', 'children'),
              [Input('tabs', 'value')])
def render_content(tab):
    return LAYOUTS[tab]


if __name__ == '__main__':
    app.run_server(debug=True)