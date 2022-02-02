#https://github.com/ishanmehta17/dash_template/blob/master/src/dash_template.py

from email.policy import default
import pandas as pd
import dash
from dash import dcc
from dash import html
import dash_bootstrap_components as dbc
import plotly.express as px
from dash.dependencies import Input, Output
import re
from scraperLoggers import scraperLogger
from webScraperCommon import SSHTunnelOperations, interrogateStoreFlask
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import traceback, os
from customExceptions import *

# the style arguments for the sidebar.
SIDEBAR_STYLE = {
    'position': 'fixed',
    'top': 0,
    'left': 0,
    'bottom': 0,
    'width': '20%',
    'padding': '20px 10px',
    'background-color': '#f8f9fa'
}

# the style arguments for the main content page.
CONTENT_STYLE = {
    'margin-left': '25%',
    'margin-right': '5%',
    'padding': '20px 10p'
}

TEXT_STYLE = {
    'textAlign': 'center',
    'color': '#191970'
}

CARD_TEXT_STYLE = {
    'textAlign': 'center',
    'color': '#0074D9'
}

colors = {
    'background': '#111111',
    'text': '#7FDBFF',
    'graph': '#'
}


# output = []

# output.append(html.H1(children=[
#                                 'Currently scraping ',
#                                 html.Div(id='current-store-as-title', style={'display': 'inline'}),
#                                 ".com for item"],
#                       style = {"textAlign": "center", "color": colors["text"]}))
#output.append(html.Div(children='test', style = {"textAlign": "center", "color": colors["text"]}))

try:
    username = os.environ["tweakersCloneUsername"]
    password = os.environ["tweakersClonePassword"]
except KeyError as e:
    raise UnavailableCredentialsException(msg = traceback.format_exc())

sshFunctions = SSHTunnelOperations(username,password,"mysql","dateItemPrice")

try:
    sshFunctions.start_tunnel()
    URIForDB = sshFunctions.getURI()
except Exception:
    scraperLogger(level = "ERROR", msg = "URI for DB not attainable, : \n" + traceback.format_exc())
    raise

server = Flask(__name__)
server.config['SQLALCHEMY_DATABASE_URI']=URIForDB
server.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(server)

dbFunctions = interrogateStoreFlask(db)
dbFunctions.start_session()
available_stores = dbFunctions.available_online_stores()
default_store = available_stores[0]
print(f"The default store is {default_store}")
controls = dbc.FormGroup(
    [
        html.P('Online Store', style = 
            {'textAlign' : 'center'
        }),
        dcc.Dropdown(
            id='chosenStore',
            options=[{'label': str.capitalize(item), 'value': item} for item in available_stores],
            value=default_store,  # default value
        ),
        html.P('Filter item', style={
            'textAlign': 'center'
        }),
        dcc.Dropdown(
            id='items-available',
            value=['Select item'] # default value
        ),
        html.Br(),
        html.P('Range Slider', style={
            'textAlign': 'center'
        }),
        dcc.RangeSlider(
            id='range_slider',
            min=0,
            max=20,
            step=0.5,
            value=[5, 15]
        ),
        html.P('Check Box', style={
            'textAlign': 'center'
        }),
        dbc.Card([dbc.Checklist(
            id='check_list',
            options=[{
                'label': 'Value One',
                'value': 'value1'
            },
                {
                    'label': 'Value Two',
                    'value': 'value2'
                },
                {
                    'label': 'Value Three',
                    'value': 'value3'
                }
            ],
            value=['value1', 'value2'],
            inline=True
        )]),
        html.Br(),
        html.P('Radio Items', style={
            'textAlign': 'center'
        }),
        dbc.Card([dbc.RadioItems(
            id='radio_items',
            options=[{
                'label': 'Value One',
                'value': 'value1'
            },
                {
                    'label': 'Value Two',
                    'value': 'value2'
                },
                {
                    'label': 'Value Three',
                    'value': 'value3'
                }
            ],
            value='value1',
            style={
                'margin': 'auto'
            }
        )]),
        html.Br(),
        dbc.Button(
            id='submit_button',
            n_clicks=0,
            children='Submit',
            color='primary',
            block=True
        ),
    ]
)

sidebar = html.Div(
    [
        html.H2('Parameters', style=TEXT_STYLE),
        html.Hr(),
        controls
    ],
    style=SIDEBAR_STYLE,
)

content = html.Div(
    [
     html.Div(id="main-content")], style = CONTENT_STYLE
    )
app = dash.Dash(server=server,external_stylesheets=[dbc.themes.BOOTSTRAP])
app.layout = html.Div([sidebar, content, dcc.Store(id="current-store",data="coolblue"),
                                         dcc.Store(id="current-store-df")])

@app.callback(Output("current-store","data"),
               Input("chosenStore", "value"))
def update_main_title(chosenStore):
    print("running update_main_title()")
    if chosenStore is None:
        chosenStore = default_store
    return [chosenStore]

@app.callback(Output("current-store-df","data"),
               Input("current-store", "data"))
def _read_from_db(chosenStore):
    print("running _read_from_db()")
    chosenStore = "".join(chosenStore)
    df = dbFunctions.read_from_db(chosenStore)
    return df.to_json(orient="split")

@app.callback(Output("items-available","options"),
               Input("current-store-df", "data"))
def available_items_in_store(df):
    print("running available_items_in_store()")
    df = pd.read_json(df,orient="split")
    df.fillna("", inplace=True)
    searchTerms = df.searchTerm.unique()
    return [{'label': str.capitalize(searchTerm), 'value': searchTerm} for searchTerm in searchTerms]

@app.callback(Output("main-content","children"),
               Input("current-store-df", "data"))
def update_charts(df):
    print("running update_charts()")
    df = pd.read_json(df,orient="split")
    df.fillna("", inplace=True)
    uniqueItems = df.item.unique()
    output = []
    
    for uniqueItem in uniqueItems:
        uniqueItemdf = df[df.item == uniqueItem]
        
        fig = px.line(uniqueItemdf, x="date", y="price")
        fig.update_layout(
            plot_bgcolor=colors['background'],
            paper_bgcolor=colors['background'],
            font_color=colors['text']
        )
        itemLink = uniqueItemdf.iloc[0]["link"]
        # Title of item

        output.append(html.A(href="https://" + str(itemLink), 
                             children = html.Div(children = str(uniqueItem),
                                                 style = {"textAlign": "center", 
                                                          "color": colors["text"]})))
        output.append(dcc.Graph(id = str(uniqueItem), figure = fig))
        output.append(html.Div(html.Br()))
    return output

if __name__ == "__main__":
    app.init_app(server)
    app.run_server(debug=True,host="0.0.0.0",port=5000,use_reloader=False)
