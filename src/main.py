import plotly.figure_factory as ff
import plotly.express as px
import pandas as pd
import h3
import data_merging

def lat_lon_to_h3(row):
    # Convert latitude and longitude to H3 hexagon ID
    hex_id = h3.geo_to_h3(row['Latitude'], row['Longitude'], resolution=8)  # You can adjust the resolution as needed
    return hex_id

def main():
    px.set_mapbox_access_token(open("src/.mapbox_token").read())
    df = data_merging.merge_data()

    # Add hexagon ID to the DataFrame
    df['Hex_ID'] = df.apply(lat_lon_to_h3, axis=1)

    fig = ff.create_hexbin_mapbox(
        data_frame=df, lat="Latitude", lon="Longitude",
        nx_hexagon=150, opacity=0.5, labels={"color": "Point Count"},
        min_count=1, color_continuous_scale="Viridis",
        #show_original_data=True,
        #original_data_marker=dict(size=4, opacity=0.6, color="deeppink")
    )

    fig.show()

    hex_value = '882baa4523fffff'  # Replace with the specific hex ID you are interested in
    filtered_df = df[df['Hex_ID'] == hex_value]

    if not filtered_df.empty:
        print(f"Points where Hex_ID equals '{hex_value}':")
        for index, row in filtered_df.iterrows():
            print(f"Latitude: {row['Latitude']}, Longitude: {row['Longitude']}")
    else:
        print(f"No points found for Hex_ID '{hex_value}'")

if __name__ == "__main__":
    main()
