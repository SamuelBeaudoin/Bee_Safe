import plotly.figure_factory as ff
import plotly.express as px
import pandas as pd
import numpy as np
import data_merging
import plotly.express as px
import plotly.graph_objects as go
import h3



# Define a custom aggregation function to calculate the average of the "cost" attribute for each row
def custom_agg(row):
    return np.mean(row['COST'])

def main():
    px.set_mapbox_access_token(open(".mapbox_token").read())
    df = data_merging.merge_data()

    fig = ff.create_hexbin_mapbox(
        data_frame=df, lat="Latitude", lon="Longitude",
        nx_hexagon=150, opacity=0.5, labels={"color": "Cost"},
        min_count=1, color_continuous_scale="Viridis",
        color="COST", 
        agg_func=np.mean, 
        range_color=[-20,20]
        # show_original_data=True,
        #original_data_marker=dict(size=4, opacity=0.6, color="deeppink")
        
    )

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

    # Plot using Plotly Express
    fig = px.choropleth_mapbox(hexagon_counts, geojson=geojson_hexagons, locations='hex_id', color='count',
                            color_continuous_scale="Viridis", mapbox_style="mapbox://styles/mapbox/streets-v11",
                            zoom=10, center={"lat": data['Latitude'].mean(), "lon": data['Longitude'].mean()},
                            opacity=0.5)

    # Set the Mapbox access token for the figure
    fig.update_layout(mapbox_accesstoken=mapbox_access_token)
    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
    fig.show()

if __name__ == "__main__": 
    main()