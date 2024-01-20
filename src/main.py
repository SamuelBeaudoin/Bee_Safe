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
def lat_lng_to_hexagon(latitude, longitude, resolution=9):
    return h3.geo_to_h3(latitude, longitude, resolution)

# Apply this function to create a hexagon ID for each point
data['hex_id'] = data.apply(lambda row: lat_lng_to_hexagon(row['Latitude'], row['Longitude']), axis=1)

# Count the number of points in each hexagon
hexagon_counts = data['hex_id'].value_counts().reset_index()
hexagon_counts.columns = ['hex_id', 'count']

# Convert hexagon IDs to GeoJSON polygons with correct coordinate order
def hexagon_to_geojson(hex_id):
    hex_boundary = h3.h3_to_geo_boundary(hex_id, geo_json=False)  # Get boundary in (lat, lon)
    # Convert to (lon, lat) for GeoJSON
    coordinates = [[lon, lat] for lat, lon in hex_boundary]
    coordinates.append(coordinates[0])  # Close the polygon by repeating the first point
    return {"type": "Polygon", "coordinates": [coordinates]}

hexagon_counts['geometry'] = hexagon_counts['hex_id'].apply(hexagon_to_geojson)

# Create a DataFrame suitable for Plotly Express
geojson_hexagons = {
    "type": "FeatureCollection",
    "features": [
        {"type": "Feature", "geometry": geom, "id": hex_id}
        for hex_id, geom in zip(hexagon_counts['hex_id'], hexagon_counts['geometry'])
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
    # Update the map based on user input
    fig = px.choropleth_mapbox(hexagon_counts, geojson=geojson_hexagons, locations='hex_id', color='count',
                                color_continuous_scale="Viridis", mapbox_style="mapbox://styles/mapbox/streets-v11",
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
    fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})

    return fig

if __name__ == '__main__':
    app.run_server(debug=True)
