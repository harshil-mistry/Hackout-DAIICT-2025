from flask import Flask, render_template, request, jsonify, redirect, url_for
from dotenv import load_dotenv
import os
import requests
from datetime import datetime
import logging
import random
import json
import google.generativeai as genai
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from twilio.rest import Client

# Load environment variables
load_dotenv()

# Configure Google Gemini AI
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    print(f"Gemini API configured successfully")
else:
    print("Warning: GEMINI_API_KEY not found in environment variables")

# Debug environment loading
print("=== ENVIRONMENT DEBUG ===")
print(f"Current working directory: {os.getcwd()}")
print(f"Environment file exists: {os.path.exists('.env')}")
print(f"SECRET_KEY from env: {os.getenv('SECRET_KEY')}")
print(f"WEATHER_API_KEY from env: {os.getenv('WEATHER_API_KEY')}")
print(f"GEMINI_API_KEY from env: {'Set' if GEMINI_API_KEY else 'Not set'}")
print("=========================")

# Communication Services Configuration
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER')

# Email Configuration
SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
SMTP_USERNAME = os.getenv('SMTP_USERNAME')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')

# Initialize Twilio client
twilio_client = None
if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN:
    try:
        twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        print("✅ Twilio client initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize Twilio client: {e}")
else:
    print("⚠️ Twilio credentials not found in environment variables")

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

def get_wind_direction(degrees):
    """Convert wind direction degrees to text"""
    directions = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE',
                 'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW']
    index = round(degrees / 22.5) % 16
    return directions[index]

def calculate_uv_index(weather_data):
    """Estimate UV index based on weather conditions"""
    # Simplified UV calculation based on cloud cover and time
    cloud_cover = weather_data.get('clouds', {}).get('all', 0)
    if cloud_cover > 80:
        return random.randint(1, 3)
    elif cloud_cover > 50:
        return random.randint(3, 6)
    else:
        return random.randint(6, 9)

def get_air_quality_estimation(weather_data):
    """Estimate air quality based on weather conditions"""
    humidity = weather_data['main']['humidity']
    pressure = weather_data['main']['pressure']
    
    if pressure > 1020 and humidity < 60:
        return {'level': 'Good', 'aqi': random.randint(1, 50), 'color': 'green'}
    elif pressure > 1010 and humidity < 70:
        return {'level': 'Moderate', 'aqi': random.randint(51, 100), 'color': 'yellow'}
    else:
        return {'level': 'Unhealthy', 'aqi': random.randint(101, 150), 'color': 'orange'}

