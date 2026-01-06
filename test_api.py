import requests
import json
url = "https://us-central1-interbono-website.cloudfunctions.net/getStockData"
data = {"urls": ["BNC.CR", "MVZ-A.CR", "BNC"]} # Trying variants
headers = {
    "Origin": "https://interbono.com",
    "Referer": "https://interbono.com/",
    "User-Agent": "Mozilla/5.0"
}
try:
    r = requests.post(url, json=data, headers=headers)
    print(f"Status: {r.status_code}")
    print(r.text)
except Exception as e:
    print(e)
