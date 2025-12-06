import urllib.request
import urllib.parse

def test_ctext():
    url = "https://ctext.org/xuanhe-huapu/zh"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as response:
            content = response.read().decode('utf-8')
            print("Successfully fetched Xuanhe Huapu index.")
            print(content[:500])
    except Exception as e:
        print(f"Error fetching CTEXT: {e}")

if __name__ == "__main__":
    test_ctext()