def estimate_sea_conditions(weather_data):
    """Estimate sea conditions for coastal areas"""
    wind_speed = weather_data['wind']['speed'] * 3.6  # km/h
    pressure = weather_data['main']['pressure']
    
    if wind_speed < 20 and pressure > 1015:
        return {'condition': 'Calm', 'wave_height': '0.5-1m', 'safety': 'Safe'}
    elif wind_speed < 35 and pressure > 1005:
        return {'condition': 'Moderate', 'wave_height': '1-2m', 'safety': 'Caution'}
    else:
        return {'condition': 'Rough', 'wave_height': '2-4m', 'safety': 'Warning'}

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
        print(f"🔧 DEBUG: Using STATIC DEMO weather data for {city_name} (API key not configured)")
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
        print(f"✅ DEBUG: Using REAL weather data for {city_name} from OpenWeatherMap API")
        
        # Calculate additional metrics
        wind_direction_text = get_wind_direction(data['wind'].get('deg', 0))
        uv_index = calculate_uv_index(data)
        air_quality = get_air_quality_estimation(data)
        sea_conditions = estimate_sea_conditions(data)
        
        return {
            'city': city_name,
            'temperature': round(data['main']['temp']),
            'feels_like': round(data['main']['feels_like']),
            'temp_min': round(data['main']['temp_min']),
            'temp_max': round(data['main']['temp_max']),
            'humidity': data['main']['humidity'],
            'pressure': data['main']['pressure'],
            'sea_level_pressure': data['main'].get('sea_level', data['main']['pressure']),
            'wind_speed': round(data['wind']['speed'] * 3.6),  # Convert m/s to km/h
            'wind_direction': data['wind'].get('deg', 0),
            'wind_direction_text': wind_direction_text,
            'wind_gust': round(data['wind'].get('gust', 0) * 3.6) if data['wind'].get('gust') else 0,
            'description': data['weather'][0]['description'].title(),
            'main_weather': data['weather'][0]['main'],
            'icon': data['weather'][0]['icon'],
            'visibility': data.get('visibility', 10000) / 1000,  # Convert to km
            'clouds': data['clouds']['all'],
            'sunrise': datetime.fromtimestamp(data['sys']['sunrise']).strftime('%H:%M'),
            'sunset': datetime.fromtimestamp(data['sys']['sunset']).strftime('%H:%M'),
            'country': data['sys']['country'],
            'timezone': data.get('timezone', 0),
            'last_updated': datetime.now().strftime('%H:%M'),
            'threat_level': calculate_threat_level(data),
            'uv_index': uv_index,
            'air_quality': air_quality,
            'sea_conditions': sea_conditions,
            'coordinates': {'lat': lat, 'lon': lon}
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
    print(f"🔧 DEBUG: Generating STATIC DEMO weather data for {city_name}")
    temp = random.randint(25, 35)
    return {
        'city': city_name,
        'temperature': temp,
        'feels_like': temp + random.randint(-2, 4),
        'temp_min': temp - random.randint(2, 5),
        'temp_max': temp + random.randint(2, 5),
        'humidity': random.randint(60, 85),
        'pressure': random.randint(1010, 1020),
        'sea_level_pressure': random.randint(1012, 1022),
        'wind_speed': random.randint(10, 25),
        'wind_direction': random.randint(0, 360),
        'wind_direction_text': get_wind_direction(random.randint(0, 360)),
        'wind_gust': random.randint(15, 35),
        'description': random.choice(['Clear Sky', 'Few Clouds', 'Partly Cloudy', 'Light Breeze']),
        'main_weather': random.choice(['Clear', 'Clouds', 'Mist']),
        'icon': '01d',
        'visibility': round(random.uniform(8, 15), 1),
        'clouds': random.randint(10, 40),
        'sunrise': '06:30',
        'sunset': '18:45',
        'country': 'IN',
        'timezone': 19800,
        'last_updated': datetime.now().strftime('%H:%M'),
        'threat_level': 'green',
        'uv_index': random.randint(3, 8),
        'air_quality': {'level': 'Good', 'aqi': random.randint(20, 80), 'color': 'green'},
        'sea_conditions': {'condition': 'Calm', 'wave_height': '0.5-1m', 'safety': 'Safe'},
        'coordinates': {'lat': 22.0, 'lon': 71.0}
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

# ======================================
# LLM INTEGRATION FOR COASTAL THREAT ANALYSIS
# ======================================

def analyze_coastal_threat():
    """
    Core function to analyze coastal threats using Google Gemini AI
    Fetches weather data for critical locations and analyzes threats
    """
    try:
        print(f"🧠 DEBUG: Starting AI coastal threat analysis...")
        
        # Define critical coastal locations for analysis
        critical_locations = [
            'Dwarka',  # Important religious and coastal city
            'Kandla',  # Major port
            'Mandvi',  # Coastal tourism area
            'Veraval'  # Major fishing port
        ]
        
        # Fetch weather data for critical locations
        weather_analysis_data = {}
        for location in critical_locations:
            if location in GUJARAT_CITIES:
                coords = GUJARAT_CITIES[location]
                weather_data = fetch_weather_data(location, coords['lat'], coords['lon'])
                weather_analysis_data[location] = weather_data
        
        # If no weather data available, use mock data
        if not weather_analysis_data:
            weather_analysis_data = {
                'Dwarka': get_mock_weather_data('Dwarka'),
                'Kandla': get_mock_weather_data('Kandla')
            }
        
        # Call Gemini AI for threat analysis
        ai_analysis = call_gemini_api(weather_analysis_data)
        
        return ai_analysis
        
    except Exception as e:
        logger.error(f"Error in coastal threat analysis: {e}")
        # Return fallback analysis
        return get_fallback_analysis()

def call_gemini_api(weather_data):
    """
    Call Google Gemini API for intelligent coastal threat analysis
    """
    try:
        if not GEMINI_API_KEY:
            logger.warning("Gemini API key not available, using fallback analysis")
            print(f"🔧 DEBUG: Using STATIC DEMO AI analysis (Gemini API key not configured)")
            return get_fallback_analysis()
        
        print(f"✅ DEBUG: Using REAL Gemini AI analysis (API key configured)")
        
        # Create detailed prompt for Gemini
        prompt = create_analysis_prompt(weather_data)
        
        # Initialize Gemini model
        model = genai.GenerativeModel('gemini-2.5-pro')
        
        # Generate analysis
        response = model.generate_content(prompt)
        
        # Parse the response
        analysis_result = parse_gemini_response(response.text)
        
        logger.info("Successfully generated AI coastal threat analysis")
        print(f"✅ DEBUG: Gemini AI analysis completed successfully")
        return analysis_result
        
    except Exception as e:
        logger.error(f"Error calling Gemini API: {e}")
        return get_fallback_analysis()

def create_analysis_prompt(weather_data):
    """
    Create a detailed prompt for Gemini AI coastal threat analysis
    """
    prompt = f"""
You are an expert coastal safety analyst for Gujarat, India. Analyze the following real-time weather data for critical coastal locations and provide a comprehensive threat assessment.

WEATHER DATA:
{json.dumps(weather_data, indent=2)}

ANALYSIS INSTRUCTIONS:
1. Evaluate coastal threats including: high winds, storm surge risk, extreme temperatures, poor visibility, rough seas
2. Consider the impact on: fishing operations, port activities, coastal tourism, local communities
3. Factor in seasonal patterns for Arabian Sea coastal regions
4. Assess threat levels: GREEN (safe), YELLOW (monitor), RED (dangerous)

REQUIRED JSON RESPONSE FORMAT:
{{
    "alert_level": "green|yellow|red",
    "overall_threat_score": 1-10,
    "primary_concerns": ["concern1", "concern2"],
    "reason": "Detailed explanation of current conditions and why this alert level",
    "recommended_action": "Specific actionable recommendations for authorities and public",
    "affected_areas": ["area1", "area2"],
    "risk_factors": {{
        "wind_risk": "low|medium|high",
        "wave_risk": "low|medium|high", 
        "visibility_risk": "low|medium|high",
        "temperature_risk": "low|medium|high"
    }},
    "forecast_trend": "improving|stable|deteriorating",
    "emergency_contacts": "relevant contact info if alert_level is red",
    "last_updated": "{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
}}

Respond with ONLY the JSON object, no additional text.
"""
    return prompt

def parse_gemini_response(response_text):
    """
    Parse and validate Gemini API response
    """
    try:
        # Clean the response text
        response_text = response_text.strip()
        
        # Remove markdown code blocks if present
        if response_text.startswith('```json'):
            response_text = response_text[7:]
        if response_text.startswith('```'):
            response_text = response_text[3:]
        if response_text.endswith('```'):
            response_text = response_text[:-3]
        
        # Parse JSON
        analysis = json.loads(response_text.strip())
        
        # Validate required fields
        required_fields = ['alert_level', 'reason', 'recommended_action']
        for field in required_fields:
            if field not in analysis:
                raise ValueError(f"Missing required field: {field}")
        
        # Ensure alert_level is valid
        if analysis['alert_level'] not in ['green', 'yellow', 'red']:
            analysis['alert_level'] = 'green'
        
        return analysis
        
    except Exception as e:
        logger.error(f"Error parsing Gemini response: {e}")
        return get_fallback_analysis()

def get_fallback_analysis():
    """
    Provide fallback analysis when AI is unavailable
    """
    print(f"🔧 DEBUG: Generating STATIC DEMO fallback analysis (AI unavailable)")
    return {
        "alert_level": "green",
        "overall_threat_score": 3,
        "primary_concerns": ["Normal coastal conditions"],
        "reason": "Current weather conditions are within normal parameters for Gujarat coastal regions. Wind speeds and sea conditions are manageable for routine coastal activities.",
        "recommended_action": "Continue normal coastal operations with standard safety precautions. Monitor weather updates regularly.",
        "affected_areas": ["Gujarat Coast"],
        "risk_factors": {
            "wind_risk": "low",
            "wave_risk": "low",
            "visibility_risk": "low",
            "temperature_risk": "low"
        },
        "forecast_trend": "stable",
        "emergency_contacts": "Contact local authorities if conditions change",
        "last_updated": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "data_source": "Fallback analysis - AI unavailable"
    }

# ======================================
# COMMUNICATION SERVICES
# ======================================

def send_email(to_email, subject, message):
    """Send email using SMTP"""
    try:
        if not SMTP_USERNAME or not SMTP_PASSWORD:
            return {"success": False, "error": "Email credentials not configured"}
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = SMTP_USERNAME
        msg['To'] = to_email
        msg['Subject'] = subject
        
        # Add body to email
        msg.attach(MIMEText(message, 'plain'))
        
        # Create SMTP session
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()  # Enable security
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        text = msg.as_string()
        server.sendmail(SMTP_USERNAME, to_email, text)
        server.quit()
        
        return {"success": True, "message": f"Email sent successfully to {to_email}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def send_sms(to_phone, message):
    """Send SMS using Twilio"""
    try:
        if not twilio_client:
            return {"success": False, "error": "Twilio client not initialized"}
        
        # Format phone number
        if not to_phone.startswith('+'):
            to_phone = '+91' + to_phone  # Default to India
        
        message = twilio_client.messages.create(
            body=message,
            from_=f'+{TWILIO_PHONE_NUMBER}',
            to=to_phone
        )
        return {"success": True, "message": f"SMS sent successfully to {to_phone}", "sid": message.sid}
    except Exception as e:
        return {"success": False, "error": str(e)}

# ======================================
# FLASK ROUTES
# ======================================

# Main route - Landing page
@app.route('/')
def index():
    return render_template('index.html')

# Official dashboard route with real weather data
@app.route('/api/debug-status')
def debug_status():
    """Debug endpoint to check API configuration status"""
    weather_api_key = os.getenv('WEATHER_API_KEY')
    gemini_api_key = os.getenv('GEMINI_API_KEY')
    
    status = {
        'weather_api_configured': bool(weather_api_key and weather_api_key != 'your-openweathermap-api-key'),
        'gemini_api_configured': bool(gemini_api_key and gemini_api_key != 'your_google_gemini_api_key_here'),
        'data_sources': {
            'weather': 'REAL API' if (weather_api_key and weather_api_key != 'your-openweathermap-api-key') else 'DEMO DATA',
            'ai_analysis': 'REAL AI' if (gemini_api_key and gemini_api_key != 'your_google_gemini_api_key_here') else 'DEMO DATA'
        }
    }
    
    print(f"🔍 DEBUG: API Status Check - Weather: {status['data_sources']['weather']}, AI: {status['data_sources']['ai_analysis']}")
    
    return jsonify(status)


@app.route('/api/ai-analysis')
def get_ai_analysis():
    """
    Asynchronous endpoint for fetching AI coastal threat analysis.
    This endpoint is called via AJAX after the main dashboard loads.
    """
    print(f"🌐 DEBUG: AI Analysis API endpoint called - Processing async request...")
    try:
        logger.info("API: Starting asynchronous AI coastal threat analysis...")
        
        # Perform the actual AI analysis
        ai_threat_analysis = analyze_coastal_threat()
        
        logger.info(f"API: AI Analysis completed - Alert Level: {ai_threat_analysis.get('alert_level', 'unknown')}")
        
        # Convert AI analysis to alert format for the dashboard
        ai_alert = {
            'title': f"AI Threat Assessment - {ai_threat_analysis.get('alert_level', 'unknown').upper()} Alert",
            'description': ai_threat_analysis.get('reason', 'Analysis unavailable'),
            'location': ', '.join(ai_threat_analysis.get('affected_areas', ['Gujarat Coast'])),
            'time': ai_threat_analysis.get('last_updated', 'Unknown'),
            'level': ai_threat_analysis.get('alert_level', 'green'),
            'icon': 'fa-brain',
            'priority': ai_threat_analysis.get('alert_level', 'green'),
            'recommended_action': ai_threat_analysis.get('recommended_action', 'Monitor conditions'),
            'threat_score': ai_threat_analysis.get('overall_threat_score', 3),
            'risk_factors': ai_threat_analysis.get('risk_factors', {}),
            'primary_concerns': ai_threat_analysis.get('primary_concerns', []),
            'forecast_trend': ai_threat_analysis.get('forecast_trend', 'stable'),
            'data_source': ai_threat_analysis.get('data_source', 'Gemini AI Analysis'),
            'is_placeholder': False
        }
        
        # Return both the alert and full analysis data
        response_data = {
            'success': True,
            'ai_alert': ai_alert,
            'ai_analysis': ai_threat_analysis,
            'timestamp': ai_threat_analysis.get('last_updated', 'Unknown')
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Error in AI analysis API: {e}")
        
        # Return error response with fallback data
        fallback_analysis = get_fallback_analysis()
        error_alert = {
            'title': "AI Threat Assessment - Service Unavailable",
            'description': f"AI analysis temporarily unavailable: {str(e)}",
            'location': 'Gujarat Coast',
            'time': 'Error occurred',
            'level': 'yellow',
            'icon': 'fa-exclamation-triangle',
            'priority': 'yellow',
            'recommended_action': 'Manual monitoring recommended',
            'threat_score': 3,
            'risk_factors': {},
            'primary_concerns': ['AI service unavailable'],
            'forecast_trend': 'unknown',
            'data_source': 'Fallback Analysis',
            'is_placeholder': False
        }
        
        return jsonify({
            'success': False,
            'error': str(e),
            'ai_alert': error_alert,
            'ai_analysis': fallback_analysis
        }), 500


@app.route('/dashboard')
def dashboard():
    print(f"🌐 DEBUG: Dashboard route accessed - Loading page with placeholder AI data...")
    try:
        # Test API key first
        api_key = os.getenv('WEATHER_API_KEY')
        logger.info(f"Dashboard loading... API Key available: {'Yes' if api_key else 'No'}")
        print(f"🔑 DEBUG: Weather API Key configured: {'Yes' if api_key and api_key != 'your-openweathermap-api-key' else 'No'}")
        
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
        
        # Initialize placeholder AI alerts for immediate loading
        ai_alerts = [
            {
                'title': "AI Threat Assessment - Loading...",
                'description': "Analyzing coastal threat data using Gemini AI...",
                'location': 'Gujarat Coast',
                'time': 'Loading...',
                'level': 'loading',
                'icon': 'fa-spinner fa-spin',
                'priority': 'loading',
                'recommended_action': 'Loading analysis...',
                'threat_score': 0,
                'risk_factors': {},
                'primary_concerns': [],
                'forecast_trend': 'analyzing',
                'data_source': 'Gemini AI Analysis (Loading)',
                'is_placeholder': True
            }
        ]
        
        # Placeholder AI analysis object
        ai_threat_analysis = {
            'alert_level': 'loading',
            'reason': 'AI analysis in progress...',
            'affected_areas': ['Gujarat Coast'],
            'last_updated': 'Loading...',
            'recommended_action': 'Please wait while we analyze the data',
            'overall_threat_score': 0,
            'risk_factors': {},
            'primary_concerns': ['Analysis in progress'],
            'forecast_trend': 'analyzing',
            'data_source': 'Gemini AI Analysis',
            'is_placeholder': True
        }
        
        # Add mock community reports
        community_reports = generate_mock_reports()
        
        # Calculate summary stats including AI analysis
        total_alerts = len(ai_alerts)
        critical_alerts = len([a for a in ai_alerts if a['level'] == 'red'])
        total_reports = len(community_reports)
        
        logger.info(f"Dashboard data loaded successfully. Weather data points: {len(weather_data)}, AI Analysis: {ai_threat_analysis.get('alert_level', 'unknown')}")
        
        print(f"📊 DEBUG: Dashboard template data summary:")
        print(f"   - Weather data cities: {list(weather_data.keys())}")
        print(f"   - All cities data: {len(all_cities_data)} cities")
        print(f"   - AI alerts: {len(ai_alerts)} alert(s) with placeholder data")
        print(f"   - Community reports: {len(community_reports)} mock reports")
        print(f"   - AI analysis status: {ai_threat_analysis.get('alert_level', 'unknown')}")
        
        return render_template('dashboard.html', 
                             weather_data=weather_data,
                             all_cities_data=all_cities_data,
                             city_stats=city_stats,
                             ai_alerts=ai_alerts,
                             community_reports=community_reports,
                             ai_analysis=ai_threat_analysis,  # Pass full AI analysis for additional display
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

# Get detailed city weather data
@app.route('/api/city/<city_name>')
def get_city_weather(city_name):
    """Get detailed weather data for a specific city"""
    if city_name not in GUJARAT_CITIES:
        return jsonify({'error': 'City not found'}), 404
    
    coords = GUJARAT_CITIES[city_name]
    weather_data = fetch_weather_data(city_name, coords['lat'], coords['lon'])
    weather_data['icon_class'] = coords['icon']
    
    return jsonify(weather_data)

# Communication Testing Route
@app.route('/test-communications')
def test_communications():
    """Test page for email, SMS, and WhatsApp functionality"""
    return render_template('test_communications.html')

@app.route('/api/test-communications', methods=['POST'])
def api_test_communications():
    """API endpoint to test email and SMS"""
    try:
        data = request.get_json()
        service_type = data.get('type')  # 'email' or 'sms'
        recipient = data.get('recipient')
        custom_message = data.get('message', '')
        
        if not service_type or not recipient:
            return jsonify({"success": False, "error": "Missing required fields: type and recipient"})
        
        # Only allow email and SMS
        if service_type not in ['email', 'sms']:
            return jsonify({"success": False, "error": "Invalid service type. Only 'email' and 'sms' are supported."})
        
        # Create test message
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        default_message = f"""🌊 CoastalGuard AI Test Alert 🌊

This is a test message from CoastalGuard AI coastal threat monitoring system.

Test Details:
- Service: {service_type.upper()}
- Time: {timestamp}
- Status: System operational

If you received this message, the {service_type} notification system is working correctly.

This is an automated test message. No action required.

---
CoastalGuard AI - Protecting Gujarat's Coast
"""
        
        message = custom_message if custom_message else default_message
        
        result = {"success": False, "error": "Unknown service type"}
        
        if service_type == 'email':
            subject = f"CoastalGuard AI Test Alert - {timestamp}"
            result = send_email(recipient, subject, message)
            
        elif service_type == 'sms':
            # Truncate message for SMS (160 character limit)
            sms_message = f"CoastalGuard AI Test: System operational at {timestamp}. SMS notifications working correctly."
            if custom_message:
                sms_message = custom_message[:160]
            result = send_sms(recipient, sms_message)
        
        # Add timestamp to result
        result['timestamp'] = timestamp
        result['service_type'] = service_type
        result['recipient'] = recipient
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
