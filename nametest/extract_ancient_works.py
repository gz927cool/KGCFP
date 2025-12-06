import urllib.request
import urllib.parse
import re
import csv
import time
import os

def get_wikisource_content(book_name, volume):
    base_url = "https://zh.wikisource.org/wiki/"
    path = f"{book_name}/卷{volume}"
    encoded_path = urllib.parse.quote(path)
    url = base_url + encoded_path
    
    print(f"Fetching: {url}")
    
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as response:
            content = response.read().decode('utf-8')
            return content
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

def extract_works_from_text(text):
    # Find all content within 《》
    works = re.findall(r'《(.*?)》', text)
    return works

def parse_huaji(content, volume):
    painters_data = []
    if not content:
        return painters_data
        
    # Split by paragraphs or just look for <b>Name</b> patterns
    # The structure is <p><b>Name</b>，Description...</p>
    # or <p>...<b>Name</b>...</p>
    
    # Regex to find <b>Name</b> followed by text until next <b> or end of p
    # Note: This is a simple regex, might miss some edge cases
    
    # Find all paragraphs first
    paragraphs = re.findall(r'<p>(.*?)</p>', content, re.DOTALL)
    
    for p in paragraphs:
        # Check if there is a bold name at the start or inside
        # Usually in Hua Ji it's <b>Name</b> at the start of the entry
        name_match = re.search(r'<b>(.*?)</b>', p)
        if name_match:
            name = name_match.group(1)
            # Clean name (remove html tags if any inside, though unlikely for name)
            name = re.sub(r'<.*?>', '', name)
            
            # Extract works from the whole paragraph
            works = extract_works_from_text(p)
            
            if works:
                painters_data.append({
                    'Painter': name,
                    'Book': '画继',
                    'Volume': volume,
                    'Works': '; '.join(works),
                    'Raw_Text': re.sub(r'<.*?>', '', p)[:100] + "..." # Store snippet
                })
    
    return painters_data

def parse_tuhua(content, volume):
    painters_data = []
    if not content:
        return painters_data
    
    # Tuhua structure: <p>Name，Place...</p>
    # We need to be careful.
    
    paragraphs = re.findall(r'<p>(.*?)</p>', content, re.DOTALL)
    
    for p in paragraphs:
        clean_p = re.sub(r'<.*?>', '', p).strip()
        if not clean_p:
            continue
            
        # Heuristic: The paragraph starts with a name followed by a comma or space
        # And it contains "有《...》" or just "《...》"
        
        # Try to extract name. Usually 2-4 chars at the start.
        # Look for pattern: "Name，" or "Name "
        match = re.match(r'^([\u4e00-\u9fa5]{2,4})[，,]', clean_p)
        if match:
            name = match.group(1)
            
            # Filter out common non-names if necessary (e.g. "叙论", "唐末")
            if "二十七人" in name or "九十一人" in name:
                continue
                
            # Clean titles like "道士张素卿" -> "张素卿"
            if name.startswith("道士"):
                name = name[2:]
            if name.startswith("僧"):
                name = name[1:]
            
            works = extract_works_from_text(clean_p)
            if works:
                painters_data.append({
                    'Painter': name,
                    'Book': '图画见闻志',
                    'Volume': volume,
                    'Works': '; '.join(works),
                    'Raw_Text': clean_p[:100] + "..."
                })
                
    return painters_data

def main():
    all_data = []
    
    # Process Hua Ji (Volumes 1-10)
    # Note: Volume 1 is usually intro, but we check anyway
    chinese_nums = ["一", "二", "三", "四", "五", "六", "七", "八", "九", "十"]
    
    print("Processing Hua Ji...")
    for i, num in enumerate(chinese_nums):
        vol_num = str(i + 1)
        content = get_wikisource_content("畫繼", num)
        if content:
            data = parse_huaji(content, vol_num)
            print(f"  Vol {vol_num}: Found {len(data)} painters with works.")
            all_data.extend(data)
        time.sleep(1) # Be nice to the server

    # Process Tuhua Jianwen Zhi (Volumes 1-6)
    print("\nProcessing Tuhua Jianwen Zhi...")
    for i, num in enumerate(chinese_nums[:6]):
        vol_num = str(i + 1)
        content = get_wikisource_content("圖畫見聞誌", num)
        if content:
            data = parse_tuhua(content, vol_num)
            print(f"  Vol {vol_num}: Found {len(data)} painters with works.")
            all_data.extend(data)
        time.sleep(1)

    # Save to CSV
    output_file = 'ancient_text_works_extracted.csv'
    keys = ['Painter', 'Book', 'Volume', 'Works', 'Raw_Text']
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(all_data)
        
    print(f"\nSaved {len(all_data)} records to {output_file}")

if __name__ == "__main__":
    main()
