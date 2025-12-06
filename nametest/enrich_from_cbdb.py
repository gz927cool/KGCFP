import csv
import json
import urllib.request
import urllib.parse
import time
import sys

def get_cbdb_data(name):
    base_url = "https://cbdb.fas.harvard.edu/cbdbapi/person.php"
    params = urllib.parse.urlencode({'name': name, 'o': 'json'})
    url = f"{base_url}?{params}"
    
    try:
        # Add a User-Agent just in case
        headers = {'User-Agent': 'Mozilla/5.0'}
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
            return data
    except Exception as e:
        print(f"Error querying {name}: {e}")
        return None

def process_painters():
    input_file = 'song_dynasty_painters_full.csv'
    output_file = 'song_dynasty_painters_enriched.csv'
    
    with open(input_file, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        if 'CBDB_ID' not in fieldnames:
            fieldnames.append('CBDB_ID')
        
        rows = list(reader)
    
    total = len(rows)
    print(f"Processing {total} painters...")
    
    updated_count = 0
    
    for i, row in enumerate(rows):
        name = row['Name']
        # Skip if name looks like a QID (starts with Q and followed by digits)
        if name.startswith('Q') and name[1:].isdigit():
            continue
            
        print(f"[{i+1}/{total}] Checking {name}...", end='', flush=True)
        
        # Only query if we are missing info or just want to add CBDB ID
        # But user said "supplement info", so we try to find everyone.
        
        data = get_cbdb_data(name)
        
        if data and 'Package' in data and 'PersonAuthority' in data['Package'] and 'PersonInfo' in data['Package']['PersonAuthority']:
            person_info = data['Package']['PersonAuthority']['PersonInfo']
            
            if 'Person' not in person_info:
                print(" No match.")
                continue
                
            persons = person_info['Person']
            if isinstance(persons, dict):
                persons = [persons]
            
            # Filter for Song Dynasty if possible
            # Dynasty names: 唐, 北宋, 南宋, 宋, etc.
            target_person = None
            
            # First pass: look for exact Song dynasty match
            for p in persons:
                basic = p.get('BasicInfo', {})
                dynasty = basic.get('DynastyBirth', '') + basic.get('DynastyDeath', '')
                if '宋' in dynasty:
                    target_person = p
                    break
            
            # If no Song match, but only one result, take it (risky but maybe okay for this context)
            if not target_person and len(persons) == 1:
                target_person = persons[0]
            
            if target_person:
                basic = target_person.get('BasicInfo', {})
                cbdb_id = basic.get('PersonId', '')
                row['CBDB_ID'] = cbdb_id
                
                # Update fields if missing in CSV
                if row['DOB'] == 'N/A' or not row['DOB']:
                    row['DOB'] = basic.get('YearBirth', 'N/A')
                
                if row['DOD'] == 'N/A' or not row['DOD']:
                    row['DOD'] = basic.get('YearDeath', 'N/A')
                
                if row['POB'] == 'N/A' or not row['POB']:
                    row['POB'] = basic.get('IndexAddr', 'N/A')
                
                # Gender mapping
                if row['Gender'] == 'N/A' or not row['Gender']:
                    g = basic.get('Gender', '')
                    if g == '0': row['Gender'] = '男'
                    elif g == '1': row['Gender'] = '女'
                
                print(f" Found! ID: {cbdb_id}")
                updated_count += 1
            else:
                print(" Multiple matches or no Song dynasty match.")
        else:
            print(" No data.")
            
        # Be nice to the API
        time.sleep(0.5)
        
        # Save periodically or just at the end? Let's save at the end to avoid file corruption on interrupt
        # But for large datasets, maybe every 50?
        if (i + 1) % 50 == 0:
            print("Saving progress...")
            with open(output_file, 'w', newline='', encoding='utf-8-sig') as f_out:
                writer = csv.DictWriter(f_out, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)

    # Final save
    with open(output_file, 'w', newline='', encoding='utf-8-sig') as f_out:
        writer = csv.DictWriter(f_out, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
        
    print(f"Done. Updated {updated_count} records. Saved to {output_file}")

if __name__ == "__main__":
    process_painters()
