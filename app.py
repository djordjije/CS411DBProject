# Import database utilities
import mysql_utils
import mongodb_utils
import neo4j_utils

# Import query files
import mysql_queries
import neo4j_queries

# Import utils file
import utils

# Dash Plotly dependencies
import dash
from dash import dash_table
from dash import dcc
from dash import html
from dash import callback_context
from dash.dependencies import Input, Output, State

# DB dependencies
from pymongo import MongoClient

# Other dependencies
import pandas as pd
import numpy as np

# Create Dash app
app = dash.Dash(__name__, title='Keyword Analytics')

"""
Run preliminary queries to set up the initial dashboard state
"""

faculty_name_list = [i['name'] for i in
                     mongodb_utils.mongodb_aggregate("faculty", [{"$project": {"_id": 0, "name": 1}}])]
# print("faculty_name_list: ", faculty_name_list) # Debug

# Widget 1 (MySQL)
# Function: For a given keyword and year range, plot the num publications
#   containing that keyword using prepared statements.
# Drop and redefine the W1 procedure
mysql_utils.mysql_query("DROP PROCEDURE IF EXISTS GetKeywordCitations;")
mysql_utils.mysql_query(mysql_queries.w1_stored_procedure)

# Run W1 default query
w1_initial_query = "CALL GetKeywordCitations('{}', 2000, 2020);".format("databases")
w1_initial_result = mysql_utils.mysql_query(w1_initial_query)

# Widget 2 (MongoDB)
# Function: Display and update faculty information
first_faculty_entry = mongodb_utils.mongodb_aggregate("faculty", [{"$match": {"name": faculty_name_list[0]}}])

# Widget 3 (Neo4j)
pub_collab_cts_results, _, _ = neo4j_utils.neo4j_query(neo4j_queries.pub_collab_cts_query)
pub_collab_cts_df = pd.DataFrame(columns=["Faculty Member 1", "Faculty Member 2", "Number of Collaborations"])
for r in pub_collab_cts_results:
    pub_collab_cts_df.loc[len(pub_collab_cts_df.index)] = [
        r.get("faculty1"), r.get("faculty2"), r.get("collaboration_count")
    ]

pub_keyword_names = list(mysql_utils.mysql_query(mysql_queries.publication_keyword_names_query)["keyword_names"])
w3_total_records = str(len(pub_collab_cts_df.to_dict('records')))


# Widget 4
# Drop and redefine the W1 procedure
mysql_utils.mysql_query("DROP PROCEDURE IF EXISTS GetFacultyPairKeywords;")
mysql_utils.mysql_query(mysql_queries.w4_stored_procedure)

# Run W1 default query
w4_initial_query = "CALL GetFacultyPairKeywords('{}', '{}');".format("Agouris,Peggy", "Stefanidis,Anthony")
w4_initial_result = mysql_utils.mysql_query(w4_initial_query)
w4_initial_shared_keywords = w4_initial_result["shared_keyword_names"].iloc[0].split(",")
w4_initial_table_content = [{"Keyword Names": keyword} for keyword in w4_initial_shared_keywords]
# print("w4_initial_result: ", w4_initial_result) # Debug

# Widget 5
# UIUC is University of Illinois at Urbana Champaign
university_names = list(mysql_utils.mysql_query("SELECT DISTINCT name FROM university;")["name"])

# Widget 6
potential_faculty_duplicates = utils.identify_potential_faculty_name_duplicates(faculty_name_list)
w6_query = mysql_queries.w6_query

for i, potential_faculty_duplicate in enumerate(potential_faculty_duplicates):
    w6_query += "'{}'".format(potential_faculty_duplicate)

    if i != len(potential_faculty_duplicates) - 1:
        w6_query += ", "

w6_query += ")"
w6_query += " ORDER BY CASE "

for i, potential_faculty_duplicate in enumerate(potential_faculty_duplicates):
    w6_query += " WHEN faculty_name='{}' THEN {} ".format(potential_faculty_duplicate, i)

w6_query += "ELSE 999 END;"

potential_faculty_duplicates_tables = mysql_utils.mysql_query(w6_query)
w6_total_records = str(len(potential_faculty_duplicates_tables))


