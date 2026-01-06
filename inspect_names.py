import requests
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_interbono_api():
    url = "https://getmarketvalues-hdiyird7fq-uc.a.run.app"
    
    symbols = ["PGR.CR", "BNC.CR"] 
    
    yahoo_urls = [f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}" for symbol in symbols]
    
    payload = {
        "urls": yahoo_urls
    }
    
    headers = {
        "Content-Type": "application/json",
         "User-Agent": "Mozilla/5.0"
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        data = response.json()
        
        if 'data' in data:
            results = data['data']
            for i, result in enumerate(results):
                try:
                    meta = result['chart']['result'][0]['meta']
                    print(f"--- Meta keys for {symbols[i]} ---")
                    print(meta.keys())
                    # Check for common name fields
                    print(f"shortName: {meta.get('shortName')}")
                    print(f"longName: {meta.get('longName')}")
                    print(f"instrumentType: {meta.get('instrumentType')}")
                    print(f"exchangeName: {meta.get('exchangeName')}")
                except Exception as e:
                    print(e)

    except Exception as e:
        print(e)

if __name__ == "__main__":
    test_interbono_api()
