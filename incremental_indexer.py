import os
import json
import hashlib
import subprocess
import sys
import concurrent.futures
import argparse

CACHE_DIR = ".metadata_cache"
DB_FILE = "library.json"
EXTS = {".pdf", ".djvu", ".epub", ".mobi"}
INDEXING_TIMEOUT = 900  # 15 minutes in seconds

def get_file_hash(filepath):
    try:
        hasher = hashlib.md5()
        with open(filepath, 'rb') as f:
            buf = f.read(8192)
            hasher.update(buf)
        return hasher.hexdigest()
    except:
        return None

def index_single_file(task_tuple):
    filepath, full_mode = task_tuple
    filepath = os.path.relpath(filepath)
    print(f"Indexing {filepath} ...")
    
    file_hash = get_file_hash(filepath)
    if not file_hash: return False

    cache_key = hashlib.md5(filepath.encode()).hexdigest()
    cache_path = os.path.join(CACHE_DIR, f"{cache_key}.json")
    
    try:
        env = os.environ.copy()
        if not full_mode:
            env["SKIP_WIKI"] = "1"
            
        result = subprocess.run(
            ["python3", "library_indexer.py", filepath],
            capture_output=True, text=True, check=True, env=env,
            timeout=INDEXING_TIMEOUT
        )
        meta = json.loads(result.stdout)
        meta["_hash"] = file_hash
        meta["_path"] = filepath 
        
        with open(cache_path, 'w') as f:
            json.dump(meta, f, indent=2)
        return True
    except subprocess.TimeoutExpired:
        print(f"  WARNING: Indexing timed out for {filepath} after {INDEXING_TIMEOUT/60} minutes. Skipping.")
        return {"path": filepath, "error": "TimeoutExpired"}
    except Exception as e:
        print(f"  Failed to index {filepath}: {e}")
        return {"path": filepath, "error": str(e)}

def run_indexer(dry_run=False, full_mode=False, cores=1):
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)

    skipped_count = 0
    to_index = []

    print("Scanning directory for files...")
    for root, dirs, files in os.walk("."):
        if "/." in root or CACHE_DIR in root:
            continue
            
        for file in files:
            ext = os.path.splitext(file)[1].lower()
            if ext in EXTS:
                filepath = os.path.relpath(os.path.join(root, file))
                # Use path + hash for cache key
                file_hash = get_file_hash(filepath)
                if not file_hash: continue
                
                cache_key = hashlib.md5(filepath.encode()).hexdigest()
                cache_path = os.path.join(CACHE_DIR, f"{cache_key}.json")
                
                # Check if we need to re-index
                needs_indexing = True
                if os.path.exists(cache_path):
                    with open(cache_path, 'r') as f:
                        try:
                            cached_data = json.load(f)
                            if cached_data.get("_hash") == file_hash:
                                needs_indexing = False
                        except:
                            pass
                
                if needs_indexing:
                    to_index.append(filepath)
                else:
                    skipped_count += 1

    if dry_run:
        if to_index:
            print("Files remaining to be indexed:")
            for path in to_index:
                print(f"  {path}")
            print(f"\nTotal to index: {len(to_index)}")
        else:
            print("All files are up to date.")
        return

    print(f"Found {len(to_index)} files to index. Using {cores} core(s).")
    
    indexed_count = 0
    failures = []

    # Prepare tasks (filepath, full_mode)
    tasks = [(fp, full_mode) for fp in to_index]

    if cores > 1:
        with concurrent.futures.ThreadPoolExecutor(max_workers=cores) as executor:
            results = list(executor.map(index_single_file, tasks))
    else:
        results = [index_single_file(t) for t in tasks]

    for res in results:
        if res is True:
            indexed_count += 1
        elif isinstance(res, dict):
            failures.append(res)

    if failures:
        with open("indexing_failures.json", "w") as f:
            json.dump(failures, f, indent=2)
        print(f"Errors encountered. See indexing_failures.json for details ({len(failures)} failed).")
    else:
        if os.path.exists("indexing_failures.json"):
            os.remove("indexing_failures.json")

    print(f"Finished indexing. {indexed_count} new/updated, {skipped_count} skipped.")
    
    # Merge
    print("Merging metadata...")
    all_meta = []
    for cache_file in os.listdir(CACHE_DIR):
        if cache_file.endswith(".json"):
            with open(os.path.join(CACHE_DIR, cache_file), 'r') as f:
                try:
                    all_meta.append(json.load(f))
                except:
                    pass
    
    with open(DB_FILE, 'w') as f:
        json.dump(all_meta, f, indent=2)
    print(f"Database updated: {DB_FILE}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Incremental Library Indexer")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be indexed without doing it")
    parser.add_argument("--full", action="store_true", help="Enable full mode (e.g. Wikipedia expansion)")
    parser.add_argument("--cores", type=int, default=1, help="Number of parallel cores/threads to use")
    
    args = parser.parse_args()
    
    run_indexer(dry_run=args.dry_run, full_mode=args.full, cores=args.cores)