# Set up widget templates
app.layout = html.Div(children=[
    # Title container
    html.Div(className='title_container', children=[
        html.H1("Virtual Administrative Assistant Dashboard"),
        html.H2("CS411 Spring 2024"),
    ]),
    # Widget Grid Container
    html.Div(className='grid-container', children=[
        # First Widget
        html.Div([
            html.H2("Publication Trend Keyword Plotter"),
            html.Div(className='description', children=[
                html.P(
                    "View publication keyword citation trends with this tool. The keyword, starting year, "
                    "and ending year are selectable.")
                ]),
            dcc.Graph(
                id='graph1',
                figure={
                    'data': [
                        {'x': w1_initial_result["year"], 'y': w1_initial_result["keyword_count"], 'type': 'line',
                         'name': 'Line chart'}
                    ],
                    'layout': {
                        'title': 'Keyword Popularity',
                        'xaxis': {'title': 'Year'},
                        'yaxis': {'title': 'Num. Publications referencing Keyword'}
                    }
                },
                style={'border-radius': '15px', 'background-color': 'white', 'border-width': '10px'}
            ),
            html.Br(),
            html.Label('Keyword: ', className='test2'),
            html.Br(), html.Br(),
            dcc.Dropdown(id='w1-keyword-dropdown',
                         options=[{'label': i, 'value': i} for i in pub_keyword_names],
                         value="databases", className='dropdown', optionHeight=50),
            html.Br(),

            html.Div([
                html.Div([
                    html.Div([
                        html.Label('Start Year: '),
                        dcc.Input(id='w1-year-start-input', type='number', value=2000, className='year-input'),
                    ], className='year-container'),
                    html.Div([
                        html.Label('End Year: '),
                        dcc.Input(id='w1-year-end-input', type='number', value=2020, className='year-input')
                    ], className='year-container'),
                ], style={'width': '100%'}),
                html.Div([
                    html.Div(className='card', children=[
                        html.Div(className='text-side', children=["Avg. Yearly Citations"]),
                        html.Div(className='number-side', children=[""], id="w1-avg")
                    ], style={'marginBottom': '10px'}),
                    html.Div(className='card', children=[
                        html.Div(className='text-side', children=["Avg. Yearly Change"]),
                        html.Div(className='number-side', children=[""], id="w1-trend")
                    ])
                ])
            ], style={'display': 'flex', 'justifyContent': 'space-between', 'width': '100%'})

        ], className="grid-item"),

        # Second Widget
        html.Div([
            html.H2("Faculty Contact Information Updater"),
            html.Div(className='description', children=[
                html.P("View faculty member images and update contact information with this tool."),
            ]),
            html.Img(id='w2-img', src=first_faculty_entry[0]['photoUrl'], className="image-container"),
            html.Div([
                dcc.Dropdown(
                    id='w2-faculty-dropdown',
                    options=[{'label': i, 'value': i} for i in faculty_name_list],
                    value=faculty_name_list[0],
                    style={'margin': '0 auto'})
            ], style={'width': '100%', 'marginTop': '10px'}),
            html.Br(),
            html.Div([
                html.Div([
                    html.Label('Name: '),
                    dcc.Input(id='w2-name', type='text', value=first_faculty_entry[0]['name'],
                              style={'width': '230px'})
                ], className='w2-data-row'),

                html.Div([
                    html.Label('Phone: '),
                    dcc.Input(id='w2-phone', type='text', value=first_faculty_entry[0]['phone'],
                              style={'width': '230px'})
                ], className='w2-data-row'),

                html.Div([
                    html.Label('Email: '),
                    dcc.Input(id='w2-email', type='text', value=first_faculty_entry[0]['email'],
                              style={'width': '230px'})
                ], className='w2-data-row'),

                html.Button('Update', id='w2-update', n_clicks=0, className='button'),
            ], className='w2-data-container'),
        ], className="grid-item"),

        # Third Widget
        html.Div([
            html.H2("Top Faculty Collaborations Table"),
            html.Div(className='description', children=[
                html.P("View faculty member collaboration counts with this tool. "
                       "The top collaborators are listed in this table"),
            ]),

            dash_table.DataTable(
                id='w3-table',
                columns=[{"name": i, "id": i} for i in pub_collab_cts_df.columns],
                data=pub_collab_cts_df.to_dict('records'),  # Convert DataFrame to dictionary format
                style_table={'height': '300px', 'overflowY': 'auto'},
                style_cell={'textAlign': 'left'},
                style_header={'backgroundColor': 'darkgray', 'fontWeight': 'bold'},
                sort_action="native",
                filter_action="native",
                filter_options={"placeholder_text": "Search..."},
                style_filter={'textAlign': 'left'},
                style_data_conditional=[
                    {
                        'if': {'row_index': 'odd'},
                        'backgroundColor': 'ghostwhite',
                    }
                ],
            ),
            html.Br(),
            html.Div(className='card', children=[
                html.Div(className='text-side', children=["Collaborators"]),
                html.Div(className='number-side', children=[w3_total_records], id="w3-total")
            ])
        ], className="grid-item"),
    
        # Fourth Widget
        html.Div([
            html.H2("Faculty Pair Shared Keyword"),
            html.Div(className='description', children=[
                html.P("View faculty member shared keywords."),
            ]),
            html.Br(),
            html.Div([
                html.Label('Faculty 1 Name: '),
            ]),
            dcc.Dropdown(id='w4-faculty-dropdown-1', options=[{'label': i, 'value': i} for i in faculty_name_list],
                         value=faculty_name_list[0]),
            html.Br(),

            html.Div([
                html.Label('Faculty 2 Name: '),
            ]),
            dcc.Dropdown(id='w4-faculty-dropdown-2', options=[{'label': i, 'value': i} for i in faculty_name_list],
                         value=faculty_name_list[21]),
            html.Br(),
            dcc.Input(id='w4-faculty-keyword', type='text', value="", style={'width': '400px'},
                      placeholder='Enter new keyword here...'),
            html.Br(),
            html.Button('Add Shared Keyword', id='w4-update-f', n_clicks=0, style={'width': '230px'},
                        className='button'),
            html.Br(),

            html.Div([
                html.Label('Shared Keywords: '),
            ], style={'marginTop': '20px'}),
            html.Br(),
            dash_table.DataTable(
                id='w4-table',
                columns=[{"name": "Keyword Names", "id": "Keyword Names"}],
                data=w4_initial_table_content,
                sort_action="native",
                filter_action="native",
                filter_options={"placeholder_text": "Filter keywords with partial search term..."},
                style_filter={'textAlign': 'left'},
                style_table={'height': '300px', 'overflowY': 'auto'},
                style_cell={'textAlign': 'left', 'border': '3px solid dimgray'},
                style_header={'backgroundColor': '#456585', 'fontWeight': 'bold', 'color': 'white',
                              'paddingLeft': '5px'},
                style_data_conditional=[
                    {
                        'if': {'row_index': 'odd'},
                        'backgroundColor': 'ghostwhite',
                    }
                ],
            ),
            html.Div(className='card', children=[
                html.Div(className='text-side', children=["Total Shared"]),
                html.Div(className='number-side', children=[""], id="w4-total")
            ])


        ], className="grid-item"),

        # Fifth Widget
        html.Div([
            html.H2("Top Faculty H-Index by University"),
            html.Div(className='description', children=[
                html.P("View top faculty member H-Indexes for a given university."),
            ]),
            html.Br(),

            html.Label('University: '),
            dcc.Dropdown(id='w5-university-dropdown', options=[{'label': i, 'value': i} for i in university_names],
                         value="University of illinois at Urbana Champaign", style={'width': '800px !important'}),
            html.Br(),
            html.Label('Faculty with Top H-Index: '),
            html.Br(),
            dash_table.DataTable(
                id='w5-table',
                columns=[{"name": "Faculty Name", "id": "faculty_name"}, {"name": "H Index", "id": "h_index"}],
                data=pd.DataFrame(columns=["faculty_name", "h_index"]).to_dict('records'),
                style_table={'height': '300px', 'overflowY': 'auto'},
                style_cell={'textAlign': 'left'},
                style_header={'backgroundColor': 'darkgray', 'fontWeight': 'bold'},
                sort_action="native",
                filter_action="native",
                filter_options={"placeholder_text": "Start typing to search..."},
                style_filter={'textAlign': 'left'},
                style_data_conditional=[
                    {
                        'if': {'row_index': 'odd'},
                        'backgroundColor': 'ghostwhite',
                    }
                ],
            ),
            html.Br(),
            html.Div(className='card', children=[
                html.Div(className='text-side', children=["Total Results"]),
                html.Div(className='number-side', children=[""], id="w5-total")
            ])
        ], className="grid-item"),

        # Sixth Widget
        html.Div([
            html.H2("Stale & Unclean Faculty Data Analyzer"),
            html.Div(className='description', children=[
                html.P("View potential data cleanliness issues."),
            ]),
            dash_table.DataTable(
                id='w1-table',
                columns=[
                    {"name": "Faculty ID", "id": "faculty_id"},
                    {"name": "Faculty Name", "id": "faculty_name"},
                    {"name": "University Name", "id": "university_name"}],
                data=potential_faculty_duplicates_tables.to_dict('records'),
                style_table={'height': '300px', 'overflowY': 'auto'},
                style_cell={'textAlign': 'left'},
                style_header={'backgroundColor': 'darkgray', 'fontWeight': 'bold'},
                sort_action="native",
                filter_action="native",
                filter_options={"placeholder_text": "Search..."},
                style_filter={'textAlign': 'left'},
                style_data_conditional=[
                    {
                        'if': {'row_index': 'odd'},
                        'backgroundColor': 'ghostwhite',
                    }
                ],
            ),
            html.Br(),
            html.Div(className='card', children=[
                html.Div(className='text-side', children=["Total Issues"]),
                html.Div(className='number-side', children=[w6_total_records], id="w6-total")
            ])
        ], className="grid-item"),
    ])
])

