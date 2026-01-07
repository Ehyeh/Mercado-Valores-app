import requests
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_interbono_api():
    url = "https://getmarketvalues-hdiyird7fq-uc.a.run.app"
    
    symbols = [
        "ABC-A.CR", "BNC.CR", "BPV.CR", "BVCC.CR", "BVL.CR",
        "CCP-B.CR", "CCR.CR", "CGQ.CR", "CRM-A.CR", "DOM.CR",
        "EFE.CR", "ENV.CR", "GMC-B.CR", "GZL.CR", "ICP-B.CR",
        "IVC-A.CR", "IVC-B.CR", "MPA.CR", "MVZ-A.CR", "MVZ-B.CR",
        "PCP-B.CR", "PGR.CR", "PIV-B.CR", "PTN.CR", "RFM.CR",
        "RST.CR", "RST-B.CR", "SVS.CR", "TDV-D.CR", "TPG.CR",
        "VNA-B.CR"
    ]
    
    # Construct the payload as seen in the JS code
    yahoo_urls = [f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}" for symbol in symbols]
    
    payload = {
        "urls": yahoo_urls
    }
    
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    try:
        logger.info(f"Sending POST request to {url}")
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        
        data = response.json()
        logger.info("Successfully received response")
        
        # Access the 'data' field as seen in the JS code: S.data.map(...)
        if 'data' in data:
            results = data['data']
            logger.info(f"Received data for {len(results)} symbols")
            
            for i, result in enumerate(results):
                # The JS code accesses result.chart.result[0].meta
                try:
                    meta = result['chart']['result'][0]['meta']
                    symbol = meta.get('symbol')
                    price = meta.get('regularMarketPrice')
                    print(f"Symbol: {symbol}, Price: {price}")
                except Exception as e:
                    print(f"Error parsing item {i} ({symbols[i]}): {e}")
        else:
            logger.error("Response JSON does not contain 'data' field")
            print(json.dumps(data, indent=2))
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed: {e}")
        if hasattr(e, 'response') and e.response is not None:
             logger.error(f"Response status: {e.response.status_code}")
             logger.error(f"Response content: {e.response.text}")

if __name__ == "__main__":
    test_interbono_api()
