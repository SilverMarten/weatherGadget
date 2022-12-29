#!/usr/bin/env python

""" Collect weather data from weatherbit.io and save it to the MSN weather gadget file. """

import json, requests, pytz
import xml.etree.ElementTree as ET
from xml.sax.saxutils import escape
from datetime import datetime
from datetime import timedelta
from requests.auth import HTTPProxyAuth

# Read the settings json file
with open('settings.json') as f:
    settings = json.load(f)
    
# Path to the Gadget's cache directory
MSN_WEATHER_DIRECTORY = settings['MSN_WEATHER_DIRECTORY']
# The weather file may vary depending on your location
WEATHER_LOCATION_CODE = settings['WEATHER_LOCATION_CODE']
MSN_WEATHER_FILE = settings['MSN_WEATHER_FILE']
MSN_WEATHER_CACHE_FILE = settings['MSN_WEATHER_CACHE_FILE']

# Enter your WeatherBit.io API key
API_KEY = settings['API_KEY']
# The forecast is based on coordinates
LATITUDE = settings['LATITUDE']
LONGITUDE = settings['LONGITUDE']

# Enter any proxy URLs and credentials here
proxies = settings['proxies']

# Whether or not to verify certificates, 
# or a certificate against which to verfiy
verify = settings['verify']

WEATHER_API_URL = 'https://api.weatherbit.io/v2.0/'
CURRENT_WEATHER = 'current'
DAILY_FORECAST = 'forecast/daily'

params = { 
    'key': API_KEY, 
    'lat': LATITUDE,
    'lon': LONGITUDE,
    'units': 'I',
    'include': 'alerts'
}

# The gadget assumes that the data is in Imperial units
wind_unit = 'mph'
wind_conversion = 1
temp_unit = 'F'

# Map WeatherBit.io codes to MSN gadget codes
weathercode_to_skycode = {
    # thunderstorm
    200: 1, 201: 1, 202: 1, 230: 1, 231: 1, 232: 1, 233: 1,
    # few-showers
    300: 35, 301: 35, 520: 35,
    # rainy
    302: 9, 500: 9, 501: 9, 502: 9, 521: 9, 522: 9, 610: 9, 900: 9,
    # hail
    511: 6, 611: 6, 612: 6,
    # snow
    600: 5, 601: 5, 602: 5, 621: 5, 622: 5, 623: 5,
    # foggy
    700: 19, 711: 19, 721: 19, 731: 19, 741: 19, 751: 19,
    # sun
    800: 32,
    # partly-cloudy
    801: 29, 802: 29, 803: 29,
    # cloudy
    804: 26
}

def datetime_to_mstimestamp(dt):
    """
    Active Directory has different approach to create timestamp than Unix.
    Here's a function to convert the Unix timestamp to the AD one.

    > dt = datetime(2000, 1, 1, 0, 0)
    > datetime_to_mstimestamp(dt)
    125911548000000000
    """
    timestamp = int(dt.timestamp())
    magic_number = 116_444_736_000_000_000
    shift = 10_000_000
    return (timestamp*shift) + magic_number

def celsius_to_fahrenheit(celsius):
    return (celsius * 9/5) + 32

def fahrenheit_to_celsius(fahrenheit):
    return (fahrenheit - 32) * 5/9

# Get the current weather
currentWeatherResponse = requests.get(WEATHER_API_URL + CURRENT_WEATHER,
                                      params=params, proxies=proxies, verify=verify)
currentWeather = currentWeatherResponse.json()['data'][0]
alerts = currentWeatherResponse.json()['alerts']
alertTitle = alerts[0]['title'] if len(alerts) > 0 else ''

# print('Currently in %s it is %dC with %s' % (currentWeather['city_name'], fahrenheit_to_celsius(currentWeather['temp']), currentWeather['weather']['description']), flush=True)

# Get the forecast
forecastResponse = requests.get(WEATHER_API_URL + DAILY_FORECAST,
                                params=params, proxies=proxies, verify=verify)
dailyforecast = forecastResponse.json()['data']

# print('Tomorrow it will be a high of %dC with %s' % (fahrenheit_to_celsius(dailyforecast[1]['max_temp']), dailyforecast[1]['weather']['description']), flush=True)

# Create the XML
CacheFile = ET.Element('CacheFile')
Version = ET.SubElement(CacheFile, 'Version')
Version.text = '1.0'
SavedTime = ET.SubElement(CacheFile, 'SavedTime')
SavedTime.text = str(datetime_to_mstimestamp(datetime.now()))
ExpiryTime = ET.SubElement(CacheFile, 'ExpiryTime')
ExpiryTime.text = str(datetime_to_mstimestamp(datetime.now() + timedelta(days=5)))