"""
Callback Definitions 
"""


# Callback affecting W1
@app.callback(
    Output('graph1', 'figure'), Output('w1-avg', 'children'), Output('w1-trend', 'children'),
    [Input('w1-keyword-dropdown', 'value'),
     Input('w1-year-start-input', 'value'),
     Input('w1-year-end-input', 'value'),
     ]
)
def update_w1(keyword, year_start, year_end):
    year_start = int(year_start)
    year_end = int(year_end)

    w1_updated_query = "CALL GetKeywordCitations('{}', {}, {});".format(keyword, year_start, year_end)
    w1_updated_result = mysql_utils.mysql_query(w1_updated_query)

    # Calculates the slope rate of change on publications per year over the period.
    w1_years_list = np.array([int(i) for i in w1_updated_result["year"].tolist()])
    w1_num_pubs_list = np.array([int(i) for i in w1_updated_result["keyword_count"].tolist()])
    w1_slope = np.polyfit(w1_years_list, w1_num_pubs_list, 1)
    w1_average = str(int(w1_num_pubs_list.mean()))

    return {'data': [{
                        'x': w1_updated_result["year"],
                        'y':  w1_updated_result["keyword_count"],
                        'type': 'line',
                        'name': 'Line chart'
                    }],
            'layout': {
                'title': 'Keyword Popularity',
                'xaxis': {'title': 'Year'},
                'yaxis': {'title': 'Num. Publications referencing Keyword'}
            }}, w1_average, f'{w1_slope[0]:.2f}'


