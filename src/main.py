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
    fig.show()

if __name__ == "__main__": 
    main()