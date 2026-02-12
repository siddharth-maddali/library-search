import os
import re
import json
import sys
import requests
from bs4 import BeautifulSoup
import nltk
from nltk.corpus import stopwords

# Import TOC extractor
try:
    from extract_toc_tokens import extract_tokens_from_toc
except ImportError:
    sys.stderr.write("Warning: extract_toc_tokens.py not found. TOC extraction disabled.\n")
    def extract_tokens_from_toc(path): return []

# Ensure nltk resources are available (quietly)
try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords', quiet=True)

# Configuration
GLOSSARY_FILE = "glossary.json"
STOPWORDS = set(stopwords.words('english'))
# Add custom project-specific stopwords
STOPWORDS.update({"vol", "volume", "edition", "ed", "theory", "applications", "methods", "unknown", "bookfi", "org"})

COMMON_PUBLISHERS = [
    "Wiley", "Springer", "Dover", "MIT Press", "Cambridge University Press", 
    "Oxford University Press", "Pearson", "McGraw-Hill", "Elsevier", "Routledge", 
    "Princeton University Press", "Addison-Wesley", "O'Reilly", "Manning", 
    "Packt", "Cengage", "Taylor & Francis", "Sage", "Mir Publishers", "Mir", "Penguin", 
    "HarperCollins", "Simon & Schuster", "Macmillan", "Pergamon", "Butterworth"
]

def load_glossary():
    if os.path.exists(GLOSSARY_FILE):
        with open(GLOSSARY_FILE, 'r') as f:
            return set(json.load(f))
    return set()

GLOSSARY_TERMS = load_glossary()

def get_tokens_from_text(text):
    """Extracts technical terms from text using the glossary."""
    if not text: return []
    tokens = set()
    # Normalize text
    clean_text = re.sub(r'[^a-z0-9\s\-]', ' ', text.lower())
    words = clean_text.split()
    
    for i in range(len(words)):
        # Monograms
        w = words[i].strip()
        if len(w) > 2 and w in GLOSSARY_TERMS:
            tokens.add(w)
        
        # Bigrams
        if i < len(words) - 1:
            bigram = f"{words[i]} {words[i+1]}"
            if bigram in GLOSSARY_TERMS:
                tokens.add(bigram)
        
        # Polygrams (Trigrams)
        if i < len(words) - 2:
            trigram = f"{words[i]} {words[i+1]} {words[i+2]}"
            if trigram in GLOSSARY_TERMS:
                tokens.add(trigram)
                
    return list(tokens)

def fetch_wikipedia_content(query):
    """Searches Wikipedia and returns text content of the primary page."""
    search_url = f"https://en.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "list": "search",
        "srsearch": query,
        "format": "json"
    }
    headers = {
        "User-Agent": "ScientificLibraryIndexer/1.0 (contact: admin@example.com)"
    }
    try:
        response = requests.get(search_url, params=params, headers=headers, timeout=10)
        data = response.json()
        search_results = data.get("query", {}).get("search", [])
        
        if not search_results:
            return ""
        
        page_title = search_results[0]["title"]
        
        # Fetch actual page content
        content_params = {
            "action": "query",
            "prop": "extracts",
            "exintro": True,
            "explaintext": True,
            "titles": page_title,
            "format": "json"
        }
        content_response = requests.get(search_url, params=content_params, headers=headers, timeout=10)
        content_data = content_response.json()
        pages = content_data.get("query", {}).get("pages", {})
        
        for page_id in pages:
            return pages[page_id].get("extract", "")
            
    except Exception as e:
        sys.stderr.write(f"Wikipedia fetch error for '{query}': {e}\n")
    return ""

