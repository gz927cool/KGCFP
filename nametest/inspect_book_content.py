import urllib.request
import urllib.parse

def get_wikisource_content(book_name, volume):
    base_url = "https://zh.wikisource.org/wiki/"
    # Encode the book name and volume part
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

def inspect_content(content, book_name, volume, snippet_length=2000):
    if not content:
        return
    
    # Find the main content area (heuristic for MediaWiki)
    start_marker = '<div class="mw-parser-output">'
    start_idx = content.find(start_marker)
    
    if start_idx != -1:
        # Clean up some HTML tags for readability in the terminal
        text = content[start_idx:start_idx+snippet_length]
        print("\n--- Content Snippet ---\n")
        print(text)
        print("\n-----------------------\n")
    else:
        print("Could not find main content div. Dumping raw start:")
        print(content[:500])

    # Save to file for inspection
    filename = f"content_{book_name}_v{volume}.html"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Saved content to {filename}")

print("Inspecting Hua Ji (画继) Volume 2...")
content_huaji = get_wikisource_content("畫繼", "二")
inspect_content(content_huaji, "HuaJi", "2")

print("\nInspecting Tuhua Jianwen Zhi (圖畫見聞誌) Volume 2...")
content_tuhua = get_wikisource_content("圖畫見聞誌", "二")
inspect_content(content_tuhua, "Tuhua", "2")
