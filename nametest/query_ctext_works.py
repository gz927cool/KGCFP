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

def search_ctext(name):
    # Search specifically in Xuanhe Huapu first as it lists works systematically
    base_url = "https://ctext.org/xuanhe-huapu"
    # We can't easily search *inside* a book via URL parameters without using the global search
    # Global search: https://ctext.org/search?q=NAME
    
    encoded_name = urllib.parse.quote(name)
    search_url = f"https://ctext.org/search?q={encoded_name}"
    
    print(f"Searching for {name}...")
    html = get_html(search_url)
    
    if not html:
        return []

    # Look for links to Xuanhe Huapu chapters
    # Pattern: <a href="xuanhe-huapu/juan-...">
    # We want to prioritize Xuanhe Huapu
    
    links = re.findall(r'<a href="(xuanhe-huapu/[^"]+)"', html)
    
    # Deduplicate and prioritize
    unique_links = []
    for link in links:
        if link not in unique_links:
            unique_links.append(link)
            
    return unique_links

def extract_works_from_chapter(chapter_url, name):
    full_url = f"https://ctext.org/{chapter_url}"
    html = get_html(full_url)
    
    if not html:
        return []
        
    # Clean HTML tags to get text
    # This is a very rough cleaner
    text = re.sub(r'<[^>]+>', '', html)
    
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Find the section for the painter
    # Usually starts with name
    # In Xuanhe Huapu, the format is often: "Name ... biography ... 今御府所藏... works ..."
    
    # Find the index of the name
    name_idx = text.find(name)
    if name_idx == -1:
        return []
        
    # Look for "今御府所藏" (Stored in Imperial Repository) after the name
    # This phrase introduces the list of works in Xuanhe Huapu
    start_marker = "今御府所藏"
    start_idx = text.find(start_marker, name_idx)
    
    if start_idx == -1 or (start_idx - name_idx) > 2000: # If too far away, might be another person
        # Try "御府所藏"
        start_marker = "御府所藏"
        start_idx = text.find(start_marker, name_idx)
        
    if start_idx == -1 or (start_idx - name_idx) > 2000:
        return []
        
    # Extract text after marker
    works_text = text[start_idx + len(start_marker):]
    
    # The list usually ends with the number of works or the next person's name
    # Or just take a chunk and try to parse titles
    # Titles are often 2-5 characters, listed sequentially.
    # Example: "Work A, Work B, Work C..."
    # In CTEXT text, they might be just space separated or comma separated.
    
    # Let's take a chunk of 500 chars
    chunk = works_text[:500]
    
    # Heuristic extraction:
    # Look for patterns. In Xuanhe Huapu, it often lists: "Title One, Title Two..."
    # We will just return the raw chunk for now, or try to split by common separators if present.
    # Actually, let's just return the raw string and clean it up later or let the user see it.
    
    # Try to stop at the next number (often total count) or next person
    # "凡若干件" (Total X items)
    end_marker_match = re.search(r'凡[一二三四五六七八九十百]+件', chunk)
    if end_marker_match:
        chunk = chunk[:end_marker_match.start()]
        
    return chunk.strip()

def process_painters():
    input_file = 'song_dynasty_figure_painters.csv'
    output_file = 'song_dynasty_painters_works_ctext.csv'
    
    painters = []
    with open(input_file, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        painters = list(reader)
        
    # Add new column
    for p in painters:
        p['CTEXT_Works'] = ''
        
    print(f"Processing {len(painters)} painters...")
    
    for i, p in enumerate(painters):
        name = p['Name']
        # Handle names like "释..." (Shi...)
        search_name = name
        if name.startswith('释'):
            search_name = name[1:] # Search for the name without Shi title might be better, or keep it.
            
        links = search_ctext(search_name)
        
        found_works = []
        
        # Only check the first few links to avoid spamming
        for link in links[:3]:
            print(f"  Checking {link}...")
            works = extract_works_from_chapter(link, search_name)
            if works:
                # Clean up the works string
                # Remove common noise
                works = works.replace('&nbsp;', ' ').replace('：', '')
                # Try to split into a list if it looks like a list
                # In Xuanhe Huapu, titles are often just concatenated.
                found_works.append(works)
                break # Found the main entry
        
        if found_works:
            p['CTEXT_Works'] = "; ".join(found_works)
            print(f"  Found works for {name}")
        else:
            print(f"  No works found for {name}")
            
        time.sleep(1)
        
    # Save
    fieldnames = list(painters[0].keys())
    with open(output_file, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(painters)
        
    print(f"Saved to {output_file}")

if __name__ == "__main__":
    process_painters()
