import pdfplumber
import sys
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.util import ngrams
from nltk.tag import pos_tag
import string
import re
import os
import subprocess
import pytesseract
from pdf2image import convert_from_path
from PIL import Image
import io

# Import project utilities
try:
    from token_utils import get_tokens_from_text, GLOSSARY_TERMS
except ImportError:
    def get_tokens_from_text(text): return []
    GLOSSARY_TERMS = set()

# Download necessary NLTK data
try:
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('tokenizers/punkt_tab')
except LookupError:
    nltk.download('punkt', quiet=True)
    nltk.download('punkt_tab', quiet=True)
try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords', quiet=True)
try:
    nltk.data.find('taggers/averaged_perceptron_tagger')
    nltk.data.find('taggers/averaged_perceptron_tagger_eng')
except LookupError:
    nltk.download('averaged_perceptron_tagger', quiet=True)
    nltk.download('averaged_perceptron_tagger_eng', quiet=True)

# Configuration
MAX_PAGES_TEXT = 50
MAX_PAGES_OCR = 25
ABSTRACT_KEYWORDS = [r'\babstract\b', r'\bintroduction\b', r'\bsummary\b']

def clean_text(text):
    if not text: return ""
    # Remove leader dots ......
    text = re.sub(r'\.{2,}', ' ', text) 
    # Remove page numbers at end of line
    text = re.sub(r'\s+\d+\s*$', '', text, flags=re.MULTILINE)
    # Remove sequences of digits that look like page numbers
    text = re.sub(r'\b\d+\b', '', text)
    # Remove Roman numerals often found in TOCs
    text = re.sub(r'\b[ivxlcdm]+\b', '', text, flags=re.IGNORECASE)
    # Remove non-alphanumeric (keep spaces and hyphens)
    text = re.sub(r'[^a-zA-Z\s\-]', ' ', text)
    # Collapse whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def extract_tokens_from_djvu(filepath):
    """Extracts text from DJVU using djvutxt for the first MAX_PAGES_TEXT pages."""
    try:
        # djvutxt doesn't easily support page ranges without extracting page by page
        # But we can try to extract the whole thing and take the first chunk of text
        # Or better, loop through pages
        combined_text = ""
        for p in range(1, MAX_PAGES_TEXT + 1):
            cmd = ["djvutxt", f"--page={p}", filepath]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            if result.returncode != 0:
                if p == 1:
                    sys.stderr.write(f"  djvutxt failed on page 1: {result.stderr}\n")
                break
            combined_text += result.stdout + "\n"
        return combined_text
    except Exception as e:
        sys.stderr.write(f"  DJVU extraction error: {e}\n")
        return ""

def get_ocr_text(pdf_path, max_pages=MAX_PAGES_OCR):
    """Performs OCR on the first max_pages of a PDF."""
    sys.stderr.write(f"  Performing OCR on first {max_pages} pages...\n")
    ocr_text = ""
    try:
        # Convert PDF to images page-by-page to save memory
        for i in range(1, max_pages + 1):
            images = convert_from_path(pdf_path, first_page=i, last_page=i, dpi=200)
            if not images:
                break
            page_text = pytesseract.image_to_string(images[0])
            ocr_text += page_text + "\n"
            
            # Early exit if we find TOC-like structure
            if "contents" in page_text.lower() or "table of contents" in page_text.lower():
                # If we found the start of TOC, maybe grab 2 more pages and stop
                sys.stderr.write(f"  TOC found via OCR on page {i}. Continuing briefly...\n")
                # Continue for at most 3 more pages
                for j in range(i+1, min(i+4, max_pages + 1)):
                    imgs = convert_from_path(pdf_path, first_page=j, last_page=j, dpi=200)
                    if imgs:
                        ocr_text += pytesseract.image_to_string(imgs[0]) + "\n"
                break
    except Exception as e:
        sys.stderr.write(f"  OCR Error: {e}\n")
    return ocr_text

