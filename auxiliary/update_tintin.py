import json
import os
import re

DB_FILE = "library.json"

def update_tintin():
    if not os.path.exists(DB_FILE):
        print(f"Error: {DB_FILE} not found.")
        return

    with open(DB_FILE, 'r') as f:
        data = json.load(f)

    count = 0
    for item in data:
        path = item.get('path', '')
        # Check if it's a Tintin book based on path (case-insensitive)
        if "tintin" in path.lower():
            # Extract filename without extension
            filename = os.path.splitext(os.path.basename(path))[0]
            
            new_title = filename.strip()
            
            # Pattern 1: "Number Tintin - Title" (e.g. "11 Tintin - Secret Of The Unicorn")
            # We look for a hyphen surrounded by whitespace
            parts = re.split(r'\s+-\s+', filename, 1)
            if len(parts) > 1:
                # Take the part after the hyphen
                new_title = parts[1].strip()
            else:
                # Pattern 2: "Number Title" (e.g. "03 Tintin In America")
                # Just remove the leading digits and whitespace
                new_title = re.sub(r'^\d+\s+', '', filename).strip()

            # Update title
            item['title'] = new_title

            # Update metadata
            item['author'] = "Hergé"
            item['publisher'] = "Casterman"
            # Tag it as a comic/book if not set
            if not item.get('type'):
                item['type'] = "Comic"
            
            # Ensure these keywords exist
            keywords = set(item.get('keywords', []))
            keywords.add("comic")
            keywords.add("tintin")
            keywords.add("hergé")
            item['keywords'] = list(keywords)
            
            count += 1

    with open(DB_FILE, 'w') as f:
        json.dump(data, f, indent=4)

    print(f"Successfully updated {count} Tintin entries.")

if __name__ == "__main__":
    update_tintin()