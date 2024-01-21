import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import plotly.express as px
import plotly.graph_objects as go
import h3
import data_merging
import dash_bootstrap_components as dbc
import networkx as nx
from opencage.geocoder import OpenCageGeocode

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Set your Mapbox access token here
mapbox_access_token = 'pk.eyJ1IjoidHV0cmUiLCJhIjoiY2xybWRicGhyMHBiaDJrb3I3ZXFocTA2dSJ9.rBItPyF-B0-YPcl9W7KKHg'

opencage_api_key = 'd0d560b267c94cdabd9ffb677e28ce29'
geocoder = OpenCageGeocode(opencage_api_key)

# Load your data
data = data_merging.merge_data()

custom_color_scale = [
    [0.0, 'rgb(0, 255, 0)'],    # Green at 0, corresponding to cost 1
    [0.15, 'rgb(255, 255, 0)'],
    [0.35, 'rgb(255, 150, 0)'], # Yellow at 0.25, around cost 2
    [0.55, 'rgb(255, 0, 0)'],  # Orange at 0.5, around cost 2.5
    # More gradual change between 2.5 and 10
    [0.7, 'rgb(128, 0, 0)'],   # Red at 0.75, around cost 6
    [0.8, 'rgb(165,42,42)'],     # Dark red at 1, corresponding to cost 10
    [1.0, 'rgb(0, 0, 0)']
]
  
# Function to convert coordinates to hexagons
def lat_lng_to_hexagon(latitude, longitude, resolution=10):
    return h3.geo_to_h3(latitude, longitude, resolution)

# Apply this function to create a hexagon ID for each point
data['hex_id'] = data.apply(lambda row: lat_lng_to_hexagon(row['Latitude'], row['Longitude']), axis=1)

# Calculate the average cost in each hexagon
hexagon_average_cost = data.groupby('hex_id')['COST'].mean().reset_index()
hexagon_average_cost.columns = ['hex_id', 'average_cost']

input_values = {}

# Convert hexagon IDs to GeoJSON polygons
def hexagon_to_geojson(hex_id):
    hex_boundary = h3.h3_to_geo_boundary(hex_id, geo_json=False)
    coordinates = [[lon, lat] for lat, lon in hex_boundary]
    coordinates.append(coordinates[0])
    return {"type": "Polygon", "coordinates": [coordinates]}

hexagon_average_cost['geometry'] = hexagon_average_cost['hex_id'].apply(hexagon_to_geojson)

# Create a DataFrame suitable for Plotly Express
geojson_hexagons = {
    "type": "FeatureCollection",
    "features": [
        {"type": "Feature", "geometry": geom, "id": hex_id}
        for hex_id, geom in zip(hexagon_average_cost['hex_id'], hexagon_average_cost['geometry'])
    ]
}

isFetchingLatLong=False

# Layout of the Dash app
app.layout = dbc.Container([
    html.H1("Street Safety", className="mt-4 mb-4"),

    dbc.Row([
        dbc.Col([
            html.Label("Current Location Address:   "),
            dcc.Input(id='current-address-input', type='text', placeholder="Enter Address", value = "1450 Rue Guy Montreal", className="mb-2"),
        ], md=6),

        dbc.Col([
            html.Label("Destination Address:   "),
            dcc.Input(id='dest-address-input', type='text', placeholder="Enter Address", value = "1450 Rue Guy Montreal", className="mb-2"),
        ], md=6)
    ]),

    dcc.Loading(
        id="loading-geocode",
        type="default",
        children=[
            html.Div([
                dcc.Graph(id='hexagon-map', clickData=None),
            ]),
        ]
    ),
       
    html.Div(id='hexagon-stats')
])


