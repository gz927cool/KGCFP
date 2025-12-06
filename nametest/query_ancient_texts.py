import csv
import urllib.request
import urllib.parse
import re
import time
import sys

def get_html(url):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as response:
            return response.read().decode('utf-8')
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

def extract_works_from_wikisource(text, painter_name):
    # Normalize text
    # Wikisource HTML has tags, we need to be careful.
    # But get_html returns raw HTML.
    
    # Remove tags but keep some structure? No, just text is fine.
    clean_text = re.sub(r'<[^>]+>', '', text)
    clean_text = re.sub(r'\s+', '', clean_text)
    
    # Search for name
    # Try Traditional and Simplified
    # We need a way to convert, or just search for the name as provided (usually Simplified in CSV)
    # But Wikisource is Traditional.
    # I don't have a converter handy.
    # I will try to search for the name as is, and if not found, maybe try to guess Traditional?
    # Or just rely on the fact that many names are the same.
    # "李公麟" -> "李公麟" (Same)
    # "马远" -> "馬遠" (Different)
    
    # Simple mapping for common chars in names
    # This is hacky.
    # Better: Search for the name in the CSV, if not found, skip.
    # But I can try to map some common ones.
    
    # Let's just try with the name we have.
    
    name_indices = [m.start() for m in re.finditer(re.escape(painter_name), clean_text)]
    
    if not name_indices:
        # Try to convert common simplified to traditional for the name
        # This is a very limited map
        map_s2t = {'马': '馬', '远': '遠', '赵': '趙', '刘': '劉', '松': '松', '年': '年', '梁': '梁', '楷': '楷', '钱': '錢', '选': '選', '释': '釋', '画': '畫'}
        trad_name = "".join([map_s2t.get(c, c) for c in painter_name])
        if trad_name != painter_name:
            name_indices = [m.start() for m in re.finditer(re.escape(trad_name), clean_text)]
            
    for name_idx in name_indices:
        # Look for "御府所藏"
        window = clean_text[name_idx:name_idx+10000]
        
        # Markers: "今御府所藏", "御府所藏"
        marker_match = re.search(r'(今?御府所藏)', window)
        
        if marker_match:
            # Safety check: Ensure no new person marker "▲" between name and works
            # The name is at 0 in window (relative to name_idx)
            # The marker is at marker_match.start()
            
            segment_before_works = window[:marker_match.start()]
            if '▲' in segment_before_works:
                continue # Belongs to someone else
            
            # Also check for [编辑] which indicates a new section in Wikisource
            if '[编辑]' in segment_before_works:
                 continue

            start_pos = marker_match.end()
            works_section = window[start_pos:]
            
            # End marker: "凡" + number + "件"
            # Or next person marker "▲" or section "◎"
            # Or Wikisource edit link "[编辑]"
            
            # Regex for end markers
            # We want the earliest match
            end_markers = [r'凡[一二三四五六七八九十百]+件', r'▲', r'◎', r'\[编辑\]']
            
            min_end_pos = len(works_section)
            found_end = False
            
            for marker in end_markers:
                match = re.search(marker, works_section)
                if match:
                    if match.start() < min_end_pos:
                        min_end_pos = match.start()
                        found_end = True
            
            if found_end:
                works_raw = works_section[:min_end_pos]
                return works_raw
            elif len(works_section) < 2000: # If short and no marker, maybe it's the end of file
                 return works_section
                
    return None

def process_painters_wikisource():
    input_file = 'song_dynasty_figure_painters.csv'
    output_file = 'song_dynasty_painters_works_ancient.csv'
    
    painters = []
    with open(input_file, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        painters = list(reader)
        
    for p in painters:
        p['Ancient_Text_Works'] = ''
        
    # Xuanhe Huapu Chapters 1-7 (Taoist/Buddhist and Figures)
    # URLs need to be encoded
    base_url = "https://zh.wikisource.org/wiki/宣和畫譜/卷"
    
    # Chapters 1 to 7
    # Use Chinese numerals
    numerals = ['一', '二', '三', '四', '五', '六', '七']
    
    for i, num in enumerate(numerals):
        url = f"{base_url}{num}"
        encoded_url = urllib.parse.quote(url, safe=':/')
        print(f"Fetching {encoded_url}...")
        
        html = get_html(encoded_url)
        if not html:
            continue
            
        # Debug: Print first 500 chars of text
        clean_text = re.sub(r'<[^>]+>', '', html)
        clean_text = re.sub(r'\s+', '', clean_text)
        if i == 6: # Chapter 7 (index 6)
            print(f"Debug Chapter 7 content start: {clean_text[:200]}")
            if "李公麟" in clean_text:
                print("Found '李公麟' in Chapter 7.")
                idx = clean_text.find("李公麟")
                # Print a larger chunk to see where the works are
                print(f"Context: {clean_text[idx:idx+4000]}")
            else:
                print("Did NOT find '李公麟' in Chapter 7.")
        
        for p in painters:
            if p['Ancient_Text_Works']:
                continue
                
            name = p['Name']
            search_name = name
            if name.startswith('释'):
                search_name = name[1:]
                
            works = extract_works_from_wikisource(html, search_name)
            if works:
                print(f"  Found works for {name} in Chapter {num}")
                p['Ancient_Text_Works'] = works
                
        time.sleep(1)
        
    # Save
    fieldnames = list(painters[0].keys()) + ['Ancient_Text_Works']
    # Remove duplicates if any
    fieldnames = list(dict.fromkeys(fieldnames))
    
    with open(output_file, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(painters)
        
    print(f"Saved to {output_file}")

if __name__ == "__main__":
    process_painters_wikisource()
