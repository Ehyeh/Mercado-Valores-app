import requests
from bs4 import BeautifulSoup

url = "https://www.bolsadecaracas.com/"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

response = requests.get(url, headers=headers, verify=False)
soup = BeautifulSoup(response.content, 'html.parser')

# Find the IBC value
# Based on chunk, it's near "Índices"
indices_section = soup.find(string="Índices")
if indices_section:
    print("Found 'Índices'")
    # Maybe the parent or previous element has the value?
    # Chunk showed "3.358,29" before "Índices"
    
    # Let's print some nearby text
    print(indices_section.find_parent().get_text())


# Find tables
tables = soup.find_all('table')
print(f"Found {len(tables)} tables")

for i, table in enumerate(tables):
    print(f"--- Table {i} ---")
    # Print headers
    headers = [th.get_text().strip() for th in table.find_all('th')]
    print(f"Headers: {headers}")
    # Print first row
    first_row = table.find('tr', recursive=True)
    if first_row:
         print(f"Row 1: {[td.get_text().strip() for td in first_row.find_all(['td', 'th'])]}")
    
    # Check if this table has stock data
    if "Precio" in str(table) or "Símbolo" in str(table) or "Symbol" in str(table):
        print("POTENTIAL STOCK TABLE")

