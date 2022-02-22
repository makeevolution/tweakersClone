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
import time

# the style arguments for the sidebar.
SIDEBAR_STYLE = {
    'position': 'fixed',
    'top': 0,
    'left': 0,
    'bottom': 0,
    'width': '20%',
    'padding': '20px 10px',
    'background-color': '#aaaaaa'
}

# the style arguments for the main content page.
CONTENT_STYLE = {
    'margin-left': '25%',
    'margin-right': '5%',
    'padding': '20px 10p',
    'background-color': '#63636c'
}

colors = {
    'background': '#111111',
    'text': '#ffffff',
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
dbFunctions.start_db_session()

available_stores = dbFunctions.available_online_stores()
default_store = available_stores[2]

searched_items = dbFunctions.searched_terms_in_store(default_store)
default_search_term = searched_items[0]

print(f"The default store is {default_store}, and default search term is {default_search_term}")

controls = dbc.FormGroup(
    [
        html.P('Choose online store', style = 
            {'textAlign' : 'center',
            'fontFamily': "Courier New",
            'fontSize': 16
        }),
        dcc.Dropdown(
            id='chosenStore',
            options=[{'label': str.capitalize(item), 'value': item} for item in available_stores],
            value=default_store,  # default value
        ),
        html.Br(),
        html.P('Choose a search term currently being tracked', style={
            'textAlign': 'center',
            'fontFamily': "Courier New",
            'fontSize': 16
        }),
        dcc.Dropdown(
            id='searched-terms',
            options=[{'label': str.capitalize(item), 'value': item} for item in searched_items],
            value=default_search_term, # default value
        ),
        html.Br(),
        html.Div(children=(html.P("Hi! The dashboard shows daily price history of the most relevant\
                                   items that correspond to the chosen search term.\
                                   Choose the online store and the desired search term. Click on the title\
                                   to go to the item listing on the chosen store.",
                                   style={"textAlign":"center",
                                          "fontFamily": "Courier New"})))
    ]
)

sidebar = html.Div(
    [
        html.H2('TrackIt', style={'fontFamily': "Courier New",
                                  "textAlign": "center"}),
        html.Hr(),
        controls
    ],
    style=SIDEBAR_STYLE,
)

content = html.Div(
    [html.Div(id="main-content")], style = CONTENT_STYLE
    )
app = dash.Dash(server=server,external_stylesheets=[dbc.themes.BOOTSTRAP])
app.layout = html.Div([
                        sidebar, content, dcc.Store(id="current-store",data="coolblue"),
                                          dcc.Store(id="current-store-df"),
                                          dcc.Loading(
                                                id="loading-1",
                                                type="default",
                                                children=html.Div(id="loading-output-1"),
                                                fullscreen=True,
                                                style={'backgroundColor': 'transparent'}
                                          ),
                                         ],
                                         style={"background-color":'#63636c'},
                                         )

@app.callback(Output("current-store","data"),
               Input("chosenStore", "value"))
def update_main_title(chosenStore):
    print("running update_main_title()")
    if chosenStore is None:
        chosenStore = default_store
    return chosenStore

@app.callback(Output("current-store-df","data"),
               Input("current-store", "data"))
def _read_from_db(chosenStore):
    print("running _read_from_db()")
    df = dbFunctions.read_from_db(chosenStore)
    return df.to_json(orient="split")

@app.callback(Output("searched-terms","options"),
               Input("current-store", "data"))
def searched_terms_in_store(chosenStore):
    searched_terms = dbFunctions.searched_terms_in_store(chosenStore)
    return [{'label': str.capitalize(term), 'value': term} for term in searched_terms]

@app.callback(Output("main-content","children"),
               Input("searched-terms","value"),
               Input("current-store-df", "data"))
def update_charts(currentSearchTerm,df):
    print("running update_charts()")
    df = pd.read_json(df,orient="split",convert_dates=False,keep_default_dates=True)
    df = df[df.searchTerm == currentSearchTerm.lower()]
    df.fillna("", inplace=True)
    uniqueItems = df.item.unique()
    output = [html.Br()]

    for uniqueItem in uniqueItems:
        uniqueItemdf = df[df.item == uniqueItem]
        uniqueItemdf = uniqueItemdf.drop_duplicates(subset = 'date', keep = 'last')
        
        fig = px.scatter(uniqueItemdf, x="date", y="price", color_discrete_sequence = ['red'])
        fig.update_layout(
            plot_bgcolor='#63636c',
            paper_bgcolor='#63636c',
            font_family="Courier New",
            font_color="white",
            title_font_family="Times New Roman",
            title_font_color="red",
            legend_title_font_color="green"
        )
        
        itemLink = uniqueItemdf.iloc[0]["link"]
        # Title of item

        output.append(html.A(href="https://" + str(itemLink), 
                             children = html.Div(children = str(uniqueItem),
                                                 style = {"textAlign": "center", 
                                                          "color": colors["text"],
                                                          "font-family": "Courier New, serif"})))
        output.append(dcc.Graph(id = str(uniqueItem), figure = fig))
        output.append(html.Hr(style={"border":"1px dashed black"}))
    print("update charts complete")
    return output

if __name__ == "__main__":
    app.init_app(server)
    app.run_server(debug=True,host="0.0.0.0",port=5000,use_reloader=False)
