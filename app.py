from flask import Flask, render_template, request, jsonify, redirect, url_for
from dotenv import load_dotenv
import os
import requests
from datetime import datetime
import logging

# Load environment variables
load_dotenv()

# Debug environment loading
print("=== ENVIRONMENT DEBUG ===")
print(f"Current working directory: {os.getcwd()}")
print(f"Environment file exists: {os.path.exists('.env')}")
print(f"SECRET_KEY from env: {os.getenv('SECRET_KEY')}")
print(f"WEATHER_API_KEY from env: {os.getenv('WEATHER_API_KEY')}")
print("=========================")

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'coastalguard-dev-key-2025')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Gujarat coastal cities with coordinates
GUJARAT_CITIES = {
    'Ahmedabad': {'lat': 23.0225, 'lon': 72.5714, 'icon': 'fa-anchor'},
    'Surat': {'lat': 21.1702, 'lon': 72.8311, 'icon': 'fa-ship'},
    'Vadodara': {'lat': 22.3072, 'lon': 73.1812, 'icon': 'fa-industry'},
    'Rajkot': {'lat': 22.3039, 'lon': 70.8022, 'icon': 'fa-cog'},
    'Bhavnagar': {'lat': 21.7645, 'lon': 72.1519, 'icon': 'fa-anchor'},
    'Jamnagar': {'lat': 22.4707, 'lon': 70.0577, 'icon': 'fa-oil-well'},
    'Porbandar': {'lat': 21.6417, 'lon': 69.6293, 'icon': 'fa-ship'},
    'Dwarka': {'lat': 22.2394, 'lon': 68.9678, 'icon': 'fa-mosque'},
    'Veraval': {'lat': 20.9077, 'lon': 70.3665, 'icon': 'fa-fish'},
    'Okha': {'lat': 22.4672, 'lon': 69.0717, 'icon': 'fa-lighthouse'}
}

def fetch_weather_data(city_name, lat, lon):
    """Fetch weather data from OpenWeatherMap API"""
    # Force reload environment variables
    load_dotenv(override=True)
    
    api_key = os.getenv('WEATHER_API_KEY')
    
    # Enhanced debugging
    print("=== WEATHER API DEBUG ===")
    print(f"Raw API key from env: '{api_key}'")
    print(f"API key type: {type(api_key)}")
    print(f"API key equals placeholder: {api_key == 'your-openweathermap-api-key'}")
    print(f"Working directory: {os.getcwd()}")
    print(f".env file exists: {os.path.exists('.env')}")
    print("========================")
    
    # Check all possible sources
    if not api_key:
        print("Trying to read .env file directly...")
        try:
            with open('.env', 'r') as f:
                content = f.read()
                print("Content of .env file:")
                for line in content.split('\n'):
                    if 'WEATHER_API_KEY' in line:
                        print(f"Found line: {line}")
        except Exception as e:
            print(f"Error reading .env file: {e}")
    
    if not api_key or api_key.strip() == '' or api_key == 'your-openweathermap-api-key':
        logger.warning("Weather API key not configured properly")
        return get_mock_weather_data(city_name)
    
    try:
        # Current weather API call
        url = f"http://api.openweathermap.org/data/2.5/weather"
        params = {
            'lat': lat,
            'lon': lon,
            'appid': api_key.strip(),  # Strip any whitespace
            'units': 'metric'
        }
        
        logger.info(f"Making API call to OpenWeatherMap for {city_name}")
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        logger.info(f"Successfully fetched weather data for {city_name}")
        return {
            'city': city_name,
            'temperature': round(data['main']['temp']),
            'feels_like': round(data['main']['feels_like']),
            'humidity': data['main']['humidity'],
            'pressure': data['main']['pressure'],
            'wind_speed': round(data['wind']['speed'] * 3.6),  # Convert m/s to km/h
            'wind_direction': data['wind'].get('deg', 0),
            'description': data['weather'][0]['description'].title(),
            'icon': data['weather'][0]['icon'],
            'visibility': data.get('visibility', 10000) / 1000,  # Convert to km
            'last_updated': datetime.now().strftime('%H:%M'),
            'threat_level': calculate_threat_level(data)
        }
        
    except requests.exceptions.RequestException as e:
        logger.error(f"API request error for {city_name}: {e}")
        return get_mock_weather_data(city_name)
    except KeyError as e:
        logger.error(f"Missing data in API response for {city_name}: {e}")
        return get_mock_weather_data(city_name)
    except Exception as e:
        logger.error(f"Unexpected error for {city_name}: {e}")
        return get_mock_weather_data(city_name)

def get_mock_weather_data(city_name):
    """Return mock weather data when API is unavailable"""
    import random
    return {
        'city': city_name,
        'temperature': random.randint(25, 35),
        'feels_like': random.randint(26, 38),
        'humidity': random.randint(60, 85),
        'pressure': random.randint(1010, 1020),
        'wind_speed': random.randint(10, 25),
        'wind_direction': random.randint(0, 360),
        'description': random.choice(['Clear Sky', 'Few Clouds', 'Partly Cloudy', 'Light Breeze']),
        'icon': '01d',
        'visibility': round(random.uniform(8, 15), 1),
        'last_updated': datetime.now().strftime('%H:%M'),
        'threat_level': 'green'
    }

def calculate_threat_level(weather_data):
    """Calculate threat level based on weather conditions"""
    temp = weather_data['main']['temp']
    wind_speed = weather_data['wind']['speed'] * 3.6  # Convert to km/h
    pressure = weather_data['main']['pressure']
    
    # Simple threat calculation logic
    if temp > 40 or wind_speed > 50 or pressure < 990:
        return 'red'
    elif temp > 35 or wind_speed > 30 or pressure < 1000:
        return 'yellow'
    else:
        return 'green'

