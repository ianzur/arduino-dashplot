import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import dash_daq as daq
import pandas as pd
import plotly.graph_objs as go
import serial
import re
from datetime import datetime
import os

HIST_LEN = 1200
BAUD = 9600

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

ser = serial.Serial('/dev/ttyACM0', baudrate=BAUD)

app.layout = html.Div([

    dcc.Store(
        id='memory',
        storage_type='local'
    ),

    dcc.Interval(
        id="read-interval",
        interval=1*1500,
        n_intervals=0
    ),

    html.Div(
        [
            html.H2('MY GRAPH'),
            html.Div(
                [
                    html.Div(
                        [
                            dcc.Input(
                                id='filename',
                                type='text',
                                placeholder='filename',
                            ),
                        ]
                    ),
                    html.Button(
                        'Save',
                        id='save-button',
                    ),
                ],
            ),
            daq.StopButton(
                id='stop-button',
                size=166,
            ),
            dcc.Textarea(
                id='read-me',
                disabled=True,
                title='README',
                value='Dash app to graph and save data from single serial input',
                style={
                    'width': '40%',
                }
            )

        ],
        className='row',
        style={
            "marginTop": "1%",
            "marginBottom": "2%",
            "justify-content": "space-around",
            "align-items": "center",
            "display": "flex",
            "position": "relative",
        }
    ),

    dcc.Graph(
        id="my-graph",
        style={"height": "475px", "marginBottom": "1%"},
        animate=True
    ),

    html.Div(
        str(datetime.now().strftime('%H:%M:%S.%f')),
        id='start-time',
        style={'display': 'none'}
    ),
])


@app.callback(
    Output('memory', 'data'),
    [
        Input('read-interval', 'n_intervals')
    ],
    [
        State('memory', 'data'),
        State('start-time', 'children'),
    ])
def read(_, df, start_time):
    s = ser

    if s.is_open:

        if df is not None:
            df = pd.read_json(df, orient='index')

        while True:
            if s.in_waiting > 0:

                line = s.readline()

                g = re.match(r'b\'(\d{1,8})\\t(\d{1,5})\\r\\n\'', str(line))

                if g is not None:

                    new = pd.DataFrame(
                        {
                            'time': [int(g.group(1)) / 1000],
                            # 'time': [int(g.group(1)) / 1000 + pd.to_timedelta(start_time).total_seconds()],
                            'randn [8-bit]': [int(g.group(2))]
                        })

                    if df is None:
                        df = new
                    else:
                        df = df.append(new, ignore_index=True, sort=False)

            else:
                if df is not None:
                    biggest = df.index.max()

                    if biggest > HIST_LEN:
                        df = df.iloc[biggest - HIST_LEN:biggest]

                    return df.to_json(orient='index')


@app.callback(
    Output('my-graph', 'figure'),
    [
        Input('memory', 'data')
    ],
)
def update_graph(data):

    data = pd.read_json(data, orient='index')

    # plotting this causes animation bug?
    # data.time = pd.to_datetime(data.time, unit='s', origin=datetime.today().date())

    return {
        'data': [
            go.Scatter(
                x=data.time,
                y=data['randn [8-bit]'],
                mode="lines",
                marker={"size": 6},
                name="Random Numbers"
            )
        ],
        "layout": go.Layout(
            xaxis={
                "title": 'time [ms]',
                "range": [min(data.time), max(data.time)],
            },
            yaxis={"title": "Random Numbers"},
            margin={"l": 70, "b": 100, "t": 0, "r": 25},
        )
    }


@app.callback(
    [
        Output('stop-button', 'buttonText'),
        Output('read-interval', 'disabled')],
    [
        Input('stop-button', 'n_clicks')
    ])
def end(clicks):

    if clicks is None:
        dash.exceptions.PreventUpdate()
    else:
        if clicks % 2 == 0:
            return 'stop', False
        else:
            return 'start', True

    return 'stop', False


@app.callback(
    [
        Output('filename', 'value'),
        Output('read-me', 'value')
    ],
    [
        Input('save-button', 'n_clicks')
    ],
    [
        State('memory', 'data'),
        State('filename', 'value'),
        State('read-me', 'value'),
        State('start-time', 'children'),
    ])
def save(clicks, df, name, readme, start_time):

    if clicks is None:
        dash.exceptions.PreventUpdate()
    else:
        if df is not None or name is not None:
            df = pd.read_json(df, orient='index')
            # df.time = pd.to_datetime(df.time, unit='s', origin=datetime.today().date())
            df.time = pd.to_datetime(df.time + pd.to_timedelta(start_time).total_seconds(), unit='s', origin=datetime.today().date())
            print(df.time)
            out = os.path.join(os.getcwd(), name.split('.')[0] + '.csv')
            df.to_csv(out)
            return '', 'Saved to: ' + out

    return name, readme


if __name__ == '__main__':
    app.run_server(debug=True)
