import urllib.request
import urllib.parse

def check_book_url(book_name, juan_num):
    base_url = f"https://zh.wikisource.org/wiki/{book_name}/卷{juan_num}"
    encoded_url = urllib.parse.quote(base_url, safe=':/')
    print(f"Checking {encoded_url}...")
    
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    
    try:
        req = urllib.request.Request(encoded_url, headers=headers)
        with urllib.request.urlopen(req) as response:
            if response.status == 200:
                print("  Success!")
                return True
    except Exception as e:
        print(f"  Failed: {e}")
        return False

if __name__ == "__main__":
    # Check Hua Ji (Song Dynasty, covers Southern Song)
    check_book_url("畫繼", "一")
    check_book_url("畫繼", "1")
    
    # Check Tuhua Jianwen Zhi (Northern Song) - maybe different title format
    check_book_url("圖畫見聞誌", "一") # Zhi character variant
    check_book_url("图画见闻志", "一") # Simplified

