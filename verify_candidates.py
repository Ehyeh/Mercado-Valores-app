import requests
import json

def verify_all_possibilities():
    url = "https://getmarketvalues-hdiyird7fq-uc.a.run.app"
    
    # Base names from BVC and search
    bases = [
        "ABC", "AIV", "BNC", "BPV", "BVCC", "BVL", "CCP", "CCR", "CGQ", "CRM",
        "DOM", "EFE", "ENV", "FNC", "FVI", "GMC", "GZL", "ICP", "IVC", "MPA",
        "MVZ", "PCP", "PGR", "PIV", "PTN", "RFM", "RST", "SVS", "TDV", "TPG",
        "VNA", "PER", "MOT", "MTC", "CANTV"
    ]
    suffixes = ["", "-A", "-B", "-D", ".A", ".B", ".D"]
    
    candidate_symbols = []
    for base in bases:
        for s in suffixes:
            candidate_symbols.append(f"{base}{s}.CR")
            
    # Add some specific ones found or mentioned
    candidate_symbols.extend([
        "PER.CR", "FVI-B.CR", "FVI-A.CR", "AIV-B.CR", "MTC-B.CR", "MOT-B.CR"
    ])
    
    # De-duplicate
    candidate_symbols = list(set(candidate_symbols))
    
    print(f"Testing {len(candidate_symbols)} candidate symbols...")
    
    # Process 1 by 1 to isolate valid ones
    valid_results = []
    
    for i, symbol in enumerate(candidate_symbols):
        if i % 10 == 0:
            print(f"Progress: {i}/{len(candidate_symbols)}...")
            
        yahoo_url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
        payload = {"urls": [yahoo_url]}
        headers = {"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"}
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if 'data' in data and data['data']:
                    result = data['data'][0]
                    try:
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
        except Exception:
            pass

    # Display results
    print("\n=== VALID SYMBOLS FOUND ===")
    # Sort by symbol
    valid_results.sort(key=lambda x: x['symbol'])
    for res in valid_results:
        print(f"{res['symbol']}: {res['name']} (Price: {res['price']})")
    
    print(f"\nTotal valid symbols: {len(valid_results)}")
    
    # Output list for copy-paste
    just_symbols = sorted([res['symbol'] for res in valid_results])
    print("\nPython list format:")
    print(json.dumps(just_symbols))

if __name__ == "__main__":
    verify_all_possibilities()
