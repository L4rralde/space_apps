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

n = len(x)

figure = dict(data=[{'x': [], 'y': []}], layout=dict(xaxis=dict(range=[-1, 1]), yaxis=dict(range=[-1, 1])))
figure['layout']['yaxis'].update(autorange = True)
figure['layout']['xaxis'].update(autorange = True)
app = dash.Dash(__name__, update_title=None)

app.layout = html.Div([dcc.Graph(id='graph', figure=figure), dcc.Interval(id="interval", interval=1)])

@app.callback(Output('graph', 'extendData'), [Input('interval', 'n_intervals')])
def update_data(n_intervals):
    index = (100*n_intervals) % n
    value = y[index] * 10**9
    t = x[index]
    return dict(x=[[t]], y=[[value]]), [0], 1000

if __name__ == '__main__':
    app.run_server()