def extract_tokens_from_toc(filepath):
    # Support .pdf.1, .djvu.1 etc.
    filename_lower = filepath.lower()
    full_text = ""
    
    if ".djvu" in filename_lower or ".djv" in filename_lower:
        sys.stderr.write(f"Processing DJVU: {filepath}\n")
        full_text = extract_tokens_from_djvu(filepath)
    elif ".pdf" in filename_lower:
        sys.stderr.write(f"Processing PDF: {filepath}\n")
        try:
            with pdfplumber.open(filepath) as pdf:
                # 1. Digital Outline
                if hasattr(pdf, 'outline') and pdf.outline:
                    sys.stderr.write("  Found digital outline.\n")
                    for item in pdf.outline:
                        if isinstance(item, dict):
                            full_text += item.get('title', '') + " "
                
                # 2. Visual Scan (First 50 pages)
                if not full_text.strip():
                    sys.stderr.write(f"  Scanning first {MAX_PAGES_TEXT} pages for TOC/Abstract...\n")
                    found_relevant = False
                    pages_to_extract = []
                    
                    limit = min(len(pdf.pages), MAX_PAGES_TEXT)
                    for i in range(limit):
                        p_text = pdf.pages[i].extract_text(x_tolerance=1)
                        if not p_text: continue
                        
                        lower_text = p_text.lower()
                        # Check for TOC or Abstract
                        if "contents" in lower_text or "abstract" in lower_text or "introduction" in lower_text:
                            found_relevant = True
                            # Extract this page and the next few
                            for j in range(i, min(i + 5, limit)):
                                pages_to_extract.append(j)
                            break
                    
                    # If nothing found, just take the first 5 pages anyway as fallback
                    if not found_relevant:
                        pages_to_extract = list(range(min(5, len(pdf.pages))))
                    
                    for p_idx in sorted(list(set(pages_to_extract))):
                        txt = pdf.pages[p_idx].extract_text(x_tolerance=1)
                        if txt:
                            full_text += txt + "\n"

                # 3. OCR Fallback if still no text (First 25 pages)
                if not full_text.strip() or len(full_text.strip()) < 100:
                    sys.stderr.write("  Text extraction yielded very little. Falling back to OCR...\n")
                    full_text = get_ocr_text(filepath, max_pages=MAX_PAGES_OCR)
                else:
                    sys.stderr.write(f"  Extracted {len(full_text)} chars using pdfplumber.\n")

        except Exception as e:
            sys.stderr.write(f"  Error reading PDF {filepath}: {e}\n")

    if not full_text.strip():
        sys.stderr.write("  No text extracted from document.\n")
        return []

    # Clean and tokenize
    # Use glossary-based extraction first
    tokens = set(get_tokens_from_text(full_text))
    
    # Supplemental: Use NLTK to find potential technical terms not in glossary
    clean_txt = clean_text(full_text)
    words = word_tokenize(clean_txt.lower())
    
    # We'll use a simplified version of the previous is_technical_token logic 
    # to add high-quality candidates even if not in glossary
    stop_words = set(stopwords.words('english'))
    
    # Bigrams/Trigrams that look technical
    bi = list(ngrams(words, 2))
    tri = list(ngrams(words, 3))
    
    candidates = [" ".join(g) for g in bi] + [" ".join(g) for g in tri]
    
    for cand in candidates:
        # Heuristic: if it's 2-3 words, not stopwords, and looks like a noun phrase
        cand_words = cand.split()
        if all(len(w) > 2 for w in cand_words) and not any(w in stop_words for w in cand_words):
            # Check POS tags
            tags = pos_tag(cand_words)
            if all(t.startswith('NN') or t.startswith('JJ') for w, t in tags):
                tokens.add(cand)

    return sorted(list(tokens))

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 extract_toc_tokens.py <file_path>")
        sys.exit(1)
        
    result = extract_tokens_from_toc(sys.argv[1])
    if result:
        print(f"\nExtracted {len(result)} unique tokens.")
        print("-" * 40)
        print(", ".join(result))
        print("-" * 40)
    else:
        print("\nNo tokens extracted.")
