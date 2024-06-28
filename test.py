from geopy.geocoders import Photon
from geopy.distance import geodesic

def get_coordinates(address):
    """Get latitude and longitude coordinates for a given address."""
    geolocator = Photon(user_agent="geoapiExercises")
    location = geolocator.geocode(address)
    if location:
        return location.latitude, location.longitude
    else:
        print("Address not found.")
        return None, None

def calculate_distance(address1, address2):
    """Calculate the distance between two addresses."""
    # Get coordinates for both addresses
    lat1, lon1 = get_coordinates(address1)
    lat2, lon2 = get_coordinates(address2)

    if lat1 is not None and lon1 is not None and lat2 is not None and lon2 is not None:
        # Calculate distance using Haversine formula
        distance = geodesic((lat1, lon1), (lat2, lon2)).kilometers
        return distance
    else:
        return None

if __name__ == "__main__":
    # Example addresses
    address1 = "Times Square, New York, NY"
    address2 = "Central Park, New York, NY"

    # Calculate distance
    distance = calculate_distance(address1, address2)

    if distance is not None:
        print(f"The distance between '{address1}' and '{address2}' is {distance:.2f} kilometers.")
    else:
        print("Distance calculation failed. Please check the provided addresses.")
