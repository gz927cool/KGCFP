import urllib.request
import urllib.parse
import json
import csv

def query_wikidata():
    endpoint_url = "https://query.wikidata.org/sparql"
    # Updated query to fetch more comprehensive information
    query = """
    SELECT DISTINCT ?painter ?painterLabel ?genderLabel ?dob ?pobLabel ?dod ?podLabel ?description ?image WHERE {
      ?painter wdt:P31 wd:Q5;                # Instance of human
               wdt:P106 wd:Q1028181;         # Occupation: painter
               wdt:P27 wd:Q7462.             # Country of citizenship: Song Dynasty
      
      OPTIONAL { ?painter wdt:P21 ?gender. } # Gender
      OPTIONAL { ?painter wdt:P569 ?dob. }   # Date of birth
      OPTIONAL { ?painter wdt:P19 ?pob. }    # Place of birth
      OPTIONAL { ?painter wdt:P570 ?dod. }   # Date of death
      OPTIONAL { ?painter wdt:P20 ?pod. }    # Place of death
      OPTIONAL { ?painter wdt:P18 ?image. }  # Image
      OPTIONAL { ?painter schema:description ?description. FILTER(LANG(?description) = "zh") }
      
      SERVICE wikibase:label { bd:serviceParam wikibase:language "zh,en". }
    }
    ORDER BY ?dob
    """

    # Set the User-Agent header as required by Wikidata User-Agent policy
    headers = {
        'User-Agent': 'VSCodeCopilotBot/1.0 (https://github.com/copilot)',
        'Accept': 'application/json'
    }

    params = urllib.parse.urlencode({'query': query, 'format': 'json'})
    url = f"{endpoint_url}?{params}"

    try:
        print("正在查询 Wikidata，请稍候...")
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            
        bindings = data['results']['bindings']
        print(f"获取到 {len(bindings)} 条记录。正在处理...")
        
        # Dictionary to deduplicate by painter ID (keep first occurrence)
        painters = {}
        
        for item in bindings:
            painter_id = item.get('painter', {}).get('value', 'N/A')
            
            if painter_id not in painters:
                painter_data = {
                    'ID': painter_id,
                    'Name': item.get('painterLabel', {}).get('value', 'N/A'),
                    'Gender': item.get('genderLabel', {}).get('value', 'N/A'),
                    'DOB': item.get('dob', {}).get('value', 'N/A'),
                    'POB': item.get('pobLabel', {}).get('value', 'N/A'),
                    'DOD': item.get('dod', {}).get('value', 'N/A'),
                    'POD': item.get('podLabel', {}).get('value', 'N/A'),
                    'Description': item.get('description', {}).get('value', 'N/A'),
                    'Image': item.get('image', {}).get('value', 'N/A')
                }
                
                # Format dates to be shorter
                for date_field in ['DOB', 'DOD']:
                    if 'T' in painter_data[date_field]:
                        painter_data[date_field] = painter_data[date_field].split('T')[0]
                
                painters[painter_id] = painter_data

        csv_data = list(painters.values())
        
        # Save to CSV
        csv_filename = 'song_dynasty_painters_full.csv'
        fieldnames = ['Name', 'Gender', 'DOB', 'POB', 'DOD', 'POD', 'Description', 'Image', 'ID']
        
        with open(csv_filename, 'w', newline='', encoding='utf-8-sig') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(csv_data)
            
        print(f"完整数据已保存至: {csv_filename}")
        print(f"共处理 {len(csv_data)} 位画家。")
        
        # Print a preview
        print("\n预览前 5 条数据:")
        print(f"{'姓名':<10} | {'性别':<4} | {'出生日期':<12} | {'出生地':<10} | {'描述'}")
        print("-" * 80)
        for p in csv_data[:5]:
            desc = p['Description']
            if len(desc) > 30: desc = desc[:27] + "..."
            print(f"{p['Name']:<10} | {p['Gender']:<4} | {p['DOB']:<12} | {p['POB']:<10} | {desc}")
            
    except Exception as e:
        print(f"Error querying Wikidata: {e}")

if __name__ == "__main__":
    query_wikidata()
