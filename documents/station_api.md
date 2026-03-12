GUIDE TO INTEGRATING THE ENVIRONMENTAL MONITORING API

1. General Information
The API system provides automated environmental monitoring data from monitoring stations. Partners use the assigned API Key to authenticate and retrieve data.

• Base URL: https://admin-qttd.tedp.vn/api/partner/v1

• Protocol: HTTPS

• Data Format: JSON

• Encoding: UTF-8

2. Authentication
All requests to the API must include the API Key in the Header to authenticate access.

• Header Name: X-API-KEY

• Access Token: c9e03048-46e1-40b0-9b6b-f12accef9f5a

3. API Reference List

3.1. Get Automation Stations
This API returns a list of automation stations along with detailed information about their location and address.

▪ Endpoint: /get-automation-stations

▪ Method: GET

▪ Description: Retrieves a list of active automation stations.

Parameters (Query Parameters):

ParameterName      DataType      Required      Default        Description
page               Integer        None          0             Current page number (starting from 0)
size               Integer        None          20            Number of records per page
apiType            Integer        Yes           1             API Type (Usually 1 for standard data)

Example Request (cURL): curl -X 'GET' \
'https://admin-qttd.tedp.vn/api/partner/v1/get-automation-stations?page=0&size=100&apiType=1' \
-H 'accept: application/json' \
-H 'X-API-KEY: c9e03048-46e1-40b0-9b6b-f12accef9f5a’
{
"content": [
{
"stationCode": "LSOS_KHIKHO", // Station Code (Used to map measurement data) "stationName": "Khanh Hoa: Vinh Hoa Ward - Nha Trang (KK)", // Station Name "address": "SOS Children's Village Nha Trang Campus...", // Address "latitude": 12.284358, // Latitude
"longitude": 109.192524, // Longitude "stationType": 4, // Station Type (4: Air) "provinceId": "2844..." // Province/City ID
}
// ... other stations
],
"pageable": { ... }, // Paging Information "totalElements": 26, // Total number of stations found "totalPages": 1 // Total number of pages
}


3.2. Get Hourly AQI Data
The API returns measurement data (AQI, dust concentration, emissions, etc.) from stations within a specified time period.

▪ Endpoint: /aqi_hours

▪ Method: GET

▪ Description: Retrieves detailed air quality monitoring data hour by hour.

Parameters (Query Parameters):

Parameter_Name       Data_Type    Required            Format/Example               Description
page                 Integer         No                   0                        Number of pages (starting from 0)
size                 Integer         No                   100                      Number of records/page
apiType              Integer         Yes                  1                        API Type
from                 DateTime        Yes            YYYY-MM-DDTHH:mm:ss            Start time for data retrieval (Example: 2025-09-10T18:00:00)
to                   DateTime        Yes            YYYY-MM-DDTHH:mm:ss            End time for data retrieval (Example: 2025-09-10T19:00:00)
Important Note:
▪ Time in the URL needs to be URL Encoded (Example: : to %3A). ▪ The space between `from` and `to` should not be too large to avoid overloading the returned data.

Example Request (cURL): curl -X 'GET' \ 'https://admin-
qttd.tedp.vn/api/partner/v1/aqi_hours?page=0&size=100&apiType=1&from=2025-09- 10T18%3A00%3A00&to=2025-09-10T18%3A00%3A00' \
-H 'accept: application/json' \
-H 'X-API-KEY: c9e03048-46e1-40b0-9b6b-f12accef9f5a’
Success Response Structure (200 OK): Data returned in Map format (Key-Value), where Key

is the stationCode of the station.
{
"content": [
{
"HCM_THDI_KHIKXQ": [ // Data of station with code HCM_THDI_KHIKXQ
{
"id": "6931318bb93db...",
"getTime": "2025-12-04T00:00:00", // Measurement time "stationId": "324818...",
"data": {
"aqi": 50.5, // AQI index "PM2.5": 50.5, // PM2.5 fine dust "PM10": 45.08, // PM10 dust
"CO": 16.22, // CO concentration "SO2": 0.68, // SO2 concentration "NO2": 5.63, // NO2 concentration "O3": 12.24, // O3 concentration
"Temp": null, // Temperature "RH": null // Humidity (null if not present)
}
}
// ... other time records
],
"LSOS_KHIKHO": [ ... ] // Data from another station
}
],
"pageable": { ... }
}

SAMPLE CODE PYTHON CALL HOUR AQI DATA:


import requests import json
from datetime import datetime
base_url = "https://admin-qttd.tedp.vn/api/partner/v1/aqi_hours" headers = {
"accept": "application/json",
"X-API-KEY": "c9e03048-46e1-40b0-9b6b-f12accef9f5a" # Replace API KEY if necessary
}
now = datetime.now()
current_time_str = now.strftime("%Y-%m-%dT%H:%M:%S") # 3. Parameter configuration
params = { "page": 0,
"size": 100,
"apiType": 1,
"from": "2025-11-01T08:30:00", # Start time (keep as is or modify as desired) "to": current_time_str # End time = Current
}
# 4. Call API
print("Calling API...")
response = requests.get(base_url, headers=headers, params=params, timeout=30) if response.status_code == 200:
data = response.json()
print("--- RETURNED RESULT ---")
print(json.dumps(data, indent=2, ensure_ascii=False))
else:


SAMPLE PYTHON CODE TO CALL AUTOMATIC MONITORING STATION LIST DATA:
import requests import json

# 1. Configure Endpoint
url = "https://admin-qttd.tedp.vn/api/partner/v1/get-automation-stations"

# 2. Configure Headers (Removed extraneous characters) headers = {
"accept": "application/json",

"X-API-KEY": "c9e03048-46e1-40b0-9b6b-f12accef9f5a"

}
# 3. Configure Parameters params = {
"page": 0,

"size": 1000,

"apiType": 1

}
# 4. Call API and print try results:
response = requests.get(url, headers=headers, params=params)