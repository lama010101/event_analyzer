import os
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
import time

def get_gps_coordinates(location_name):
    """
    Convert location name to GPS coordinates using geocoding
    Returns [latitude, longitude] or None if not found
    """
    if not location_name or location_name.lower() in ['unknown', 'unknown location']:
        return None
    
    try:
        # Initialize geocoder with a user agent
        geolocator = Nominatim(user_agent="historical_image_analyzer")
        
        # Add retry logic for better reliability
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Geocode the location
                location = geolocator.geocode(location_name, timeout=10)
                
                if location:
                    return [round(location.latitude, 4), round(location.longitude, 4)]
                else:
                    # Try with simplified location name
                    simplified_name = simplify_location_name(location_name)
                    if simplified_name != location_name:
                        simplified_location = geolocator.geocode(simplified_name, timeout=10)
                        if simplified_location:
                            return [round(simplified_location.latitude, 4), round(simplified_location.longitude, 4)]
                    break
                    
            except GeocoderTimedOut:
                if attempt < max_retries - 1:
                    time.sleep(1)  # Wait before retry
                    continue
                else:
                    print(f"Geocoding timeout for location: {location_name}")
                    break
                    
            except GeocoderServiceError as e:
                print(f"Geocoding service error: {str(e)}")
                break
        
        return None
        
    except Exception as e:
        print(f"Error geocoding location '{location_name}': {str(e)}")
        return None

def simplify_location_name(location_name):
    """
    Simplify location name for better geocoding success
    """
    if not location_name:
        return location_name
    
    # Remove common descriptive words that might interfere with geocoding
    words_to_remove = [
        'near', 'around', 'vicinity of', 'area of', 'region of',
        'front of', 'outside', 'inside', 'at the', 'in the'
    ]
    
    simplified = location_name.lower()
    for word in words_to_remove:
        simplified = simplified.replace(word, '')
    
    # Clean up extra spaces
    simplified = ' '.join(simplified.split())
    
    # If we have a comma-separated location, try just the main parts
    parts = simplified.split(',')
    if len(parts) >= 2:
        # Try just the city and country
        return f"{parts[0].strip()}, {parts[-1].strip()}"
    
    return simplified.title()

def validate_gps_coordinates(gps_coords):
    """
    Validate GPS coordinates are within valid ranges
    """
    if not gps_coords or len(gps_coords) != 2:
        return False
    
    lat, lon = gps_coords
    
    # Check latitude range (-90 to 90)
    if not isinstance(lat, (int, float)) or lat < -90 or lat > 90:
        return False
    
    # Check longitude range (-180 to 180)
    if not isinstance(lon, (int, float)) or lon < -180 or lon > 180:
        return False
    
    return True

def format_confidence_display(confidence_dict):
    """
    Format confidence scores for display
    """
    if not isinstance(confidence_dict, dict):
        return "No confidence data"
    
    formatted = []
    for key, value in confidence_dict.items():
        try:
            score = int(value)
            formatted.append(f"{key.title()}: {score}%")
        except:
            formatted.append(f"{key.title()}: N/A")
    
    return " | ".join(formatted)

def save_analysis_result(result, filename=None):
    """
    Save analysis result to JSON file
    """
    if filename is None:
        timestamp = int(time.time())
        filename = f"historical_analysis_{timestamp}.json"
    
    try:
        import json
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        return filename
    except Exception as e:
        print(f"Error saving result to file: {str(e)}")
        return None

def clean_text_for_analysis(text):
    """
    Clean extracted text for better analysis
    """
    if not text:
        return ""
    
    # Remove extra whitespace
    cleaned = ' '.join(text.split())
    
    # Remove very short words that might be OCR artifacts
    words = cleaned.split()
    filtered_words = [word for word in words if len(word) >= 2]
    
    return ' '.join(filtered_words)

def get_historical_keywords():
    """
    Return list of keywords that might indicate historical significance
    """
    return [
        # Time periods
        'war', 'battle', 'revolution', 'independence', 'liberation',
        'protest', 'demonstration', 'march', 'rally', 'uprising',
        'ceremony', 'celebration', 'memorial', 'commemoration',
        'treaty', 'agreement', 'conference', 'summit', 'meeting',
        
        # Objects/People
        'president', 'leader', 'general', 'commander', 'politician',
        'soldier', 'military', 'army', 'navy', 'air force',
        'civilian', 'citizen', 'crowd', 'masses', 'people',
        
        # Locations
        'capital', 'city', 'town', 'square', 'plaza', 'street',
        'building', 'monument', 'memorial', 'palace', 'government',
        'embassy', 'headquarters', 'base', 'front', 'border',
        
        # Events
        'assassination', 'speech', 'declaration', 'announcement',
        'victory', 'defeat', 'surrender', 'armistice', 'ceasefire',
        'invasion', 'occupation', 'liberation', 'evacuation'
    ]
