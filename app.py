from flask import Flask, render_template, request, jsonify, send_from_directory
import json
import os

app = Flask(__name__)
DB_FILE = "library.json"
library_data = []

def load_db():
    global library_data
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r') as f:
            library_data = json.load(f)
    else:
        print(f"Warning: {DB_FILE} not found. Run library_indexer.py first.")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

import logging

logging.basicConfig(filename='server.log', level=logging.DEBUG)

@app.route('/api/search')
def search():
    query_str = request.args.get('q', '').lower()
    logging.debug(f"Query: {query_str}")
    
    if not query_str:
        return jsonify([])
    
    # Parse filters (e.g., type:book)
    filters = {}
    search_terms = []
    
    parts = query_str.split()
    for part in parts:
        if ':' in part:
            key, val = part.split(':', 1)
            filters[key] = val
        else:
            search_terms.append(part)
            
    logging.debug(f"Filters: {filters}, Terms: {search_terms}")
    
    results = []
    
    for item in library_data:
        match = True
        
        # 1. Check Filters
        for key, val in filters.items():
            if key == 'type':
                item_type = item.get('type', '').lower()
                logging.debug(f"Checking Type: Item={item_type} vs Filter={val}")
                if item_type != val:
                    match = False
            elif key == 'publisher':
                item_pub = item.get('publisher', '').lower()
                logging.debug(f"Checking Pub: Item={item_pub} vs Filter={val}")
                if val not in item_pub:
                    match = False
            elif key == 'year':
                item_year = item.get('year_edition', '').lower()
                logging.debug(f"Checking Year: Item={item_year} vs Filter={val}")
                if val not in item_year:
                    match = False
                    
        if not match:
            continue
            
        # 2. Check Search Terms
        if search_terms:
            # Construct a comprehensive text blob for the item
            # including search_tokens which are technical terms found in content
            
            tokens_str = " ".join(item.get('search_tokens', []))
            keywords_str = " ".join(item.get('keywords', []))
            
            item_text = (
                f"{item['title']} {item['author']} {item.get('publisher', '')} "
                f"{item.get('year_edition', '')} {keywords_str} {tokens_str}"
            ).lower()
            
            if not all(term in item_text for term in search_terms):
                match = False
        
        if match:
            results.append(item)
    
    logging.debug(f"Found {len(results)} results")
    return jsonify(results)

# Allow serving the files themselves if needed (optional, but useful for "Path" link)
@app.route('/files/<path:filename>')
def download_file(filename):
    return send_from_directory('.', filename)

if __name__ == '__main__':
    load_db()
    app.run(host='0.0.0.0', port=5000)
