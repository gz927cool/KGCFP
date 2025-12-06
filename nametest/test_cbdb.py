import urllib.request
import urllib.parse
import json

def test_cbdb_query(name):
    base_url = "https://cbdb.fas.harvard.edu/cbdbapi/person.php"
    # CBDB API typically returns XML by default, let's check if json is an option or we parse XML
    # Trying o=json based on common API patterns, if not we will see XML in text
    params = urllib.parse.urlencode({'name': name, 'o': 'json'}) 
    url = f"{base_url}?{params}"
    
    print(f"Querying: {url}")
    
    try:
        with urllib.request.urlopen(url) as response:
            content = response.read().decode('utf-8')
            print("Response start:")
            print(content[:500]) # Print first 500 chars to inspect format
            return content
    except Exception as e:
        print(f"Error: {e}")
        return None

if __name__ == "__main__":
    test_cbdb_query("苏轼")
