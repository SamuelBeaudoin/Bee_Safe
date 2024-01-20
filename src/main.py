import plotly.figure_factory as ff
import plotly.express as px
import pandas as pd
import numpy as np
import data_merging
import plotly.express as px
import plotly.graph_objects as go
import h3
import folium
import geojson
import networkx as nx


def main():
    # Set your Mapbox access token here
    mapbox_access_token = 'pk.eyJ1IjoidHV0cmUiLCJhIjoiY2xybWRicGhyMHBiaDJrb3I3ZXFocTA2dSJ9.rBItPyF-B0-YPcl9W7KKHg'

    # Load your data
    data = data_merging.merge_data()
  
    # Function to convert coordinates to hexagons
    def lat_lng_to_hexagon(latitude, longitude, resolution=9):
        return h3.geo_to_h3(latitude, longitude, resolution)

    # Apply this function to create a hexagon ID for each point
    data['hex_id'] = data.apply(lambda row: lat_lng_to_hexagon(row['Latitude'], row['Longitude']), axis=1)

    # Calculate the average cost in each hexagon
    hexagon_average_cost = data.groupby('hex_id')['COST'].mean().reset_index()
    hexagon_average_cost.columns = ['hex_id', 'average_cost']

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

    # Plot using Plotly Express
    fig = px.choropleth_mapbox(hexagon_average_cost, geojson=geojson_hexagons, locations='hex_id', color='average_cost',
                            color_continuous_scale="Viridis", mapbox_style="mapbox://styles/mapbox/streets-v11",
                            zoom=10, center={"lat": data['Latitude'].mean(), "lon": data['Longitude'].mean()},
                            opacity=0.5)

    # Set the Mapbox access token for the figure
    fig.update_layout(mapbox_accesstoken=mapbox_access_token)
    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
    #fig.show()

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
    lat_A = 45.527507267584674
    lon_A = -73.6
    lat_B = 45.527507267584674
    lon_B = -73.61880594710823
    start_hex = lat_lng_to_hexagon(lat_A, lon_A)  # lat_A and lon_A for point A
    end_hex = lat_lng_to_hexagon(lat_B, lon_B)    # lat_B and lon_B for point B

    # Find the shortest path
    path = nx.shortest_path(G, source=start_hex, target=end_hex, weight='weight')

    # Get the center of each hexagon in the path
    path_centers = [h3.h3_to_geo(hex_id) for hex_id in path]

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

    fig.show()

if __name__ == "__main__": 
    main()