import csv
import urllib.request
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

def get_chapter_links():
    base_url = "https://ctext.org/xuanhe-huapu"
    html = get_html(base_url)
    if not html:
        return []
    
    # Extract links like "xuanhe-huapu/juan-1"
    # The links in the index page are usually relative or absolute
    links = re.findall(r'href="(xuanhe-huapu/juan-[^"]+)"', html)
    
    # Deduplicate
    unique_links = sorted(list(set(links)))
    # Sort by juan number if possible, but string sort is okay for now
    return unique_links

def extract_works_from_text(text, painter_name):
    # Normalize text
    text = re.sub(r'\s+', '', text) # Remove all whitespace for easier matching
    
    # Find painter entry
    # In Xuanhe Huapu, the entry usually starts with the name, then biography.
    # But the name might appear multiple times.
    # The biography entry usually starts with the name at the beginning of a paragraph or section.
    # However, we can just look for the name and the "御府所藏" marker following it.
    
    # Find all occurrences of the name
    # We want the one followed by "御府所藏" within a reasonable distance (e.g., < 2000 chars)
    
    name_indices = [m.start() for m in re.finditer(re.escape(painter_name), text)]
    
    for name_idx in name_indices:
        # Look ahead for the works marker
        # Markers: "今御府所藏", "御府所藏"
        
        # Limit search window
        window = text[name_idx:name_idx+3000]
        
        marker_match = re.search(r'(今?御府所藏)', window)
        
        if marker_match:
            start_pos = marker_match.end()
            works_section = window[start_pos:]
            
            # The list of works usually ends with "凡..." (Total...) or the next person's name.
            # Or just a long list of titles.
            # Titles are often 2-4 chars.
            
            # Try to find the end
            # "凡" followed by number and "件"
            end_match = re.search(r'凡[一二三四五六七八九十百]+件', works_section)
            
            if end_match:
                works_raw = works_section[:end_match.start()]
                
                # Clean up works list
                # In Xuanhe Huapu, titles are just listed one after another.
                # We can try to separate them if we detect patterns, but raw is safer.
                return works_raw
            
    return None

def process_painters_from_book():
    input_file = 'song_dynasty_figure_painters.csv'
    output_file = 'song_dynasty_painters_works_ctext.csv'
    
    painters = []
    with open(input_file, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        painters = list(reader)
        
    # Initialize works
    for p in painters:
        p['CTEXT_Works'] = ''
        
    # Get chapters
    print("Fetching Xuanhe Huapu chapters...")
    chapter_links = get_chapter_links()
    print(f"Found {len(chapter_links)} chapters.")
    
    # Iterate chapters
    for link in chapter_links:
        full_url = f"https://ctext.org/{link}"
        print(f"Processing {link}...")
        
        html = get_html(full_url)
        if not html:
            continue
            
        # Clean HTML to text
        # Remove scripts, styles
        html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL)
        html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL)
        # Remove tags
        text = re.sub(r'<[^>]+>', '', html)
        
        # Check each painter
        for p in painters:
            if p['CTEXT_Works']: # Already found
                continue
                
            name = p['Name']
            # Handle "释..."
            search_name = name
            if name.startswith('释') and len(name) > 2:
                search_name = name[1:]
            
            # Check if name is in text
            if search_name in text:
                print(f"  Found mention of {name} in {link}")
                works = extract_works_from_text(text, search_name)
                if works:
                    print(f"  Extracted works for {name}!")
                    p['CTEXT_Works'] = works
                    
        time.sleep(1) # Be nice
        
    # Save
    fieldnames = list(painters[0].keys())
    with open(output_file, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(painters)
        
    print(f"Saved to {output_file}")

if __name__ == "__main__":
    process_painters_from_book()
