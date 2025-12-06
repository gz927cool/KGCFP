import urllib.request
import urllib.parse
import re

def debug_search():
    # Search for the book title
    encoded_query = urllib.parse.quote("宣和画谱")
    url = f"https://ctext.org/search?q={encoded_query}"
    
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as response:
            content = response.read().decode('utf-8')
            
            import re
            # Look for links that might be the book
            links = re.findall(r'href="([^"]+)"', content)
            print("Found links in search results:")
            for link in links:
                if "xuanhe-huapu" in link or "wiki.pl" in link:
                    print(link)
                
    except Exception as e:
        print(f"Error: {e}")
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_search()
