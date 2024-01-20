import plotly.figure_factory as ff
import plotly.express as px

px.set_mapbox_access_token(open("src/.mapbox_token").read())
df = px.data.carshare()

fig = ff.create_hexbin_mapbox(
    data_frame=df, lat="centroid_lat", lon="centroid_lon",
    nx_hexagon=25, opacity=0.5, labels={"color": "Point Count"},
    min_count=1, color_continuous_scale="Viridis",
    show_original_data=True,
    original_data_marker=dict(size=4, opacity=0.6, color="deeppink")
)
fig.show()
