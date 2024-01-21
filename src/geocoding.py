import requests

def get_latitude_longitude(address, api_key) -> tuple(float, float):
    base_url = 'https://api.opencagedata.com/geocode/v1/json'
    
    params = {'q': address, 'key': api_key}
    response = requests.get(base_url, params=params)
    data = response.json()

    if data['status']['code'] == 200:
        location = data['results'][0]['geometry']
        latitude = location['lat']
        longitude = location['lng']

        print(f'Address: {address}')
        print(f'Latitude: {latitude}')
        print(f'Longitude: {longitude}')
    else:
        print(f'Error: {data["status"]["message"]}')
    
    return (latitude, longitude)

# Example usage
# api_key = 'd0d560b267c94cdabd9ffb677e28ce29'
# address_to_geocode = '1450 Guy St Montreal'
# print(get_latitude_longitude(address_to_geocode, api_key))
