import urllib.request
import urllib.parse
import json

def search_wikidata_entity(search_term):
    url = "https://www.wikidata.org/w/api.php"
    params = {
        "action": "wbsearchentities",
        "format": "json",
        "language": "en",
        "search": search_term
    }
    query_string = urllib.parse.urlencode(params)
    full_url = f"{url}?{query_string}"
    
    try:
        req = urllib.request.Request(full_url, headers={'User-Agent': 'VSCodeCopilotBot/1.0'})
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            for item in data.get("search", []):
                print(f"{item['id']}: {item['label']} - {item.get('description', 'No description')}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    print("Searching for 'figure painting':")
    search_wikidata_entity("figure painting")
    print("\nSearching for 'portrait':")
    search_wikidata_entity("portrait")
