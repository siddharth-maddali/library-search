import pdfplumber
import sys
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.util import ngrams
from nltk.tag import pos_tag
import string
import re

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

COMMON_ACADEMIC_TERMS = {
    'chapter', 'page', 'contents', 'table', 'section', 'index', 'appendix', 
    'introduction', 'preface', 'bibliography', 'references', 'part', 'volume',
    'edition', 'author', 'title', 'copyright', 'foreword', 'abbreviations', 
    'acknowledgements', 'overview', 'review', 'aim', 'goal', 'method', 'result', 
    'discussion', 'analysis', 'study', 'work', 'paper', 'book', 'text', 'reference', 
    'note', 'example', 'exercise', 'problem', 'solution', 'answer', 'question', 
    'test', 'exam', 'assignment', 'lecture', 'course', 'syllabus', 'schedule', 
    'calendar', 'time', 'date', 'year', 'month', 'day', 'week', 'hour', 'minute', 
    'second', 'first', 'second', 'third', 'fourth', 'fifth', 'last', 'next', 
    'previous', 'following', 'general', 'specific', 'basic', 'advanced', 
    'elementary', 'intermediate', 'total', 'average', 'mean', 'median', 'mode', 
    'maximum', 'minimum', 'high', 'low', 'small', 'large', 'big', 'short', 'long',
    'better', 'worse', 'good', 'bad', 'best', 'worst', 'simple', 'complex', 
    'hard', 'easy', 'new', 'old', 'modern', 'ancient', 'future', 'past', 
    'current', 'present', 'various', 'several', 'many', 'much', 'few', 'little',
    'less', 'more', 'most', 'least', 'some', 'any', 'all', 'none', 'every', 
    'each', 'other', 'another', 'such', 'this', 'that', 'these', 'those', 
    'which', 'what', 'where', 'when', 'who', 'whom', 'whose', 'why', 'how',
    'definition', 'definitions', 'defined', 'summary', 'summaries', 'conclusion',
    'conclusions', 'remark', 'remarks', 'further', 'reading', 'readings',
    'concept', 'concepts', 'principle', 'principles', 'theory', 'theories',
    'application', 'applications', 'system', 'systems', 'structure', 'structures',
    'process', 'processes', 'function', 'functions', 'property', 'properties',
    'background', 'material', 'materials', 'view', 'views', 'perspective', 
    'perspectives', 'approach', 'approaches', 'technique', 'techniques',
    'topic', 'topics', 'issue', 'issues', 'aspect', 'aspects', 'feature',
    'features', 'element', 'elements', 'component', 'components', 'unit', 'units',
    'item', 'items', 'detail', 'details', 'description', 'descriptions',
    'explanation', 'explanations', 'illustrative', 'illustration', 'illustrations',
    'case', 'cases', 'studies', 'survey', 'surveys', 'report', 'reports',
    'history', 'historical', 'development', 'developments', 'evolution',
    'foundation', 'foundations', 'fundamental', 'fundamentals', 'basis', 'bases',
    'core', 'key', 'main', 'major', 'minor', 'significant', 'important',
    'relevant', 'related', 'associated', 'connected', 'linked', 'common',
    'standard', 'typical', 'usual', 'normal', 'regular', 'ordinary', 'special',
    'specific', 'particular', 'individual', 'unique', 'distinct', 'different',
    'similar', 'same', 'equal', 'equivalent', 'identical', 'constant', 'variable',
    'parameter', 'factor', 'coefficient', 'value', 'data', 'information',
    'knowledge', 'understanding', 'insight', 'wisdom', 'truth', 'fact', 'reality',
    'existence', 'nature', 'essence', 'meaning', 'sense', 'interpretation',
    'translation', 'version', 'edition', 'publication', 'publisher', 'published',
    'print', 'printed', 'printing', 'press', 'journal', 'magazine', 'article',
    'essay', 'thesis', 'dissertation', 'monograph', 'treatise', 'manual',
    'guide', 'handbook', 'textbook', 'dictionary', 'encyclopedia', 'glossary',
    'vocabulary', 'terminology', 'language', 'grammar', 'syntax', 'semantics',
    'style', 'format', 'layout', 'design', 'structure', 'organization',
    'arrangement', 'order', 'sequence', 'series', 'list', 'table', 'chart',
    'graph', 'diagram', 'figure', 'image', 'picture', 'photo', 'photograph',
    'map', 'plan', 'scheme', 'sketch', 'draft', 'outline', 'summary', 'abstract',
    'extract', 'excerpt', 'quote', 'quotation', 'citation', 'reference',
    'bibliography', 'index', 'appendix', 'supplement', 'addendum', 'attachment',
    'enclosure', 'insert', 'inset', 'label', 'tag', 'marker', 'sign', 'symbol',
    'icon', 'logo', 'badge', 'emblem', 'crest', 'seal', 'stamp', 'brand',
    'trademark', 'copyright', 'patent', 'license', 'permit', 'permission',
    'authorization', 'authority', 'right', 'ownership', 'possession', 'property',
    'asset', 'liability', 'debt', 'credit', 'debit', 'balance', 'account',
    'ledger', 'journal', 'register', 'record', 'file', 'document', 'paper',
    'form', 'sheet', 'page', 'leaf', 'folio', 'recto', 'verso', 'side',
    'face', 'back', 'front', 'top', 'bottom', 'left', 'right', 'center',
    'middle', 'edge', 'margin', 'border', 'boundary', 'limit', 'end',
    'start', 'beginning', 'commencement', 'inception', 'origin', 'source',
    'root', 'cause', 'reason', 'purpose', 'motive', 'intent', 'intention',
    'objective', 'goal', 'aim', 'target', 'destination', 'direction', 'path',
    'way', 'route', 'course', 'track', 'trail', 'line', 'row', 'column',
    'grid', 'matrix', 'array', 'network', 'web', 'mesh', 'lattice', 'chain',
    'link', 'connection', 'relationship', 'relation', 'association', 'bond',
    'tie', 'knot', 'joint', 'junction', 'interface', 'interaction', 'interplay',
    'exchange', 'transfer', 'transmission', 'communication', 'contact', 'touch',
    'impact', 'influence', 'effect', 'result', 'outcome', 'consequence',
    'product', 'output', 'yield', 'return', 'gain', 'loss', 'benefit', 'cost',
    'price', 'value', 'worth', 'quality', 'quantity', 'amount', 'number',
    'count', 'measure', 'size', 'dimension', 'extent', 'magnitude', 'volume',
    'capacity', 'weight', 'mass', 'density', 'force', 'energy', 'power',
    'strength', 'weakness', 'speed', 'velocity', 'acceleration', 'momentum',
    'inertia', 'friction', 'resistance', 'stress', 'strain', 'tension',
    'pressure', 'temperature', 'heat', 'cold', 'light', 'dark', 'sound',
    'noise', 'silence', 'color', 'shape', 'form', 'texture', 'pattern',
    'model', 'type', 'kind', 'sort', 'class', 'category', 'group', 'set',
    'collection', 'batch', 'lot', 'bunch', 'cluster', 'pack', 'package',
    'bundle', 'parcel', 'packet', 'container', 'vessel', 'box', 'case',
    'crate', 'bin', 'bag', 'sack', 'pocket', 'pouch', 'envelope', 'wrapper',
    'cover', 'lid', 'cap', 'top', 'bottom', 'side', 'wall', 'floor',
    'ceiling', 'roof', 'door', 'window', 'opening', 'hole', 'gap', 'crack',
    'split', 'tear', 'cut', 'break', 'fracture', 'fragment', 'piece', 'part',
    'segment', 'section', 'sector', 'zone', 'region', 'area', 'field',
    'domain', 'realm', 'world', 'universe', 'space', 'time', 'dimension',
    'plane', 'level', 'stage', 'phase', 'state', 'condition', 'situation',
    'circumstance', 'environment', 'context', 'background', 'setting',
    'scene', 'scenario', 'landscape', 'view', 'vista', 'panorama', 'spectacle',
    'sight', 'vision', 'appearance', 'aspect', 'facade', 'surface', 'exterior',
    'interior', 'inside', 'outside', 'center', 'core', 'heart', 'nucleus',
    'focus', 'focal', 'point', 'spot', 'location', 'place', 'position',
    'site', 'venue', 'station', 'post', 'base', 'camp', 'home', 'house',
    'building', 'structure', 'construction', 'erection', 'fabrication',
    'creation', 'production', 'manufacture', 'assembly', 'installation',
    'setup', 'arrangement', 'organization', 'management', 'administration',
    'control', 'regulation', 'supervision', 'oversight', 'direction',
    'guidance', 'leadership', 'command', 'authority', 'power', 'influence',
    'prestige', 'status', 'rank', 'grade', 'level', 'tier', 'class',
    'category', 'group', 'division', 'section', 'department', 'branch',
    'unit', 'team', 'crew', 'staff', 'personnel', 'workforce', 'labor',
    'worker', 'employee', 'employer', 'manager', 'boss', 'chief', 'head',
    'leader', 'director', 'executive', 'officer', 'official', 'administrator',
    'supervisor', 'foreman', 'overseer', 'controller', 'regulator', 'inspector',
    'examiner', 'auditor', 'assessor', 'evaluator', 'judge', 'jury',
    'arbitrator', 'mediator', 'negotiator', 'diplomat', 'ambassador',
    'representative', 'delegate', 'deputy', 'agent', 'proxy', 'substitute',
    'replacement', 'successor', 'heir', 'beneficiary', 'recipient', 'receiver',
    'giver', 'donor', 'provider', 'supplier', 'vendor', 'seller', 'merchant',
    'trader', 'dealer', 'broker', 'buyer', 'purchaser', 'consumer', 'user',
    'client', 'customer', 'patron', 'guest', 'visitor', 'tourist', 'traveler',
    'passenger', 'commuter', 'driver', 'pilot', 'operator', 'mechanic',
    'technician', 'engineer', 'scientist', 'researcher', 'scholar', 'academic',
    'student', 'pupil', 'learner', 'apprentice', 'novice', 'beginner',
    'expert', 'specialist', 'professional', 'master', 'authority', 'guru',
    'teacher', 'instructor', 'tutor', 'mentor', 'coach', 'trainer', 'educator',
    'professor', 'lecturer', 'speaker', 'presenter', 'author', 'writer',
    'editor', 'publisher', 'critic', 'reviewer', 'journalist', 'reporter',
    'broadcaster', 'announcer', 'narrator', 'storyteller', 'artist', 'painter',
    'sculptor', 'musician', 'composer', 'performer', 'actor', 'actress',
    'director', 'producer', 'designer', 'architect', 'builder', 'carpenter',
    'plumber', 'electrician', 'mason', 'welder', 'machinist', 'operator',
    'farmer', 'gardener', 'grower', 'breeder', 'hunter', 'fisher', 'cook',
    'chef', 'baker', 'butcher', 'waiter', 'server', 'bartender', 'cleaner',
    'janitor', 'custodian', 'guard', 'watchman', 'policeman', 'officer',
    'soldier', 'sailor', 'marine', 'pilot', 'astronaut', 'doctor', 'physician',
    'surgeon', 'nurse', 'dentist', 'pharmacist', 'therapist', 'psychologist',
    'psychiatrist', 'counselor', 'social', 'worker', 'lawyer', 'attorney',
    'solicitor', 'barrister', 'judge', 'prosecutor', 'defender', 'plaintiff',
    'defendant', 'witness', 'victim', 'suspect', 'criminal', 'offender',
    'prisoner', 'inmate', 'convict', 'delinquent', 'sinner', 'saint',
    'angel', 'demon', 'devil', 'ghost', 'spirit', 'soul', 'mind', 'body',
    'heart', 'blood', 'sweat', 'tears', 'flesh', 'bone', 'skin', 'hair',
    'nail', 'tooth', 'eye', 'ear', 'nose', 'mouth', 'lip', 'tongue',
    'throat', 'neck', 'shoulder', 'arm', 'elbow', 'wrist', 'hand', 'finger',
    'thumb', 'chest', 'breast', 'stomach', 'belly', 'waist', 'hip', 'leg',
    'knee', 'ankle', 'foot', 'toe', 'brain', 'lung', 'heart', 'liver',
    'kidney', 'stomach', 'intestine', 'muscle', 'nerve', 'vein', 'artery',
    'cell', 'tissue', 'organ', 'system', 'organism', 'creature', 'being',
    'entity', 'life', 'death', 'birth', 'growth', 'decay', 'sickness',
    'illness', 'disease', 'health', 'wellness', 'fitness', 'strength',
    'weakness', 'pain', 'pleasure', 'joy', 'sorrow', 'happiness', 'sadness',
    'anger', 'fear', 'love', 'hate', 'hope', 'despair', 'faith', 'doubt',
    'belief', 'knowledge', 'ignorance', 'wisdom', 'folly', 'truth', 'lie',
    'fact', 'fiction', 'history', 'myth', 'legend', 'story', 'tale',
    'narrative', 'account', 'report', 'record', 'document', 'file', 'archive',
    'library', 'museum', 'gallery', 'theater', 'cinema', 'studio', 'laboratory',
    'factory', 'workshop', 'office', 'store', 'shop', 'market', 'mall',
    'center', 'station', 'terminal', 'port', 'harbor', 'airport', 'park',
    'garden', 'forest', 'wood', 'field', 'meadow', 'pasture', 'farm',
    'ranch', 'estate', 'property', 'land', 'ground', 'soil', 'earth',
    'rock', 'stone', 'sand', 'clay', 'mud', 'dust', 'dirt', 'filth',
    'waste', 'trash', 'garbage', 'rubbish', 'junk', 'scrap', 'debris',
    'remains', 'residue', 'trace', 'sign', 'mark', 'stain', 'spot',
    'blemish', 'flaw', 'defect', 'error', 'mistake', 'fault', 'failure',
    'success', 'victory', 'triumph', 'win', 'loss', 'defeat', 'draw',
    'tie', 'stalemate', 'deadlock', 'impasse', 'standoff', 'conflict',
    'fight', 'battle', 'war', 'peace', 'treaty', 'agreement', 'deal',
    'contract', 'pact', 'alliance', 'coalition', 'union', 'league',
    'federation', 'confederation', 'association', 'organization', 'society',
    'club', 'group', 'team', 'party', 'band', 'gang', 'crowd', 'mob',
    'throng', 'horde', 'mass', 'multitude', 'majority', 'minority',
    'rest', 'remainder', 'surplus', 'excess', 'deficit', 'shortage',
    'lack', 'want', 'need', 'demand', 'supply', 'stock', 'store',
    'reserve', 'hoard', 'fund', 'capital', 'wealth', 'money', 'cash',
    'currency', 'coin', 'bill', 'check', 'credit', 'debt', 'loan',
    'mortgage', 'lease', 'rent', 'tax', 'fee', 'charge', 'price',
    'cost', 'expense', 'expenditure', 'spending', 'saving', 'investment',
    'profit', 'income', 'revenue', 'earning', 'wage', 'salary', 'pay',
    'payment', 'compensation', 'reward', 'bonus', 'prize', 'gift',
    'donation', 'contribution', 'offering', 'grant', 'subsidy', 'aid',
    'help', 'support', 'assistance', 'service', 'care', 'attention',
    'regard', 'respect', 'honor', 'esteem', 'admiration', 'praise',
    'glory', 'fame', 'reputation', 'character', 'nature', 'personality',
    'identity', 'self', 'ego', 'mind', 'soul', 'spirit', 'ghost',
    'god', 'devil', 'angel', 'demon', 'heaven', 'hell', 'paradise',
    'purgatory', 'limbo', 'void', 'nothingness', 'eternity', 'infinity',
    'time', 'space', 'universe', 'cosmos', 'world', 'earth', 'planet',
    'star', 'sun', 'moon', 'sky', 'air', 'wind', 'cloud', 'rain',
    'snow', 'ice', 'hail', 'storm', 'thunder', 'lightning', 'fire',
    'water', 'sea', 'ocean', 'river', 'lake', 'stream', 'pond',
    'pool', 'spring', 'well', 'fountain', 'source', 'mouth', 'bed',
    'bank', 'shore', 'coast', 'beach', 'sand', 'wave', 'tide',
    'current', 'flow', 'flood', 'drought', 'famine', 'plague', 'pestilence',
    'epidemic', 'pandemic', 'disaster', 'catastrophe', 'calamity', 'tragedy',
    'accident', 'incident', 'event', 'occurrence', 'happening', 'phenomenon',
    'miracle', 'wonder', 'marvel', 'surprise', 'shock', 'horror', 'terror',
    'fear', 'dread', 'panic', 'anxiety', 'worry', 'concern', 'trouble',
    'problem', 'difficulty', 'hardship', 'struggle', 'effort', 'attempt',
    'trial', 'test', 'experiment', 'investigation', 'inquiry', 'question',
    'answer', 'solution', 'explanation', 'theory', 'hypothesis', 'guess',
    'estimate', 'calculation', 'measurement', 'observation', 'discovery',
    'invention', 'creation', 'innovation', 'change', 'alteration', 'modification',
    'variation', 'transformation', 'conversion', 'evolution', 'revolution',
    'rebellion', 'uprising', 'insurrection', 'mutiny', 'riot', 'disturbance',
    'disorder', 'chaos', 'anarchy', 'law', 'order', 'justice', 'right',
    'wrong', 'good', 'evil', 'virtue', 'vice', 'sin', 'crime', 'guilt',
    'innocence', 'punishment', 'penalty', 'fine', 'sentence', 'verdict',
    'judgment', 'decision', 'ruling', 'decree', 'command', 'order',
    'instruction', 'direction', 'guideline', 'rule', 'regulation', 'law',
    'statute', 'act', 'bill', 'code', 'constitution', 'charter', 'treaty',
    'agreement', 'contract', 'promise', 'oath', 'vow', 'pledge', 'guarantee',
    'warranty', 'assurance', 'insurance', 'protection', 'security', 'safety',
    'danger', 'risk', 'hazard', 'peril', 'threat', 'menace', 'challenge',
    'opportunity', 'chance', 'luck', 'fortune', 'fate', 'destiny', 'doom',
    'lot', 'portion', 'share', 'part', 'piece', 'bit', 'fragment',
    'scrap', 'crumb', 'grain', 'speck', 'dot', 'point', 'mark',
    'sign', 'symbol', 'token', 'emblem', 'badge', 'label', 'tag',
    'ticket', 'pass', 'card', 'paper', 'document', 'record', 'file',
    'folder', 'book', 'volume', 'issue', 'copy', 'edition', 'version',
    'draft', 'sketch', 'outline', 'summary', 'abstract', 'digest', 'review',
    'critique', 'analysis', 'commentary', 'explanation', 'interpretation', 'translation'
}

