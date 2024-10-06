import sys
import os
import dash
import dash_html_components as html
import dash_core_components as dcc

from dash.dependencies import Input, Output

import random
sys.path.append(os.environ["SPACE"])
from utils.utils import get_data


x, y = get_data()
max_y = 10**9 * max(abs(y))

n = len(x)

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
figure = dict(
    data=[{'x': [], 'y': []}], 
    layout=dict(xaxis=dict(range=[0, x[len(x) - 1]]), yaxis=dict(range=[-max_y, max_y]))
)

app = dash.Dash(__name__, update_title=None, external_stylesheets=external_stylesheets)

app.layout = html.Div([dcc.Graph(id='graph', figure=figure), dcc.Interval(id="interval", interval=1)])

@app.callback(Output('graph', 'extendData'), [Input('interval', 'n_intervals')])
def update_data(n_intervals):
    index = (100*n_intervals) % n
    value = y[index] * 10**9
    t = x[index]
    return dict(x=[[t]], y=[[value]]), [0], n//400

if __name__ == '__main__':
    app.run_server(host="0.0.0.0", port="8050")
