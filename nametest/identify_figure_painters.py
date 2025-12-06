import csv
import urllib.request
import urllib.parse
import json
import time
import math

def get_sparql_results(query):
    endpoint_url = "https://query.wikidata.org/sparql"
    headers = {
        'User-Agent': 'VSCodeCopilotBot/1.0',
        'Accept': 'application/json'
    }
    params = urllib.parse.urlencode({'query': query, 'format': 'json'})
    url = f"{endpoint_url}?{params}"
    
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode())
    except Exception as e:
        print(f"SPARQL Error: {e}")
        return None

def identify_figure_painters():
    input_file = 'song_dynasty_painters_enriched.csv'
    output_file = 'song_dynasty_figure_painters.csv'
    
    painters = []
    with open(input_file, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        painters = list(reader)
        
    print(f"Loaded {len(painters)} painters.")
    
    # Extract QIDs
    qids = []
    qid_to_index = {}
    for i, p in enumerate(painters):
        url = p.get('ID', '')
        if 'entity/Q' in url:
            qid = 'wd:' + url.split('/')[-1]
            qids.append(qid)
            qid_to_index[url.split('/')[-1]] = i
            
    print(f"Found {len(qids)} valid Wikidata IDs.")
    
    # Keywords for text analysis (Description field)
    keywords = ['人物', '仕女', '肖像', '写真', '道释', '鬼神', '佛像', '罗汉', 'figure', 'portrait', 'human', 'buddhist', 'taoist']
    
    # Initialize results structure
    # We will add 'Is_Figure_Painter', 'Evidence', 'Works' columns
    for p in painters:
        p['Is_Figure_Painter'] = 'No'
        p['Evidence'] = ''
        p['Works'] = ''

    # 1. Text Analysis (Initial pass with existing descriptions)
    print("Performing text analysis on descriptions...")
    for p in painters:
        desc = p.get('Description', '')
        if desc and desc != 'N/A':
            for kw in keywords:
                if kw in desc:
                    p['Is_Figure_Painter'] = 'Yes'
                    p['Evidence'] = f"Description contains '{kw}'"
                    break
    
    # 2. Wikidata Analysis (Batched)
    chunk_size = 50
    total_chunks = math.ceil(len(qids) / chunk_size)
    
    figure_painting_qids = [
        'wd:Q5448026', # figure painting
        'wd:Q134307',  # portrait
        'wd:Q200023',  # religious art
        'wd:Q1135756', # figure painting (general)
        'wd:Q93184',   # drawing (sometimes used)
        'wd:Q125191',  # photography (unlikely but check portrait)
        'wd:Q101687',  # nude
        'wd:Q212918'   # self-portrait
    ]
    
    # QIDs for "Human" to check 'depicts'
    human_qids = ['wd:Q5'] 
    
    print(f"Querying Wikidata in {total_chunks} chunks...")
    
    for i in range(0, len(qids), chunk_size):
        chunk = qids[i:i+chunk_size]
        values_clause = " ".join(chunk)
        
        print(f"Processing chunk {i//chunk_size + 1}/{total_chunks}...")
        
        # Query for:
        # 1. Painter field of work (P101) or genre (P136) matches figure painting
        # 2. Works (P170) that have genre (P136) or depict (P180) relevant things
        # 3. Also fetch English description if available to augment text analysis
        
        query = f"""
        SELECT ?painter ?painterLabel ?painterDesc ?work ?workLabel ?workGenre ?workGenreLabel ?depicts ?depictsLabel ?painterGenre ?painterGenreLabel WHERE {{
          VALUES ?painter {{ {values_clause} }}
          
          OPTIONAL {{ ?painter schema:description ?painterDesc . FILTER(LANG(?painterDesc) = "en") }}
          
          OPTIONAL {{ 
            ?painter wdt:P101 ?painterGenre . 
            FILTER(?painterGenre IN (wd:Q5448026, wd:Q134307, wd:Q200023))
          }}
          OPTIONAL {{ 
            ?painter wdt:P136 ?painterGenre . 
            FILTER(?painterGenre IN (wd:Q5448026, wd:Q134307, wd:Q200023))
          }}
          
          OPTIONAL {{
            ?work wdt:P170 ?painter .
            OPTIONAL {{ ?work wdt:P136 ?workGenre . }}
            OPTIONAL {{ ?work wdt:P180 ?depicts . }}
          }}
          
          SERVICE wikibase:label {{ bd:serviceParam wikibase:language "zh,en". }}
        }}
        """
        
        results = get_sparql_results(query)
        
        if results:
            bindings = results['results']['bindings']
            for item in bindings:
                painter_url = item['painter']['value']
                painter_qid = painter_url.split('/')[-1]
                
                if painter_qid not in qid_to_index:
                    continue
                    
                idx = qid_to_index[painter_qid]
                p = painters[idx]
                
                # Check English Description
                if 'painterDesc' in item:
                    desc = item['painterDesc']['value']
                    # Only use if we haven't found evidence yet or want to add more
                    for kw in keywords:
                        if kw in desc.lower():
                            p['Is_Figure_Painter'] = 'Yes'
                            evidence = f"Wikidata Desc: {desc}"
                            if evidence not in p['Evidence']:
                                p['Evidence'] = (p['Evidence'] + "; " + evidence).strip("; ")
                
                # Check Painter Genre
                if 'painterGenre' in item:
                    p['Is_Figure_Painter'] = 'Yes'
                    evidence = f"Known for {item.get('painterGenreLabel', {}).get('value', 'figure painting')}"
                    if evidence not in p['Evidence']:
                        p['Evidence'] = (p['Evidence'] + "; " + evidence).strip("; ")
                
                # Check Works
                if 'work' in item:
                    work_label = item.get('workLabel', {}).get('value', 'Unknown Work')
                    work_genre_id = item.get('workGenre', {}).get('value', '').split('/')[-1]
                    depicts_id = item.get('depicts', {}).get('value', '').split('/')[-1]
                    
                    is_figure_work = False
                    reason = ""
                    
                    if work_genre_id in ['Q5448026', 'Q134307', 'Q200023']:
                        is_figure_work = True
                        reason = "Genre: Figure/Portrait/Religious"
                    elif depicts_id == 'Q5':
                        is_figure_work = True
                        reason = "Depicts: Human"
                    # Check labels for keywords
                    elif any(k in work_label for k in ['图', '像', 'Portrait', 'Figure', 'Arhat', 'Luohan', 'Lady', 'Scholar', 'Immortal', 'God', 'Buddha']):
                         # Refined keywords
                         if any(x in work_label for x in ['像', 'Portrait', 'Arhat', 'Luohan', 'Lady', 'Immortal', 'Buddha', '仕女', '罗汉', '仙人', '高士']):
                             is_figure_work = True
                             reason = "Title implies figure"

                    if is_figure_work:
                        p['Is_Figure_Painter'] = 'Yes'
                        work_entry = f"{work_label} ({reason})"
                        if work_entry not in p['Works']:
                            p['Works'] = (p['Works'] + "; " + work_entry).strip("; ")
                            
        time.sleep(1) # Be nice to API

    # Filter and Save
    figure_painters = [p for p in painters if p['Is_Figure_Painter'] == 'Yes']
    
    print(f"Identified {len(figure_painters)} figure painters.")
    
    fieldnames = list(painters[0].keys())
    
    with open(output_file, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(figure_painters)
        
    print(f"Saved to {output_file}")

if __name__ == "__main__":
    identify_figure_painters()