def clean_text(text):
    if not text: return ""
    # Remove leader dots ......
    text = re.sub(r'\.{2,}', ' ', text) 
    # Remove page numbers at end of line
    text = re.sub(r'\s+\d+\s*$', '', text, flags=re.MULTILINE)
    # Remove sequences of digits that look like page numbers
    text = re.sub(r'\b\d+\b', '', text)
    # Remove Roman numerals often found in TOCs (simple heuristic: small roman numerals)
    text = re.sub(r'\b[ivxlcdm]+\b', '', text)
    # Remove non-alphanumeric (keep spaces and hyphens)
    text = re.sub(r'[^a-zA-Z\s\-]', ' ', text)
    # Collapse whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def is_technical_token(token, pos_tags_map):
    """
    Heuristics to determine if a token is likely a technical term.
    """
    words = token.split()
    
    # 1. Length check
    if len(token) < 3 or len(token) > 40:
        return False
        
    # 2. Malformed / Hyphenation check
    # Avoid "double--hyphen" or "hyphen-at-end-" or "-hyphen-at-start"
    if '--' in token or token.startswith('-') or token.endswith('-'):
        return False
    
    # 3. Stopword / Common word check (expanded)
    # We check if *all* words in the token are stopwords (bad)
    # or if the token *is* a stopword.
    # For multi-word tokens, we want at least one significant word.

    # 4. Check if token is just stopwords/numbers
    if all(w in COMMON_ACADEMIC_TERMS or w in stopwords.words('english') or w.isdigit() for w in words):
        return False
        
    # 5. POS Tagging check
    # We want tokens that contain Nouns (NN, NNS, NNP, NNPS) or Adjectives (JJ)
    # And specifically, a valid technical term usually ends in a noun.
    
    # Get tags for this token's words
    tags = pos_tag(words)
    
    # Must contain at least one Noun or Adjective
    has_content = False
    for _, tag in tags:
        if tag.startswith('NN') or tag.startswith('JJ') or tag == 'VBG': # VBG like 'Processing' can be technical
            has_content = True
            
    if not has_content:
        return False
        
    # Check if it ends with a preposition or determiner or conjunction
    last_tag = tags[-1][1]
    if last_tag in ['IN', 'DT', 'CC', 'TO', 'PRP', 'PRP$']:
        return False
        
    # Check if it starts with a bad tag for a term (like 'and', 'or')
    first_word = words[0]
    if first_word in ['and', 'or', 'the', 'a', 'an', 'in', 'on', 'at', 'to', 'for', 'by', 'with']:
        return False

    return True

