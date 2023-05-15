import os
import json
import hashlib
import argparse
from collections import defaultdict
from pathlib import Path

def calculate_hash(file_path, hash_algo):
    BUF_SIZE = 65536  # let's read stuff in 64kb chunks!

    hash_func = getattr(hashlib, hash_algo)
    hash_obj = hash_func()

    with open(file_path, 'rb') as f:
        while True:
            data = f.read(BUF_SIZE)
            if not data:
                break
            hash_obj.update(data)

    return hash_obj.hexdigest()


def save_results(dir_path, results):
    results_path = os.path.join(dir_path, 'results.json')
    with open(results_path, 'w') as f:
        json.dump(results, f)


def load_results(dir_path):
    results_path = os.path.join(dir_path, 'results.json')
    if os.path.exists(results_path):
        with open(results_path, 'r') as f:
            return json.load(f)
    else:
        return {}


def find_duplicates(dirs_path, hash_algo):
    total_files = 0
    hashed_files = 0
    hashes_full = defaultdict(list)

    for dir_path in dirs_path:
        print(f"Processing directory: {dir_path}")
        results = load_results(dir_path)
        for foldername, subfolders, filenames in os.walk(dir_path):
            for filename in filenames:
                file_path = os.path.join(foldername, filename)
                total_files += 1

                if file_path in results and os.path.getmtime(file_path) == results[file_path]['mtime']:
                    hashed_files += 1
                    print(f"Processing file {hashed_files}/{total_files} (cached)")
                    file_hash = results[file_path]['hash']
                else:
                    try:
                        file_hash = calculate_hash(file_path, hash_algo)
                        hashed_files += 1
                        print(f"Processing file {hashed_files}/{total_files}")
                        results[file_path] = {
                            'hash': file_hash,
                            'mtime': os.path.getmtime(file_path)
                        }
                    except (OSError,):
                        # the file access might've changed till the exec point got here
                        continue

                duplicate = hashes_full.get(file_hash)
                if duplicate:
                    print(f"Duplicate found: {file_path} and {duplicate}")
                    os.remove(file_path)  # remove the duplicate file
                else:
                    hashes_full[file_hash] = file_path

        save_results(dir_path, results)


def main():
    parser = argparse.ArgumentParser(description='Find duplicate files')
    parser.add_argument('-c', '--config', help='Path to configuration file', default='./config.json')
    args = parser.parse_args()

    config_path = Path(args.config)
    if not config_path.is_file():
        print(f"Configuration file not found: {config_path}")
        return

    with open(config_path, 'r') as f:
        config = json.load(f)

    dirs_path = config.get('dirs_path', [])
    hash_algo = config.get('hash_algo', 'md5')

    find_duplicates(dirs_path, hash_algo)


if __name__ == "__main__":
    main()
