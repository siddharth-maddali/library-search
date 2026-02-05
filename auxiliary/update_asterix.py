import json
import os

DB_FILE = "library.json"

def update_asterix():
    if not os.path.exists(DB_FILE):
        print(f"Error: {DB_FILE} not found.")
        return

    with open(DB_FILE, 'r') as f:
        data = json.load(f)

    count = 0
    for item in data:
        # Check if it's an Asterix book based on path or title
        if "Asterix" in item.get('path', '') or "Asterix" in item.get('title', ''):
            # Update metadata
            item['author'] = "René Goscinny & Albert Uderzo"
            item['publisher'] = "Hachette"
            # Tag it as a comic/book if not set
            if not item.get('type'):
                item['type'] = "Comic"
            
            # Ensure these keywords exist
            keywords = set(item.get('keywords', []))
            keywords.add("comic")
            keywords.add("french")
            keywords.add("asterix")
            item['keywords'] = list(keywords)
            
            count += 1

    with open(DB_FILE, 'w') as f:
        json.dump(data, f, indent=4)

    print(f"Successfully updated {count} Asterix entries.")

if __name__ == "__main__":
    update_asterix()
