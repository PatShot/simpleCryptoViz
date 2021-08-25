#Imports
import requests
import json
import os
import sys
import pandas as pd
import numpy as np
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
from dash import Dash
from dash.dependencies import Output, Input, State
from dash.exceptions import PreventUpdate
import plotly.express as px
import plotly.graph_objects as go

from datetime import datetime

#Constants
API_BASE = 'https://api.coingecko.com/api/v3/'
PING = '/ping'
ASSET_PLAT = '/asset_platforms'
COIN_LIST = '/coins/list'
ID_BTC = '/coins/bitcoin'

#Index Average Settings
#short
INDEX_WINDOW = 12
W = np.linspace(0, 1, INDEX_WINDOW)
#long - to be added

#Helpful Function Declarations:
#1. Volatility Index Calculation Function
def VolIndexFunc(series):
    """
    Calculate naive Volatility Index given a pandas Series with Alphas
    alpha = abs(z-score)
    """
    return np.exp(2*series)

#2. Data from API
def get_current_coin_chart_data(coin_id, currency, days):
    """
    Returns data at fixed time interval for given 
    coin_id vs curr.
    
    Returns JSON obj.
    """
    EXT = f'/coins/{coin_id}/market_chart?vs_currency={currency}&days={days}'
    print(EXT)
    res = requests.get(API_BASE+EXT)
    data = json.loads(res.text)
    return data

#Get Coin List from Data
coin_list_df = pd.read_csv('data/coin_list.csv')

#Start App
app = Dash(__name__, external_stylesheets=[dbc.themes.SLATE])

#LAYOUT
app.layout = html.Div([
    dbc.Card(
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    html.H1('CryptoViz')
                ], width=3),
                dbc.Col([
                ], width=3),
                dbc.Col([
                ], width=3),
            ], align='left'),            
            dbc.Row([
                dbc.Col([
                ], width=3),
                dbc.Col([
                    dcc.Location(id='dropdown_1'),
                    html.Div(id='page-content1'),
                ], width=3),
                dbc.Col([
                    html.Div(id='cur_index_disp'),
                ], width=3),
                dbc.Col([
                    dcc.Location(id='dropdown_2'),
                    html.Div(id='page-content2'),
                ], width=3),
            ], align='center'), 
            html.Br(),
            dbc.Row([
                dbc.Col([
                    dcc.Graph(id='main_price_graph') 
                ], width=7),
                dbc.Col([
                    dcc.Location(id='compare_table')
                ], width=2),
                dbc.Col([
                ], width=3),
            ], align='center'), 
            html.Br(),
            dbc.Row([
                dbc.Col([
                    dcc.Graph(id='main_graph_2')
                ], width=7),
                dbc.Col([
                    dcc.RadioItems(id = 'graph2_ctrl',
                        options=[
                            {'label': 'Volume', 'value': 'vols'},
                            {'label': 'Market Cap', 'value': 'mcap'},
                            {'label': 'Volatility', 'value': 'vlty'},
                        ],
                        value = 'vols',
                        labelStyle={'display': 'block'}
                    ),
                    dcc.Location(id='radio_out1'),
                ], width=2),
                dbc.Col([
                ], width=3),
            ], align='center'),      
        ]), color = 'dark'
    ),
    html.Footer(id='footer_text',
                children = [
                    html.Div([
                        html.P('Powered by CoinGecko.'),
                        html.A('CoinGecko/API', href='https://www.coingecko.com/en/api')
                    ])
                ]
            ),
    dcc.Store(id='coin_id_data'),
])

#CALLBACKS
@app.callback(Output('page-content1', 'children'), Input('dropdown_1', 'value'))
def generate_layout(dropdown_1):
    return html.Div([
        # html.Label('Multi-Select Dropdown'),
        dcc.Dropdown(
            options=[{'label': name, 'value': coin_id} for name, coin_id in zip(coin_list_df['name'].to_list(), coin_list_df['id'].to_list())],
            #options=[{'label': 'New York City', 'value': 'NYC'},{'label': 'Montréal', 'value': 'MTL'},{'label': 'San Francisco', 'value': 'SF'}],
            multi=False,
            id='input'
        ),
    ])