Data = ET.SubElement(CacheFile, 'Data')

# ET.indent(CacheFile)
# ET.dump(CacheFile)

xmlns = {
    'xmlns:xsd': 'http://www.w3.org/2001/XMLSchema',
    'xmlns:xsi': 'http://www.w3.org/2001/XMLSchema-instance'
}
weatherdata = ET.Element('weatherdata', xmlns)

timezoneoffset = datetime.now(pytz.timezone(currentWeather['timezone'])).utcoffset().total_seconds()/60/60

# Setup the weather element
weatherAttribs = {
    'weatherlocationcode': 'wc:' +WEATHER_LOCATION_CODE,
    'weatherlocationname': currentWeather['city_name'],
    'url': 'http://a.msn.com/54/en-US/ct%f,%f?ctsrc=Windows7' % (currentWeather['lat'], currentWeather['lon']),
    'imagerelativeurl': 'http://blob.weather.microsoft.com/static/weather4/en-us/',
    'degreetype': temp_unit,
    'provider': 'WeatherBit',
    'attribution': 'https://www.weatherbit.io/',
    'attribution2': currentWeather['sources'][0],
    'lat': str(currentWeather['lat']), 'long': str(currentWeather['lon']),
    'timezone': '%d' % timezoneoffset,
    'alert': alertTitle,
    'entityid': '24773',
    'encodedlocationname': currentWeather['city_name']
}
weather = ET.SubElement(weatherdata, 'weather', weatherAttribs)

# Create the current weather data
observation_time = datetime.strptime(currentWeather['ob_time'], '%Y-%m-%d %H:%M') + timedelta(hours=timezoneoffset)
currentAttribs = {
    'temperature': str(currentWeather['temp']),
    'skycode': str(weathercode_to_skycode[currentWeather['weather']['code']]),
    'skytext': currentWeather['weather']['description'],
    'date': observation_time.strftime('%Y-%m-%d'),
    'observationtime': observation_time.strftime('%H:%M:%S'),
    'observationpoint': currentWeather['city_name'],
    'feelslike': str(currentWeather['app_temp']),
    'humidity': str(currentWeather['rh']),
    'winddisplay': '%d %s %s' % (currentWeather['wind_spd']*wind_conversion, wind_unit, currentWeather['wind_cdir_full']),
    'day': observation_time.strftime('%A'),
    'shortday': observation_time.strftime('%a'),
    'windspeed': '%d %s' % (currentWeather['wind_spd']*wind_conversion, wind_unit)
}
current = ET.SubElement(weather, 'current', currentAttribs)

# Add the forecast for the next 5 days
for i in range(5):
    forecastDate = datetime.strptime(dailyforecast[i]['valid_date'], '%Y-%m-%d')
    forecastAttribs = {
        'low': str(dailyforecast[i]['min_temp']),
        'high': str(dailyforecast[i]['max_temp']),
        'skycodeday': str(weathercode_to_skycode[dailyforecast[i]['weather']['code']]),
        'skytextday': dailyforecast[i]['weather']['description'],
        'date': forecastDate.strftime('%Y-%m-%d'),
        'day': forecastDate.strftime('%A'),
        'shortday': forecastDate.strftime('%a'),
        'precip': str(dailyforecast[i]['pop'])
    }
    forecast = ET.Element('forecast', forecastAttribs)
    weather.append(forecast)

# ET.indent(weatherdata)
# ET.dump(weatherdata)

# Add toolbar element
ET.SubElement(weather, 'toolbar', {'timewindow': '60', 'minversion': '1.0.1965.0'})

# Set the text content of Data to the string version of weatherdata
Data.text = ET.tostring(weatherdata).decode()

# ET.indent(CacheFile)
# ET.dump(CacheFile)

# Update the cache cleanup time
CacheCleanup = ET.Element('CacheCleanup')
Timestamp = ET.SubElement(CacheCleanup, 'Timestamp')
Timestamp.text = str(datetime_to_mstimestamp(datetime.now() - timedelta(hours=2.5)))
# ET.dump(CacheCleanup)

# Save the XML
ET.ElementTree(CacheFile).write(MSN_WEATHER_DIRECTORY + MSN_WEATHER_FILE)
ET.ElementTree(CacheCleanup).write(MSN_WEATHER_DIRECTORY + MSN_WEATHER_CACHE_FILE)