# Callback affecting W2
@app.callback(
    [Output('w2-name', 'value'),
     Output('w2-phone', 'value'),
     Output('w2-email', 'value'),
     Output('w2-img', 'src'),
     ],
    [Input('w2-faculty-dropdown', 'value'),
     Input('w2-update', 'n_clicks')],
    [State('w2-faculty-dropdown', 'value'),
     State('w2-phone', 'value'),
     State('w2-email', 'value'),
     State('w2-img', 'src')
     ],
    allow_duplicate=True
)
def update_w2(faculty_name, n_clicks, name, phone, email, src):
    if callback_context.triggered[0]['prop_id'] == 'w2-faculty-dropdown.value':
        # Handle faculty selection change
        faculty_entry = mongodb_utils.mongodb_aggregate("faculty", [{"$match": {"name": faculty_name}}])
        name = faculty_entry[0]["name"]
        phone = faculty_entry[0]["phone"] if faculty_entry[0]["phone"] else ""
        email = faculty_entry[0]["email"] if faculty_entry[0]["email"] else ""
        img_src = faculty_entry[0]["photoUrl"] if faculty_entry[0]["photoUrl"] else ""
        if not utils.is_image_url(img_src):
            img_src = "/assets/default_profile_img.jpg"
    else:
        # Handle information update
        filter_stage = {"name": name}
        update_stage = {"$set": {"phone": phone, "email": email}}

        client = MongoClient(mongodb_utils.MongoDB_HOST, 27017)
        db = client[mongodb_utils.MongoDB_DB_NAME] 
        col = db["faculty"]
        
        col.update_one(filter_stage, update_stage)
        
        client.close()

        img_src = src
    
    return name, phone, email, img_src