# Callback to update the map based on address inputs
@app.callback(
    Output('hexagon-map', 'figure'),
    [Input('current-address-input', 'value'),
     Input('dest-address-input', 'value')]
)
def update_map(current_address, dest_address):
    global isFetchingLatLong
    if current_address and dest_address:
        # Geocode the addresses to coordinates
        isFetchingLatLong=True

        current_location = geocoder.geocode(current_address)
        dest_location = geocoder.geocode(dest_address)

        if current_location and dest_location:
            current_lat, current_lon = current_location[0]['geometry']['lat'], current_location[0]['geometry']['lng']
            dest_lat, dest_lon = dest_location[0]['geometry']['lat'], dest_location[0]['geometry']['lng']
        
        isFetchingLatLong=False


    # Update the map based on user input with the custom color scale
    fig = px.choropleth_mapbox(hexagon_average_cost, geojson=geojson_hexagons, locations='hex_id', color='average_cost',
                                color_continuous_scale=custom_color_scale, mapbox_style="mapbox://styles/mapbox/streets-v11",
                                zoom=10, center={"lat": current_lat, "lon": current_lon},
                                opacity=0.5, hover_data={'hex_id': False, 'average_cost': False})

    # Add red markers for the current location and destination
    fig.add_trace(go.Scattermapbox(
        mode="markers",
        lon=[current_lon, dest_lon],
        lat=[current_lat, dest_lat],
        marker=dict(
            size=10,
            color="red"
        ),
        text=["Current Location", "Destination"],
        hoverinfo="none"
    ))

     # Set the Mapbox access token for the figure
    fig.update_layout(mapbox_accesstoken=mapbox_access_token)
    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})

    # Create a graph
    G = nx.Graph()

    # Add nodes (hexagons) to the graph
    for index, row in hexagon_average_cost.iterrows():
        G.add_node(row['hex_id'], cost=row['average_cost'])

    # Define a function to find adjacent hexagons
    def find_adjacent_hexagons(hex_id):
        # Using h3 library to find neighbors
        return h3.hex_ring(hex_id, 1)

    # Add edges between adjacent hexagons
    for hex_id in G.nodes:
        neighbors = find_adjacent_hexagons(hex_id)
        for neighbor in neighbors:
            if neighbor in G.nodes:
                # Define the cost of the edge (you can adjust this logic)
                edge_cost = (G.nodes[hex_id]['cost'] + G.nodes[neighbor]['cost']) / 2
                G.add_edge(hex_id, neighbor, weight=edge_cost)

    # Define your start and end hexagons based on points A and B
    start_hex = lat_lng_to_hexagon(current_lat, current_lon)  # lat_A and lon_A for point A
    end_hex = lat_lng_to_hexagon(dest_lat, dest_lon)    # lat_B and lon_B for point B

    # Find the shortest path
    path = nx.shortest_path(G, source=start_hex, target=end_hex, weight='weight', method='dijkstra')

    # Get the center of each hexagon in the path
    path_centers = [h3.h3_to_geo(hex_id) for hex_id in path]

    # Update the map's center and zoom to focus on the path
    if path_centers:
        # Calculate the average latitude and longitude of the path for centering
        avg_lat = sum(lat for lat, lon in path_centers) / len(path_centers)
        avg_lon = sum(lon for lat, lon in path_centers) / len(path_centers)
        center = {"lat": avg_lat, "lon": avg_lon}

        # Adjust the zoom level based on the distance between the points
        # You can fine-tune the zoom level based on your specific requirements
        distance = h3.point_dist((current_lat, current_lon), (dest_lat, dest_lon), unit='m')
        if distance < 1000:  # Less than 1 km
            zoom = 14
        elif distance < 5000:  # Less than 5 km
            zoom = 12
        else:
            zoom = 10
    else:
        center = {"lat": current_lat, "lon": current_lon}
        zoom = 10

    fig.update_layout(mapbox={"center": center, "zoom": zoom})

    # Add the path as a line on the map
    path_lon = [lon for lat, lon in path_centers]
    path_lat = [lat for lat, lon in path_centers]

    fig.add_trace(go.Scattermapbox(
        mode = "lines",
        lon = path_lon,
        lat = path_lat,
        marker = {'size': 10},
        line = {'width': 3, 'color': 'red'},
        hoverinfo="none"
    ))

    # Return the figure
    return fig

@app.callback(
    Output('hexagon-stats', 'children'),
    [Input('hexagon-map', 'clickData')],
    [State('hexagon-map', 'figure')]
)
def display_hexagon_stats(clickData, figure):
    if clickData:
        
        hex_id = clickData['points'][0]['location']
        # Find the cost associated with the clicked hexagon
        cost = hexagon_average_cost[hexagon_average_cost['hex_id'] == hex_id]['average_cost'].iloc[0]
        return f" Average Cost: {cost}"
    

    return "Click on a hexagon to see its stats."

if __name__ == '__main__':
    app.run_server(debug=True)