def generate_mock_alerts():
    """Generate mock AI alerts for demonstration"""
    alerts = [
        {
            'city': 'Ahmedabad',
            'level': 'green',
            'message': 'All Clear - Normal weather patterns detected',
            'detail': 'Stable atmospheric conditions with no immediate threats.',
            'time': '5 minutes ago'
        },
        {
            'city': 'Surat',
            'level': 'yellow',
            'message': 'Monitor - Elevated wind speeds',
            'detail': 'Wind speeds slightly above normal. Continue monitoring.',
            'time': '12 minutes ago'
        },
        {
            'city': 'Dwarka',
            'level': 'green',
            'message': 'All Clear - Stable conditions',
            'detail': 'All parameters within normal ranges.',
            'time': '18 minutes ago'
        }
    ]
    return alerts

def generate_mock_reports():
    """Generate mock community reports"""
    reports = [
        {
            'title': 'Unusual Wave Activity',
            'reporter': 'Fisherman - Veraval',
            'description': 'Higher than normal waves observed near the port area',
            'time': '1h ago',
            'priority': 'blue'
        },
        {
            'title': 'Weather Update',
            'reporter': 'Resident - Dwarka',
            'description': 'Clear skies and calm waters observed',
            'time': '2h ago',
            'priority': 'green'
        },
        {
            'title': 'Strong Winds',
            'reporter': 'Port Authority - Kandla',
            'description': 'Increased wind speeds affecting small vessel operations',
            'time': '3h ago',
            'priority': 'yellow'
        }
    ]
    return reports

# Main route - Landing page
@app.route('/')
def index():
    return render_template('index.html')

# Official dashboard route with real weather data
@app.route('/dashboard')
def dashboard():
    try:
        # Test API key first
        api_key = os.getenv('WEATHER_API_KEY')
        logger.info(f"Dashboard loading... API Key available: {'Yes' if api_key else 'No'}")
        
        # Fetch weather data for key cities
        weather_data = {}
        city_stats = {'total': len(GUJARAT_CITIES), 'safe': 0, 'monitor': 0, 'alert': 0}
        
        # Get weather for first 4 cities for main display
        main_cities = list(GUJARAT_CITIES.items())[:4]
        for city_name, coords in main_cities:
            weather_data[city_name] = fetch_weather_data(city_name, coords['lat'], coords['lon'])
            
            # Count threat levels
            level = weather_data[city_name]['threat_level']
            if level == 'green':
                city_stats['safe'] += 1
            elif level == 'yellow':
                city_stats['monitor'] += 1
            elif level == 'red':
                city_stats['alert'] += 1
        
        # Get all cities data for map
        all_cities_data = {}
        for city_name, coords in GUJARAT_CITIES.items():
            city_data = fetch_weather_data(city_name, coords['lat'], coords['lon'])
            city_data['icon'] = coords['icon']
            all_cities_data[city_name] = city_data
        
        # Generate mock data for other panels
        ai_alerts = generate_mock_alerts()
        community_reports = generate_mock_reports()
        
        # Calculate summary stats
        total_alerts = len(ai_alerts)
        critical_alerts = len([a for a in ai_alerts if a['level'] == 'red'])
        total_reports = len(community_reports)
        
        logger.info(f"Dashboard data loaded successfully. Weather data points: {len(weather_data)}")
        
        return render_template('dashboard.html', 
                             weather_data=weather_data,
                             all_cities_data=all_cities_data,
                             city_stats=city_stats,
                             ai_alerts=ai_alerts,
                             community_reports=community_reports,
                             summary_stats={
                                 'total_alerts': total_alerts,
                                 'critical_alerts': critical_alerts,
                                 'monitored_cities': len(GUJARAT_CITIES),
                                 'community_reports': total_reports
                             })
    
    except Exception as e:
        logger.error(f"Error in dashboard route: {e}")
        return render_template('dashboard.html', error=str(e))

# Community forum route (we'll expand this later)
@app.route('/community')
def community():
    return render_template('community.html')

# API Test route for debugging
@app.route('/api-test')
def api_test():
    """Test OpenWeatherMap API connectivity"""
    api_key = os.getenv('WEATHER_API_KEY')
    
    test_results = {
        'api_key_loaded': bool(api_key),
        'api_key_length': len(api_key) if api_key else 0,
        'api_key_preview': api_key[:8] + '...' if api_key else 'Not loaded',
        'test_status': 'Not tested',
        'test_details': {},
        'error': None
    }
    
    if api_key:
        try:
            # Test with Ahmedabad coordinates
            url = f"http://api.openweathermap.org/data/2.5/weather"
            params = {
                'lat': 23.0225,
                'lon': 72.5714,
                'appid': api_key.strip(),
                'units': 'metric'
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                test_results['test_status'] = 'SUCCESS'
                test_results['test_details'] = {
                    'city': data.get('name', 'Unknown'),
                    'temperature': data['main']['temp'],
                    'description': data['weather'][0]['description'],
                    'humidity': data['main']['humidity'],
                    'pressure': data['main']['pressure']
                }
            else:
                test_results['test_status'] = 'FAILED'
                test_results['error'] = f"HTTP {response.status_code}: {response.text}"
                
        except Exception as e:
            test_results['test_status'] = 'ERROR'
            test_results['error'] = str(e)
    else:
        test_results['test_status'] = 'NO_API_KEY'
        test_results['error'] = 'API key not found in environment variables'
    
    return jsonify(test_results)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