def extract_metadata(filepath):
    filename = os.path.basename(filepath)
    name_no_ext = os.path.splitext(filename)[0]
    
    metadata = {
        "author": "Unknown",
        "title": name_no_ext,
        "publisher": "Unknown",
        "year_edition": "",
        "type": "Unknown",
        "search_tokens": [],
        "path": os.path.relpath(filepath),
        "filename": filename
    }

    # 1. Filename Analysis
    working_name = name_no_ext.replace("_", " ")
    
    # a. [Author/Publisher] Title
    bracket_match = re.match(r'^\[(.*?)\]\s*(.*)', working_name)
    if bracket_match:
        leader = bracket_match.group(1).replace("_", " ").strip()
        trailer = bracket_match.group(2).replace("_", " ").strip()
        
        is_pub = False
        for pub in COMMON_PUBLISHERS:
            if pub.lower() in leader.lower():
                metadata["publisher"] = pub
                is_pub = True
                break
        
        if not is_pub:
            metadata["author"] = leader
        
        if trailer:
            metadata["title"] = trailer
    
    # b. Title - Author
    elif " - " in working_name:
        parts = working_name.split(" - ", 1)
        metadata["title"] = parts[0].replace("_", " ").strip()
        metadata["author"] = parts[1].replace("_", " ").strip()
    
    else:
        metadata["title"] = working_name.replace("_", " ").strip()

    # c. Year/Edition
    # Look for 4-digit years (1700-2099)
    year_match = re.search(r'\b((?:17|18|19|20)\d{2})\b', working_name)
    if year_match:
        metadata["year_edition"] = year_match.group(1)
        # Clean from title (including surrounding parentheses/brackets)
        metadata["title"] = re.sub(f'[\(\\[]?{re.escape(metadata["year_edition"])}[\)\]]?', '', metadata["title"]).strip()
    
    # Look for edition patterns like "2nd Ed", "3rd Edition", "1st ed"
    ed_match = re.search(r'(\d+(?:st|nd|rd|th)?\s*(?:[Ee]d(?:\.|ition)?))', working_name, re.IGNORECASE)
    if ed_match:
        ed_str = ed_match.group(1)
        metadata["year_edition"] += f", {ed_str}" if metadata["year_edition"] else ed_str
        # Clean from title
        metadata["title"] = re.sub(re.escape(ed_str), '', metadata["title"], flags=re.IGNORECASE).strip()

    # Final Title cleanup (double spaces, trailing punctuation)
    metadata["title"] = re.sub(r'\s+', ' ', metadata["title"]).strip()
    metadata["title"] = metadata["title"].rstrip('-_ ')

    # d. Publisher check in filename
    if metadata["publisher"] == "Unknown":
        for pub in COMMON_PUBLISHERS:
            if pub.lower() in working_name.lower():
                metadata["publisher"] = pub
                break

    # e.g. Type determination from filename/extension (approximation)
    filename_lower = filepath.lower()
    if ".pdf" in filename_lower or ".djvu" in filename_lower or ".djv" in filename_lower:
        # Heuristic: assume books unless keywords suggest otherwise
        metadata["type"] = "Book"

    # 2. Token Extraction from Title
    title_text = metadata["title"].lower()
    # Initial seeds for Wikipedia search
    seeds = get_tokens_from_text(title_text)
    
    # Add words from title that are not stopwords
    title_words = re.sub(r'[^a-z0-9\s]', ' ', title_text).split()
    for word in title_words:
        if len(word) > 3 and word not in STOPWORDS:
            seeds.append(word)
    
    seeds = sorted(list(set(seeds)))
    metadata["search_tokens"].extend(seeds)

    # 3. Extract tokens from TOC (for PDFs and DJVUs)
    filename_lower = filepath.lower()
    if ".pdf" in filename_lower or ".djvu" in filename_lower or ".djv" in filename_lower:
        sys.stderr.write(f"Extracting content tokens from {os.path.basename(filepath)}...\n")
        toc_tokens = extract_tokens_from_toc(filepath)
        if toc_tokens:
            sys.stderr.write(f"  Found {len(toc_tokens)} tokens from content.\n")
            metadata["search_tokens"].extend(toc_tokens)

    # 4. Wikipedia Expansion
    # To avoid excessive calls, limit to top 3 technical seeds
    if os.environ.get("SKIP_WIKI") == "1":
        sys.stderr.write("Skipping Wikipedia expansion (SKIP_WIKI=1)\n")
    else:
        technical_seeds = [s for s in seeds if s in GLOSSARY_TERMS][:3]
        if not technical_seeds and seeds:
            # fallback to the longest word/phrase
            technical_seeds = sorted(seeds, key=len, reverse=True)[:1]

        for seed in technical_seeds:
            sys.stderr.write(f"Expanding token: {seed} via Wikipedia...\n")
            wiki_text = fetch_wikipedia_content(seed)
            if wiki_text:
                wiki_tokens = get_tokens_from_text(wiki_text)
                metadata["search_tokens"].extend(wiki_tokens)

    # Final cleanup
    metadata["search_tokens"] = sorted(list(set(metadata["search_tokens"])))
    
    return metadata

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 library_indexer.py <file_path>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    if os.path.exists(file_path):
        meta = extract_metadata(file_path)
        print(json.dumps(meta, indent=2))
    else:
        sys.stderr.write(f"File not found: {file_path}\n")
        sys.exit(1)
