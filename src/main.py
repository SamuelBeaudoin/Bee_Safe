import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import plotly.express as px
import plotly.graph_objects as go
import h3
import data_merging
import dash_bootstrap_components as dbc
import folium
import geojson
import networkx as nx

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Set your Mapbox access token here
mapbox_access_token = 'pk.eyJ1IjoidHV0cmUiLCJhIjoiY2xybWRicGhyMHBiaDJrb3I3ZXFocTA2dSJ9.rBItPyF-B0-YPcl9W7KKHg'

# Load your data
data = data_merging.merge_data()
  
# Function to convert coordinates to hexagons
def lat_lng_to_hexagon(latitude, longitude, resolution=10):
    return h3.geo_to_h3(latitude, longitude, resolution)

# Apply this function to create a hexagon ID for each point
data['hex_id'] = data.apply(lambda row: lat_lng_to_hexagon(row['Latitude'], row['Longitude']), axis=1)

# Calculate the average cost in each hexagon
hexagon_average_cost = data.groupby('hex_id')['COST'].mean().reset_index()
hexagon_average_cost.columns = ['hex_id', 'average_cost']

input_values={}

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

# Layout of the Dash app
app.layout = dbc.Container([
    html.H1("Hexagon Map", className="mt-4 mb-4"),
    
    dbc.Row([
        dbc.Col([
            html.Label("Current Location"),
            dcc.Input(id='current-lat-input', type='number', placeholder="Enter Latitude", value=data['Latitude'].mean(), className="mb-2"),
            dcc.Input(id='current-lon-input', type='number', placeholder="Enter Longitude", value=data['Longitude'].mean(), className="mb-4")
        ], md=6),
        
        dbc.Col([
            html.Label("Destination"),
            dcc.Input(id='dest-lat-input', type='number', placeholder="Enter Latitude", value=data['Latitude'].mean(), className="mb-2"),
            dcc.Input(id='dest-lon-input', type='number', placeholder="Enter Longitude", value=data['Longitude'].mean(), className="mb-4")
        ], md=6)
    ]),

    dcc.Graph(id='hexagon-map')
])

# Callback to update the map based on user input
@app.callback(
    Output('hexagon-map', 'figure'),
    [Input('current-lat-input', 'value'),
     Input('current-lon-input', 'value'),
     Input('dest-lat-input', 'value'),
     Input('dest-lon-input', 'value')]
)
def update_map(current_lat, current_lon, dest_lat, dest_lon):

    input_values['current_lat'] = current_lat
    input_values['current_lon'] = current_lon
    input_values['dest_lat'] = dest_lat
    input_values['dest_lon'] = dest_lon
    # Update the map based on user input
    fig = px.choropleth_mapbox(hexagon_average_cost, geojson=geojson_hexagons, locations='hex_id', color='average_cost',
                                color_continuous_scale="Icefire", mapbox_style="mapbox://styles/mapbox/streets-v11",
                                zoom=10, center={"lat": current_lat, "lon": current_lon},
                                opacity=0.5)

    # Add red markers for the current location and destination
    fig.add_trace(go.Scattermapbox(
        mode="markers",
        lon=[current_lon, dest_lon],
        lat=[current_lat, dest_lat],
        marker=dict(
            size=10,
            color="red"
        ),
        text=["Current Location", "Destination"]
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
    path = nx.shortest_path(G, source=start_hex, target=end_hex, weight='weight')

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
        line = {'width': 3, 'color': 'red'}
    ))

    # Return the figure
    return fig


if __name__ == '__main__':
    app.run_server(debug=True)
