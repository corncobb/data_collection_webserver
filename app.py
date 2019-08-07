#!/usr/bin/env python3

#NOTE: If more machines are added, table needs to be changed, and data receiver needs to be changed.

#Standard imports
import random
import datetime
from datetime import timedelta
import time
from time import mktime
import os.path
import sqlite3
from subprocess import Popen

#Third party improts
import dash
import dash_table
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Output, Input
import plotly
import credentials

#This is to specify the directory of the DB. Having a ton of problems while trying 
#to do this on Linux but Windows worked fine -_-
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, "data.db")
conn = sqlite3.connect(db_path, check_same_thread=False)

c = conn.cursor()

columns = ['Machine','State', 'Last Received', 'Total Cycle Count',	'CPM by Operation Time', 
'CPM by Shift Time', 'Encoder Count (ft)', 'Down Time', 'Operation Time (shift time-downtime)', 
'Shift Time','Total Shift Time (minutes)', 'Total Operation Time (minutes)']

app = dash.Dash(__name__)

app.layout = html.Div([
    html.Div([
    html.H1('Data Dashboard'),
    html.Div(id='datatable')], className='data-table-component'),
    html.Br(),
    html.Div(dcc.Graph(id='live-update-graph'), className='graph-component'),
    dcc.Interval(
        id='interval-component',
        interval=60*1000, # in milliseconds. Updates the graph every 60 seconds
        n_intervals=0
    ),
], className='container')

def retrieve_recent(machine):
  c.execute("SELECT * FROM data_points WHERE machine=:machine ORDER BY id DESC LIMIT 1", {'machine': machine})
  data = c.fetchone() 
  if data == None:
    return (0,0,0,str(datetime.datetime(2000,1,1,hour=0, minute=0, second=0,  microsecond=0)),0,0,0,0,0,0,0)
  else:
    return data

#returns a list so it can display in the graph
def retrieve_cpm_by_operation(machine):
  cpm_list = []
  c.execute("SELECT * FROM data_points WHERE machine=:machine ORDER BY id DESC LIMIT 4320", {'machine': machine}) #limit is 1440 to return the list of data over the last 24 hours
  data = c.fetchall()
  for x in data:
    #if the machine is "DOWN" or "OFF" then it will show 0 in the graph. This was requested by Josh
    if x[2] != "RUNNING":
      cpm_list.append(0)
    else:
      cpm_list.append(x[5])
  return cpm_list

#returns a list so it can display in the graph
def retrieve_time_list(machine):
  cpm_list = []
  c.execute("SELECT * FROM data_points WHERE machine=:machine ORDER BY time DESC LIMIT 4320", {'machine': machine}) #limit is 1440 to return the list of data over the last 24 hours
  data = c.fetchall()
  for x in data:
    cpm_list.append(x[3])
  return cpm_list

@app.callback(
    Output('datatable', "children"),
    [Input('interval-component', "n_intervals")])
def update_table(n):

    #machine_one_status_data = retrieve_recent(1) #Returns a tuple of the recent data from machine one
    machine_two_status_data = retrieve_recent(2) #Same as above for for machine two

    display_table = [
        dash_table.DataTable(
            id = 'live-update-table',
            columns = [{"name": i, "id": i} for i in columns],
            data = [
                    #Machine 2 data
                    {'Machine': 'Line ' + str(machine_two_status_data[1]),
                    'State': machine_two_status_data[2],
                    'Last Received': machine_two_status_data[3],
                    'Total Cycle Count': machine_two_status_data[4],
                    'CPM by Operation Time': machine_two_status_data[5],
                    'CPM by Shift Time': machine_two_status_data[6],
                    'Encoder Count (ft)': machine_two_status_data[7],
                    'Down Time': str(datetime.timedelta(minutes = machine_two_status_data[8])),
                    'Shift Time': str(datetime.timedelta(minutes = machine_two_status_data[9])),
                    'Operation Time (shift time-downtime)': str(datetime.timedelta(minutes = machine_two_status_data[9] - machine_two_status_data[8])),
                    'Total Shift Time (minutes)': machine_two_status_data[9],
                    'Total Operation Time (minutes)': machine_two_status_data[8],
                    },
                    ],    
            style_table={
              'width': '80p%',
              'margin-left': 'auto',
              'margin-right': 'auto'
            },  
            style_cell={
                # all three widths are needed
                'minWidth': '100px', 'width': '120px', 'maxWidth': '200px',
                'whiteSpace': 'normal',
                'fontFamily': 'Arial', 
                'size': 10,
                'textAlign': 'left'
            },
            css=[{
                'selector': '.dash-cell div.dash-cell-value',
                'rule': 'display: inline; white-space: inherit; overflow: inherit; text-overflow: inherit;'
            }],
            style_data_conditional=[
              {
                'if': {
                  'column_id': 'Last Received'
                },
                'width': '15%'
              },
              {
                'if': {
                    'column_id': 'State',
                    'filter_query': '{State} eq "RUNNING"'
                },
                'backgroundColor': '#0be000',
                'color': 'white',
                'textAlign': 'center',
                },
                {
                'if': {
                    'column_id': 'State',
                    'filter_query': '{State} eq "DOWN"'
                },
                'backgroundColor': '#e07000',
                'color': 'white',
                'textAlign': 'center',
                },
                {
                'if': {
                    'column_id': 'State',
                    'filter_query': '{State} eq "OFF"'
                },
                'backgroundColor': '#f00000',
                'color': 'white',
                'textAlign': 'center',
                }],
            style_header={'backgroundColor': '#000000','color': 'white'},
        )]

    return display_table

@app.callback(Output('live-update-graph', 'figure'),
              [Input('interval-component', 'n_intervals')])
def update_graph_live(n):

    fig = plotly.tools.make_subplots(rows=1, cols=1, vertical_spacing=0.2)

    fig['layout'] = {
                    'autosize': True,
                    'title':'CPM by Operation Time',
                    'paper_bgcolor':'rgba(0,0,0,0)',
                    'plot_bgcolor':'#e6e6e6',
                    #'automargin': True,
                    #'legend':{'x': 0, 'y': 1, 'xanchor': 'right'},
                    'xaxis':{'range':[datetime.datetime.now() - datetime.timedelta(minutes=60),
                            datetime.datetime.now()], #This is for the range of the x-axis. Right now the range will show last hour
                            'title': 'Time'},
                    'yaxis': {'range':[50,70], 'title': 'CPM by Operation Time'},
                    'showlegend': True
                    }
    #line 1
    trace_one = {
                'type':'scatter',
                'x':retrieve_time_list(1),
                'y':retrieve_cpm_by_operation(1),
                'name':'Line 1',
                'mode':'lines+markers',
                'line':{'color':'red'}
                }
    #line 2 (NOTE: Will only show if data exists)
    trace_two = {
                'type':'scatter',
                'x':retrieve_time_list(2),
                'y':retrieve_cpm_by_operation(2),
                'name':'Line 2',
                'mode':'lines+markers',
                'line':{'color':'blue'}
                }

    fig.append_trace(trace_one, 1, 1)
    fig.append_trace(trace_two, 1, 1)

    return fig

def main():
  app.run_server(debug=True, host="0.0.0.0", port=8050, use_reloader=False) #dubug=True
    
if __name__ == '__main__':
  main()
