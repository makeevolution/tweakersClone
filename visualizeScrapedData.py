import pandas as pd
import json
import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.express as px
from dash.dependencies import Input, Output
import re
from webScraperCommon import webScraperCommon

# coolblue_data = pd.io.json.read_json(path_or_buf="coolblueTest.json")
# amazon_data = pd.io.json.read_json(path_or_buf="amazonTest.json")
# bol_data = pd.io.json.read_json(path_or_buf="bolTest.json")

colors = {
    'background': '#111111',
    'text': '#7FDBFF'
}

webScraperCommon.read_from_db()

# with open("coolblueTest.json") as file:
#     coolblueData = json.load(file)
#     data = {"Product": [*map(lambda x:list(x.keys())[0], coolblueData["itemPrice"])],
#             "Price":[*map(lambda x:list(x.values())[0], coolblueData["itemPrice"])]}
#     data["price"] = [float("".join(re.findall("([0-9][^\.,]*[0-9]*)",i))) for i in data["price"]]
#     df = pd.DataFrame(data)


app = dash.Dash(__name__)

fig = px.bar(df, x="Product", y="Price", barmode="group")
fig.update_layout(
    plot_bgcolor=colors['background'],
    paper_bgcolor=colors['background'],
    font_color=colors['text']
)

app.layout = html.Div(style={'backgroundColor': colors['background']},
    children=[
    html.H1(children="Hello Dash", style = {"textAlign": "center", "color": colors["text"]}),
    html.Div(children='test', style = {"textAlign": "center", "color": colors["text"]}),
    dcc.Graph(id = "example graph", figure = fig)
])

if __name__ == "__main__":
    app.run_server(debug=True,host="localhost",port=9999)