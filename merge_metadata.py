import os
import json
import sys

def merge_json_files(directory, output_file):
    all_metadata = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".json"):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                        all_metadata.append(data)
                except Exception as e:
                    print(f"Error reading {file_path}: {e}")

    with open(output_file, 'w') as f:
        json.dump(all_metadata, f, indent=2)
    print(f"Merged {len(all_metadata)} items into {output_file}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 merge_metadata.py <cache_directory> <output_file>")
        sys.exit(1)
    
    merge_json_files(sys.argv[1], sys.argv[2])
