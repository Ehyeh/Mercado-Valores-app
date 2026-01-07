import requests
import json

def verify_targeted():
    url = "https://getmarketvalues-hdiyird7fq-uc.a.run.app"
    
    # 31 already in the app
    current = [
        "ABC-A.CR", "BNC.CR", "BPV.CR", "BVCC.CR", "BVL.CR",
        "CCP-B.CR", "CCR.CR", "CGQ.CR", "CRM-A.CR", "DOM.CR",
        "EFE.CR", "ENV.CR", "GMC-B.CR", "GZL.CR", "ICP-B.CR",
        "IVC-A.CR", "IVC-B.CR", "MPA.CR", "MVZ-A.CR", "MVZ-B.CR",
        "PCP-B.CR", "PGR.CR", "PIV-B.CR", "PTN.CR", "RFM.CR",
        "RST.CR", "RST-B.CR", "SVS.CR", "TDV-D.CR", "TPG.CR",
        "VNA-B.CR"
    ]
    
    # New candidates from search and user
    candidates = [
        "PER.CR", "PER-A.CR", "PER-B.CR", "FVI-B.CR", "FVI-A.CR", 
        "AIV-B.CR", "AIV-A.CR", "FNC.CR", "FNC-A.CR", "MOT-B.CR", 
        "MTC-B.CR", "PIV.CR", "PIV-A.CR", "CANTV.CR", "CANTV-D.CR",
        "CRM.CR", "CRM-B.CR", "IVC.CR", "GMC.CR", "GMC-A.CR",
        "ICP.CR", "ICP-A.CR", "SPS.CR", "SPS-B.CR", "BCO-A.CR",
        "BCO-B.CR", "BCV.CR", "FIM.CR", "FIM-A.CR", "FIM-B.CR"
    ]
    
    all_to_test = list(set(current + candidates))
    
    print(f"Testing {len(all_to_test)} targeted symbols...")
    
    valid_results = []
    
    for symbol in all_to_test:
        yahoo_url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
        payload = {"urls": [yahoo_url]}
        headers = {"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"}
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if 'data' in data and data['data']:
                    result = data['data'][0]
                    if result.get('chart', {}).get('result'):
                        meta = result['chart']['result'][0]['meta']
                        if meta.get('regularMarketPrice') is not None:
                            sym = meta.get('symbol')
                            name = meta.get('shortName', meta.get('longName', sym))
                            price = meta.get('regularMarketPrice')
                            valid_results.append({
                                "symbol": sym,
                                "name": name,
                                "price": price
                            })
                            print(f"  [+] Found: {sym} ({name})")
        except:
            pass

    # Sort and display
    valid_results.sort(key=lambda x: x['symbol'])
    
    print("\n=== FINAL VALID SYMBOLS LIST ===")
    symbols_only = [res['symbol'] for res in valid_results]
    print(json.dumps(symbols_only, indent=2))
    print(f"\nTotal: {len(valid_results)}")

if __name__ == "__main__":
    verify_targeted()
