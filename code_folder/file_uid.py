import hashlib

def get_file_hash(path, algo='md5', block_size=65536):
    hasher = hashlib.new(algo)
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(block_size), b''):
            hasher.update(chunk)
    return hasher.hexdigest()