@app.callback(Output('page-content2', 'children'), Input('dropdown_2', 'value'))
def generate_layout_2(dropdown_1):
    return html.Div([
        # html.Label('Multi-Select Dropdown'),
        dcc.Dropdown(
            options=[{'label': name, 'value': coin_id} for name, coin_id in zip(coin_list_df['name'].to_list(), coin_list_df['id'].to_list())],
            #options=[{'label': 'New York City', 'value': 'NYC'},{'label': 'Montréal', 'value': 'MTL'},{'label': 'San Francisco', 'value': 'SF'}],
            multi=True,
            id='input2'
        ),
    ])
    
    
@app.callback(Output('coin_id_data', 'data'), Input('input', 'value'))
def get_maingraph_data(value):
    data = get_current_coin_chart_data(coin_id=value, currency='usd', days=30)
    chart_df = pd.DataFrame(data)
    # UNIX Time
    unix_t = chart_df['prices'].apply(lambda x: x[0]/1000)
    #Date and Time
    t = pd.to_datetime(unix_t, unit='s')
    # Price
    p = chart_df['prices'].apply(lambda x: x[1])
    # Volume
    v = chart_df['total_volumes'].apply(lambda x:x[1])
    # Market Caps
    m_caps = chart_df['market_caps'].apply(lambda x:x[1])
    # Making the final frame.
    frame_col = {'datetime': t, 'unixtime':unix_t , 'prices': p, 't_vols': v, 'market_c': m_caps}
    final_df = pd.DataFrame(frame_col)

    final_df['mavg_5'] = final_df['prices'].rolling(window=5).mean()
    final_df['mavg_20'] = final_df['prices'].rolling(window=20).mean()
    final_df['exmavg_24'] = final_df['prices'].ewm(span=24, adjust=True).mean()
    final_df['stddev_5'] = final_df['prices'].rolling(window=5).std()
    final_df['z_score_5'] = (final_df['prices'] - final_df['mavg_5'])/final_df['stddev_5']
    final_df['alpha_5'] = np.abs(final_df['z_score_5'])
    final_df['vol_index_5'] = VolIndexFunc(final_df['alpha_5'])
    final_df['index_avg'] = final_df['vol_index_5'].rolling(window=INDEX_WINDOW).apply(lambda x: sum((W*x)))
    return final_df.to_json(date_format='iso', orient='split')


@app.callback(Output('main_price_graph', 'figure'), Input('coin_id_data', 'data'), Input('input', 'value'))
def render_price(j_data, value):
    if value is None:
        raise PreventUpdate
    else:
        gr_data_df = pd.read_json(j_data, orient='split')
        #Price Graph, so y is 'prices'
        fig = px.line(data_frame=gr_data_df, x='datetime', y=['prices', 'mavg_5', 'mavg_20', 'exmavg_24'])
        fig.update_xaxes(rangeslider_visible=True)
    return fig

@app.callback(Output('main_graph_2', 'figure'), Input('coin_id_data', 'data'), Input('input', 'value'), Input('graph2_ctrl', 'value'))
def render_vols(j_data, value, choice):
    if value is None:
        raise PreventUpdate
    else:
        gr_data_df = pd.read_json(j_data, orient='split')
        if choice == 'vols':
            fig = px.line(data_frame=gr_data_df, x='datetime', y='t_vols')
            fig.update_xaxes(rangeslider_visible=True)
            return fig
        if choice == 'mcap':
            fig = px.line(data_frame=gr_data_df, x='datetime', y='market_c')
            fig.update_xaxes(rangeslider_visible=True)
            return fig
        if choice == 'vlty':
            fig = px.line(data_frame=gr_data_df, x='datetime', y='index_avg')
            fig.update_xaxes(rangeslider_visible=True)
            return fig

@app.callback(Output('cur_index_disp', 'children'), Input('coin_id_data', 'data'))
def update_vol_index(j_data):
    gr_data_df = pd.read_json(j_data, orient='split')
    index_val = gr_data_df['index_avg'].iloc[-1]
    return html.H3(f'Volatility Index: %.3f' %index_val)

if __name__ == "__main__":
    app.run_server()
