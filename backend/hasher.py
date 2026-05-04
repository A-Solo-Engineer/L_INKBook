import hashlib

def hash_text(text):
    """
    Hashes a given text string using SHA-256.

    This function takes a string input, encodes it to bytes using UTF-8,
    and computes the SHA-256 hash. The result is returned as a hexadecimal
    string. This is used for hashing text content in logbook entries to
    ensure integrity and detect any tampering.

    Args:
        text (str): The text string to hash.

    Returns:
        str: The SHA-256 hash as a hexadecimal string.
    """
    return hashlib.sha256(text.encode('utf-8')).hexdigest()

def hash_bytes(data):
    """
    Hashes given bytes data using SHA-256.

    This function takes bytes data directly and computes the SHA-256 hash.
    The result is returned as a hexadecimal string. This is useful for
    hashing binary data like images or other non-text content.

    Args:
        data (bytes): The bytes data to hash.

    Returns:
        str: The SHA-256 hash as a hexadecimal string.
    """
    return hashlib.sha256(data).hexdigest()

def hash_table(table_data):
    """
    Hashes table data represented as a string using SHA-256.

    This function takes table data as a string (e.g., CSV or serialized
    format) and computes the SHA-256 hash. The result is returned as a
    hexadecimal string. This ensures that tabular data in entries is
    cryptographically secured against modifications.

    Args:
        table_data (str): The table data as a string to hash.

    Returns:
        str: The SHA-256 hash as a hexadecimal string.
    """
    return hashlib.sha256(table_data.encode('utf-8')).hexdigest()

def create_merkle_hash(text_hash, image_hash, table_hash):
    """
    Creates a Merkle root hash by combining three hashes using SHA-256.

    This function takes three individual hashes (for text, image, and table
    components of an entry) and combines them into a single Merkle root hash.
    It does this by concatenating the hashes and hashing the result again.
    This creates a tamper-proof summary of all entry components, where any
    change in any component will alter the root hash.

    Args:
        text_hash (str): The SHA-256 hash of the text content.
        image_hash (str): The SHA-256 hash of the image content.
        table_hash (str): The SHA-256 hash of the table content.

    Returns:
        str: The Merkle root hash as a hexadecimal string.
    """
    combined = text_hash + image_hash + table_hash
    return hashlib.sha256(combined.encode('utf-8')).hexdigest()

def create_entry_hash(merkle_hash, prev_hash, metadata):
    """
    Creates the final entry hash by combining the Merkle hash, previous entry hash, and metadata.

    This function takes the Merkle root hash of the current entry's components,
    the hash of the previous entry (to create a chain), and metadata (e.g., timestamp,
    author). It concatenates these and hashes them to produce the final entry hash.
    This ensures the immutability of the logbook chain, as any tampering with an
    entry or its predecessors will break the hash chain.

    Args:
        merkle_hash (str): The Merkle root hash of the entry's components.
        prev_hash (str): The hash of the previous entry in the chain.
        metadata (str): Additional metadata as a string.

    Returns:
        str: The final entry hash as a hexadecimal string.
    """
    combined = merkle_hash + prev_hash + metadata
    return hashlib.sha256(combined.encode('utf-8')).hexdigest()