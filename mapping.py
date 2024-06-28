from geopy.geocoders import Nominatim
import folium

def get_coordinates(address):
    geolocator = Nominatim(user_agent="map_plotter")
    location = geolocator.geocode(address)
    if location:
        return location.latitude, location.longitude
    else:
        return None, None

def plot_on_map(address):
    # Get coordinates for the address
    latitude, longitude = get_coordinates(address)
    if latitude is None or longitude is None:
        print("Coordinates not found for the given address.")
        return

    # Create a map centered around the coordinates
    map_plot = folium.Map(location=[latitude, longitude], zoom_start=15)

    # Add a marker for the address
    folium.Marker([latitude, longitude], popup=address).add_to(map_plot)

    # Save the map to an HTML file
    map_plot.save("map.png")

    print("Map plotted and saved as 'map.html'.")