def extract_tokens_from_toc(pdf_path):
    sys.stderr.write(f"Processing: {pdf_path}\\n")
    tokens = []
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            toc_text = ""
            
            # Strategy 1: Digital Outline (Bookmarks)
            if hasattr(pdf, 'outline') and pdf.outline:
                sys.stderr.write("  Found digital outline (bookmarks).\\n")
                for item in pdf.outline:
                    if isinstance(item, dict):
                        toc_text += item.get('title', '') + " "
            
            # Strategy 2: Visual scan if outline is empty
            if not toc_text.strip():
                sys.stderr.write("  No digital outline. Scanning pages for 'Contents'...\\n")
                found_toc = False
                start_page = -1
                
                # Scan first 20 pages
                limit = min(len(pdf.pages), 20)
                for i in range(limit):
                    page_text = pdf.pages[i].extract_text(x_tolerance=1)
                    if not page_text: continue
                    
                    lines = page_text.lower().split('\\n')
                    header_found = False
                    for line in lines[:5]:
                        if "contents" in line or "table of contents" in line:
                            if len(line.split()) < 10:
                                header_found = True
                                break
                    
                    if header_found:
                        sys.stderr.write(f"  Found visual Table of Contents on page {i+1}\\n")
                        start_page = i
                        found_toc = True
                        break
                
                if found_toc:
                    pages_to_scan = 4 
                    for j in range(pages_to_scan):
                        p_idx = start_page + j
                        if p_idx >= len(pdf.pages): break
                        
                        p_text = pdf.pages[p_idx].extract_text(x_tolerance=1)
                        if p_text:
                            toc_text += p_text + "\\n"
            
            if not toc_text.strip():
                sys.stderr.write("  No Table of Contents found.\\n")
                return []

            # Process Text
            clean_toc = clean_text(toc_text)
            
            # Initial Tokenization
            words = word_tokenize(clean_toc.lower())
            
            # Generate candidates
            candidates = set()
            
            # Monograms
            candidates.update(words)
            
            # Bigrams
            bi = list(ngrams(words, 2))
            candidates.update([" ".join(g) for g in bi])
            
            # Trigrams
            tri = list(ngrams(words, 3))
            candidates.update([" ".join(g) for g in tri])
            
            # Filter candidates
            final_tokens = []
            for token in candidates:
                if is_technical_token(token, {}):
                    final_tokens.append(token)
            
            return sorted(final_tokens)

    except Exception as e:
        sys.stderr.write(f"  Error reading PDF: {e}\\n")
        return []

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 extract_toc_tokens.py <pdf_file>")
        sys.exit(1)
        
    result = extract_tokens_from_toc(sys.argv[1])
    if result:
        print(f"\\nExtracted {len(result)} unique tokens.")
        print("-" * 40)
        print(", ".join(result))
        print("-" * 40)
    else:
        print("\\nNo tokens extracted.")