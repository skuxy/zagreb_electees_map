import csv
import os
import time
import folium

from geopy.exc import GeocoderTimedOut
from geopy.geocoders import Nominatim


geolocator = Nominatim(user_agent="electees", timeout=10)
all_addresses = {}

def read_csv(file_path):
    """
    Reads a CSV file and returns a list of dictionaries representing the rows.
    """
    with open(file_path, mode='r', encoding='utf-8') as file:
        reader = csv.DictReader(file, delimiter=';')
        return [row for row in reader]


def safe_geocode(address, max_retries=3):
    for _ in range(max_retries):
        try:
            location = geolocator.geocode(address)
            return (location.latitude, location.longitude) if location else (None, None)
        except GeocoderTimedOut:
            print(f"Retrying {address}...")
            time.sleep(2)  # Wait before retrying
    return None, None

def fetch_coordinates_from_csv(file_path):
    """
    Reads a CSV file and fetches coordinates for each address.
    """
    data = read_csv(file_path)
    for row in data:
        name, address = row['name'], row['address']
        if address:
            coordinates = safe_geocode(address)
            if coordinates:
                print(f"Fetched coordinates for {name}: {coordinates}")
                row['latitude'], row['longitude'] = coordinates
            else:
                row['latitude'], row['longitude'] = None, None
    return data


def create_map_from_file(csv_path):
    """
    Reads a CSV file and creates a map with markers for each address.
    """
    data = fetch_coordinates_from_csv(csv_path)
    all_addresses[csv_path] = data

    #save data to a temp file
    save_coordinates(csv_path, data)

    # Create a map centered around the first address
    map_points(csv_path, data)


def map_points(csv_path, data):
    if data and data[0]['latitude'] and data[0]['longitude']:
        map_center = (data[0]['latitude'], data[0]['longitude'])
    else:
        map_center = (0, 0)  # Default to (0, 0) if no valid coordinates
    map_osm = folium.Map(location=map_center, zoom_start=12, tiles='OpenStreetMap')
    for row in data:
        name = row['name']
        latitude = row.get('latitude')
        longitude = row.get('longitude')
        if latitude and longitude:
            folium.Marker(
                location=[latitude, longitude],
                popup=name,
                icon=folium.Icon(color='blue', icon='info-sign')
            ).add_to(map_osm)
    map_osm.save('results/' + csv_path.replace('.csv', '.html'))


def save_coordinates(csv_path, data):
    with open('temp/' + csv_path.replace('.csv', '_temp.csv'), 'w', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=data[0].keys(), delimiter=';')
        writer.writeheader()
        writer.writerows(data)


def load_csvs():
    for dirpath, dirnames, electees_list in os.walk('data/'):
        for file in electees_list:
            if file.endswith('.csv'):
                print(f"Processing {file}...")
                create_map_from_file(dirpath + file)
                print(f"Map saved for {file}.")
            else:
                print(f"Skipping {file}, not a CSV file.")

colors = {
    'bernardic': 'lightblue',
    'dalija': 'darkgreen',
    'hdz': 'blue',
    'hocemo': 'beige',
    'jonjic': 'black',
    'kalinic': 'gray',
    'kolakusic': 'purple',
    'lovric': 'pink',
    'msr':  'white',
    'mozemo': 'green',
    'most': 'orange',
    'rf': 'red'
}

def color_all():
    map_osm = folium.Map(location=(45.1, 15.2), zoom_start=7, tiles='OpenStreetMap')

    for party, color in colors.items():
        with open('temp/data/' + party + '_temp.csv', 'r', encoding='utf-8') as file:
            group = folium.FeatureGroup(name=party)
            reader = csv.DictReader(file, delimiter=';')
            for row in reader:
                name = row['name']
                address = row['address']
                latitude = row['latitude']
                longitude = row['longitude']
                if latitude and longitude:
                    folium.Marker(
                        location=[latitude, longitude],
                        popup=party + '\n' + name + '\n' + address,
                        icon=folium.Icon(color=color, icon='info-sign')
                    ).add_to(group)

            group.add_to(map_osm)

    folium.LayerControl(collappsed=False, ).add_to(map_osm)
    map_osm.save('results/all_parties_map.html')

if __name__ == "__main__":
    if not os.path.exists('results') and os.path.exists('temp'):
        os.makedirs('results')
        os.makedirs('temp')
        load_csvs()

    color_all()
    print("All maps have been created and saved.")


