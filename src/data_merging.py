import pandas as pd
import os
import glob

def merge_data():
    # Get all the files in the data directory
    df1 = pd.read_csv("data/actes-criminels.csv")
    df2 = pd.read_csv("data/rues-pietonnes.csv")
    df3 = pd.read_csv("data/feux-pietons.csv")
    df4 = pd.read_csv("data/collisions-routieres.csv")

    # Renaming latitude and longitude columns for consistency and adding 'Type' column
    df1 = df1.rename(columns={'LATITUDE': 'Latitude', 'LONGITUDE': 'Longitude'})
    df1['Type'] = 'actes-criminels'#score: 10

    df2 = df2.rename(columns={'LATITUDE': 'Latitude', 'LONGITUDE': 'Longitude'})
    df2['Type'] = 'rues-pietonnes'#score: 1

    df3 = df3.rename(columns={'Latitude': 'Latitude', 'Longitude': 'Longitude'})
    df3['Type'] = 'feux-pietons'#score: 3

    df4 = df4.rename(columns={'LOC_LAT': 'Latitude', 'LOC_LONG': 'Longitude'})
    df4['Type'] = 'collisions-routieres'#score: 7

    # Selecting only the required columns
    df1 = df1[['Type', 'Latitude', 'Longitude']]
    df2 = df2[['Type', 'Latitude', 'Longitude']]
    df3 = df3[['Type', 'Latitude', 'Longitude']]
    df4 = df4[['Type', 'Latitude', 'Longitude']]

    # Concatenating all dataframes
    merged_df = pd.concat([df1, df2, df3, df4])

    # Drop rows with missing values
    merged_df = merged_df.dropna()

    # Saving the merged dataframe to a new CSV file
    output_file = 'data/merged_data.csv'
    merged_df.to_csv(output_file, index=False)

    return merged_df