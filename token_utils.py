import os
import re
import json
import nltk
from nltk.corpus import stopwords

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

def load_glossary():
    """Loads glossary terms from the specified JSON file."""
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