# Callback affecting W4 (updated faculty pair selection)
# Input('w4-faculty-dropdown-1', 'value'), Input('w4-faculty-dropdown-2', 'value')
@app.callback(

    [Output('w4-table', 'data'), Output("w4-total", "children")],
    [Input('w4-update-f', 'n_clicks'),
     Input('w4-faculty-dropdown-1', 'value'),
     Input('w4-faculty-dropdown-2', 'value')],
    [State('w4-faculty-keyword', 'value'),
     State('w4-table', 'data'),
     ], allow_duplicate=True
)
# Callback affecting W4 (keyword insertion)
def update_w4_faculty_keywords(n_clicks, faculty_name_1, faculty_name_2, faculty_keyword, w4_table_data):

    if not ((callback_context.triggered[0]['prop_id'] == 'w4-faculty-dropdown-1.value')
            or (callback_context.triggered[0]['prop_id'] == 'w4-faculty-dropdown-2.value')):

        # Find associated faculty ID
        if faculty_keyword != "":
            # Get the faculty ID
            faculty_id_query = lambda faculty_name: "SELECT id FROM faculty WHERE name='{}'".format(faculty_name)
            faculty_1_id = mysql_utils.mysql_query(faculty_id_query(faculty_name_1))["id"].iloc[0]
            faculty_2_id = mysql_utils.mysql_query(faculty_id_query(faculty_name_2))["id"].iloc[0]

            print("Insert faculty ID: ", faculty_1_id, faculty_2_id)  # Debug

            # Create the keyword id
            keyword_id_query_result = mysql_utils.mysql_query(
                "SELECT id FROM keyword where name='{}'".format(faculty_keyword))
            
            # Keyword already exists in keyword table
            if len(keyword_id_query_result):
                keyword_id = int(keyword_id_query_result["id"].iloc[0])
            # Keyword doesn't exist in the keyword table
            else:
                keyword_id = int(mysql_utils.mysql_query("SELECT MAX(id) as max_id FROM keyword")["max_id"].iloc[0]) + 1
                # Insert into keyword table
                keyword_insertion_query = "INSERT INTO keyword (id, name) \
                                        VALUES ({}, '{}');".format(keyword_id, faculty_keyword)
                mysql_utils.mysql_query(keyword_insertion_query)
                print("Inserted keyword: ", faculty_keyword, " into keyword table")  # Debug

            # Insert into faculty_keyword, which triggers duplication deletion
            mysql_utils.mysql_query(mysql_queries.w4_faculty_keyword_insertion_transaction_query_list[0])
            mysql_utils.mysql_query(mysql_queries.w4_faculty_keyword_insertion_transaction_query_list[1]
                                    .format(faculty_1_id, keyword_id))
            mysql_utils.mysql_query(mysql_queries.w4_faculty_keyword_insertion_transaction_query_list[2]
                                    .format(faculty_2_id, keyword_id))
            mysql_utils.mysql_query(mysql_queries.w4_faculty_keyword_insertion_transaction_query_list[3])

    w4_query = "CALL GetFacultyPairKeywords('{}', '{}');".format(faculty_name_1, faculty_name_2)
    w4_result = mysql_utils.mysql_query(w4_query)

    if len(w4_result):
        w4_shared_keywords = w4_result["shared_keyword_names"].iloc[0].split(",")
        w4_table_content = [{"Keyword Names": keyword} for keyword in w4_shared_keywords]
        tot_shared_keywords = str(len(w4_table_content))
        return [w4_table_content, tot_shared_keywords]
    else:
        return [[{"Keyword Names": ""}], "0"]


# Callback affecting W5 (updated university name selection)
@app.callback(

    [Output('w5-table', 'data'), Output("w5-total", "children")],
    [Input('w5-university-dropdown', 'value')],
    [State('w5-table', 'data')]
)
def update_w5_faculty_h_index(university_name, w5_table_data):
    # Drop the existing view faculty_publication_view
    mysql_utils.mysql_query("DROP VIEW If EXISTS faculty_publication_view;")
    # Create a new faculty_publication_view view corresponding to the given university
    mysql_utils.mysql_query(mysql_queries.w5_view_creation_query.format(university_name))
    
    # Run the H-Index Query
    h_index_query_result = mysql_utils.mysql_query(mysql_queries.w5_h_index_creation_query)
    
    # Return the updated table to Dash
    return [h_index_query_result.to_dict('records'), str(len(h_index_query_result.to_dict('records')))]


if __name__ == '__main__':
    app.run_server(debug=True)
