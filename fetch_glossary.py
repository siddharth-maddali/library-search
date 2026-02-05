import requests
from bs4 import BeautifulSoup
import json
import re

URLS = [
    "https://en.wikipedia.org/wiki/Glossary_of_physics",
    "https://en.wikipedia.org/wiki/Glossary_of_areas_of_mathematics"
]

def fetch_terms():
    terms = set()
    for url in URLS:
        try:
            headers = {
                'User-Agent': 'GeminiCLI/1.0 (Educational Purpose; contact: admin@example.com)'
            }
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Wikipedia glossaries usually use <dt> for terms or <b> inside <li> or <p>
            # Glossary of physics uses <dt class="glossary"> or just <dt>
            
            for dt in soup.find_all('dt'):
                term = dt.get_text().strip()
                # Clean up (remove citations like [1])
                term = re.sub(r'\[.*?\]', '', term)
                # Remove anything in parentheses
                term = re.sub(r'\(.*?\)', '', term)
                if term:
                    terms.add(term.lower().strip())

            # Specific handling for Areas of Mathematics which might be different (usually ul > li > a)
            if "mathematics" in url:
                for li in soup.find_all('li'):
                    a = li.find('a')
                    if a:
                        term = a.get_text().strip()
                        if term and len(term.split()) < 5: # simple heuristic to avoid long sentences
                             terms.add(term.lower().strip())
                             
        except Exception as e:
            print(f"Error fetching {url}: {e}")
    
    return sorted(list(terms))

if __name__ == "__main__":
    all_terms = fetch_terms()
    print(f"Found {len(all_terms)} terms.")
    with open("glossary.json", "w") as f:
        json.dump(all_terms, f, indent=2)
