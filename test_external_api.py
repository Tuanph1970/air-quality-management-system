#!/usr/bin/env python3
"""Test script to verify external station API connectivity."""
import requests
import json

# 1. Cấu hình Endpoint
url = "https://admin-qttd.tedp.vn/api/partner/v1/get-automation-stations"

# 2. Cấu hình Headers
headers = {
    "accept": "application/json",
    "X-API-KEY": "c9e03048-46e1-40b0-9b6b-f12accef9f5a"
}

# 3. Cấu hình Tham số
params = {
    "page": 0,
    "size": 1000,
    "apiType": 1
}

# 4. Gọi API và in kết quả
try:
    print("=" * 60)
    print("Testing External Station API")
    print("=" * 60)
    print(f"URL: {url}")
    print(f"Headers: {headers}")
    print(f"Params: {params}")
    print("-" * 60)
    
    response = requests.get(url, headers=headers, params=params, timeout=30)
    
    print(f"HTTP Status Code: {response.status_code}")
    print(f"Response Headers: {dict(response.headers)}")
    print("-" * 60)
    
    if response.status_code == 200:
        data = response.json()
        print("✅ SUCCESS! API is working!")
        print(f"Response type: {type(data)}")
        
        if isinstance(data, dict):
            print(f"Keys in response: {list(data.keys())}")
            content = data.get('content', [])
            print(f"Number of stations: {len(content)}")
            total_elements = data.get('totalElements', 'N/A')
            print(f"Total elements: {total_elements}")
            
            if content:
                print("\nFirst station sample:")
                print(json.dumps(content[0], indent=2))
        else:
            print(f"Response content (first 500 chars): {str(data)[:500]}")
            
    elif response.status_code == 500:
        print("❌ FAILED! API returned 500 Internal Server Error")
        print(f"Response body: {response.text[:500]}")
    else:
        print(f"❌ FAILED! API returned {response.status_code}")
        print(f"Response body: {response.text[:500]}")
        
except requests.exceptions.Timeout:
    print("❌ FAILED! Request timed out after 30 seconds")
except requests.exceptions.ConnectionError as e:
    print(f"❌ FAILED! Connection error: {e}")
except requests.exceptions.RequestException as e:
    print(f"❌ FAILED! Request exception: {e}")
except json.JSONDecodeError as e:
    print(f"❌ FAILED! Could not parse JSON response: {e}")
    print(f"Raw response: {response.text[:500]}")
except Exception as e:
    print(f"❌ FAILED! Unexpected error: {e}")

print("=" * 60)
