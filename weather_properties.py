
# Path to the Gadget's cache directory
MSN_WEATHER_DIRECTORY = 'C:\\Users\\Paul\\AppData\\Local\\Microsoft\\Windows Sidebar\\Cache\\168522d5-1082-4df2-b2f6-9185c31f9472\\'
# The weather file may vary depending on your location
WEATHER_LOCATION_CODE = 'CAXX0343'
MSN_WEATHER_FILE = '_wc-' + WEATHER_LOCATION_CODE + 'Fen-US_.xml'
MSN_WEATHER_CACHE_FILE = 'GlobalCacheCleanup.xml'

# Enter your WeatherBit.io API key
API_KEY = ''
# The forecast is based on coordinates
LATITUDE = 45.1234
LONGITUDE = -75.5678

# Enter any proxy URLs and credentials here
proxies = {
    #'http': 'http://user:password@http-proxy:8080',
    #'https': 'http://user:password@http-proxy:8080'
}

# Whether or not to verify certificates, 
# or a certificate against which to verfiy
verify = 'proxy.cer'