import urllib.request
import urllib.parse
import json

def find_properties():
    endpoint_url = "https://query.wikidata.org/sparql"
    query = """
    SELECT ?property ?propertyLabel WHERE {
      ?property a wikibase:Property .
      ?property rdfs:label ?propertyLabel .
      FILTER(
        REGEX(?propertyLabel, "China Biographical Database", "i") || 
        REGEX(?propertyLabel, "Shanghai Library", "i") || 
        REGEX(?propertyLabel, "Geni.com", "i")
      )
      SERVICE wikibase:label { bd:serviceParam wikibase:language "en,zh". }
    }
    LIMIT 20
    """

    headers = {
        'User-Agent': 'VSCodeCopilotBot/1.0',
        'Accept': 'application/json'
    }

    params = urllib.parse.urlencode({'query': query, 'format': 'json'})
    url = f"{endpoint_url}?{params}"

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            
        for item in data['results']['bindings']:
            p_id = item['property']['value'].split('/')[-1]
            label = item['propertyLabel']['value']
            print(f"{p_id}: {label}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    find_properties()
