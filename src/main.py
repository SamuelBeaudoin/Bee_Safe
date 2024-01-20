import plotly.figure_factory as ff
import plotly.express as px
import pandas as pd
import data_merging

def main():
    px.set_mapbox_access_token(open(".mapbox_token").read())
    df = data_merging.merge_data()

    fig = ff.create_hexbin_mapbox(
        data_frame=df, lat="Latitude", lon="Longitude",
        nx_hexagon=150, opacity=0.5, labels={"color": "Point Count"},
        min_count=1, color_continuous_scale="Viridis",
        #show_original_data=True,
        #original_data_marker=dict(size=4, opacity=0.6, color="deeppink")
    )
    fig.show()

if __name__ == "__main__": 
    main()