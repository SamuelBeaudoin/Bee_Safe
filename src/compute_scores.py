import pandas as pd
import os
import glob

# SCALE IS 0 to 10

# Function for computing crime severity, for the actes-criminels data set
# Simply adds a COST field depending on the crime 
def preprocess_crime_data():
    df = pd.read_csv("../data/actes-criminels.csv")

    # Severity of each crime
    crime_cost_severity= {
        "Méfait": 2,
        "Introduction": 3,
        "Vols qualifiés": 4,
        "Vol dans / sur véhicule à moteur": 6,
        "Vol de véhicule à moteur": 6,
        "Infractions entrainant la mort": 10
    }

    df['COST']=df['CATEGORIE'].map(crime_cost_severity)

    return df

def proprocess_car_crash_data():
    df = pd.read_csv("../data/collisions-routieres.csv")


    GRAVITY_COSTS = {
        "Dommages matériels inférieurs au seuil de rapportage": 3,
	    "Dommages matériels seulement" : 3,
	    "Léger" : 4,
	    "Grave": 5,
	    "Mortel": 8
    }

    def compute_cost(row):
        GRAVITY = GRAVITY_COSTS[row['GRAVITE']]
        NB_MORTS=row['NB_MORTS']
        NB_BLESSES_GRAVES=row['NB_BLESSES_GRAVES']
        NB_BLESSES_LEGERS=row['NB_BLESSES_LEGERS']
        
        weight = GRAVITY + NB_MORTS*0.5 + NB_BLESSES_GRAVES*0.25 + NB_BLESSES_LEGERS*0.1
        
        if weight > 10:
            return 10
        else:
            return weight


    df['COST'] = df.apply(compute_cost, axis=1)
    return df

def preprocess_rue_pieton():
    df = pd.read_csv("../data/rues-pietonnes.csv")

    def compute_cost(row):
        if row['VOIE_CYCLABLE'] == 'Oui':
            return -5
        else:
            return -7
        
    df['COST'] = df.apply(compute_cost, axis=1)
    return df


def preprocess_feux_pieton():
    pass









