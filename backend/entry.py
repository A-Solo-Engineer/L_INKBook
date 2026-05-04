from dataclasses import dataclass, field
from datetime import datetime
import json
import base64
from config import GENESIS_HASH

from backend.hasher import (
    hash_text,
    hash_bytes,
    hash_table,
    create_merkle_hash,
    create_entry_hash
)
from backend.database import get_last_entry


@dataclass
class Entry:
    """
    Represents a single tamper-proof entry in the L_INKBook logbook.

    Each entry contains both structured metadata (date, project, author, status)
    and free-form content (problem, ideas, observations, etc.). Every entry is
    cryptographically locked with SHA-256 hashing and linked to the previous
    entry via prev_hash, forming an immutable chain.

    Attributes:
        entry_number: Integer primary key, auto-incremented by database.
        date: ISO format timestamp of when the entry was created.
        project_name: Name of the project this entry belongs to.
        logged_by: Author/person who created this entry.
        status: Current status - one of "Idea", "In Progress", or "Completed".
        prev_hash: SHA-256 hash of the previous entry, linking entries in chain.
        entry_hash: Final immutable SHA-256 hash of this complete entry.
        content: Dictionary containing all free-form fields (problem, idea, etc.).
    """
    entry_number: int = None
    date: str = field(default_factory=lambda: datetime.now().isoformat())
    project_name: str = ""
    logged_by: str = ""
    status: str = ""
    prev_hash: str = ""
    entry_hash: str = ""
    content: dict = field(default_factory=dict)


def _extract_text_content(content_dict):
    """
    Extracts and combines all text fields from the content dictionary.

    This helper function collects all free-form text fields (problem, idea,
    file_structure, etc.) and concatenates them into a single string. This
    combined text is then hashed to create one component of the Merkle hash.

    Args:
        content_dict (dict): Dictionary containing content fields.

    Returns:
        str: Combined text from all text fields, or empty string if none exist.
    """
    text_fields = [
        'problem',
        'idea',
        'file_structure',
        'data_structure',
        'visual_representation',
        'objectives',
        'key_notes',
        'observations',
        'next_steps',
        'scribble'
    ]

    combined_text = ""
    for field_name in text_fields:
        value = content_dict.get(field_name, "")
        if isinstance(value, str):
            combined_text += value

    return combined_text


def _extract_image_data(content_dict):
    """
    Extracts image data from the content dictionary.

    This helper function retrieves any embedded image data (stored as bytes
    or base64 string). If no image exists, returns None so a default hash
    can be used instead.

    Args:
        content_dict (dict): Dictionary containing content fields.

    Returns:
        bytes or None: Image data as bytes, or None if no image exists.
    """
    image_data = content_dict.get('image', None)

    if image_data is None:
        return None

    # If image is stored as base64 string, convert to bytes
    if isinstance(image_data, str):
        try:
            return base64.b64decode(image_data)
        except Exception:
            return None

    # If already bytes, return as-is
    if isinstance(image_data, bytes):
        return image_data

    return None


def _extract_table_data(content_dict):
    """
    Extracts table data from the content dictionary.

    This helper function retrieves table data which might be stored as a
    string (CSV format) or other structured format. If no table exists,
    returns None so a default hash can be used instead.

    Args:
        content_dict (dict): Dictionary containing content fields.

    Returns:
        str or None: Table data as string, or None if no table exists.
    """
    table_data = content_dict.get('table', None)

    if table_data is None:
        return None

    # If table is a dict or list, convert to JSON string
    if isinstance(table_data, (dict, list)):
        return json.dumps(table_data)

    # If already a string, return as-is
    if isinstance(table_data, str):
        return table_data

    return None


def _create_hashes(content_dict, prev_hash, metadata_str):
    """
    Creates all hashes for an entry following the cryptographic chain process.

    This helper orchestrates the hashing pipeline:
    1. Extract and hash text content
    2. Extract and hash image data (or use default)
    3. Extract and hash table data (or use default)
    4. Combine all three into Merkle root hash
    5. Combine Merkle hash with previous hash and metadata into final entry hash

    Args:
        content_dict (dict): Dictionary containing entry content.
        prev_hash (str): Hash of previous entry in chain.
        metadata_str (str): Metadata string (date + author + status).

    Returns:
        tuple: (merkle_hash, entry_hash)
    """
    # Step 1: Hash text fields
    text_content = _extract_text_content(content_dict)
    text_hash = hash_text(text_content)

    # Step 2: Hash image data or default
    image_data = _extract_image_data(content_dict)
    if image_data is not None:
        image_hash = hash_bytes(image_data)
    else:
        image_hash = hash_text("no_images")

    # Step 3: Hash table data or default
    table_data = _extract_table_data(content_dict)
    if table_data is not None:
        table_hash = hash_table(table_data)
    else:
        table_hash = hash_text("no_tables")

    # Step 4: Create Merkle root hash
    merkle_hash = create_merkle_hash(text_hash, image_hash, table_hash)

    # Step 5: Create final entry hash
    entry_hash = create_entry_hash(merkle_hash, prev_hash, metadata_str)

    return merkle_hash, entry_hash


def create_entry(project_name, logged_by, status, content, db_path):
    """
    Creates a complete, cryptographically secured Entry for the logbook.

    This function is the main factory for creating new entries. It:
    1. Generates a timestamp
    2. Retrieves the previous entry's hash from the database
    3. Orchestrates the hashing process for all content
    4. Constructs and returns a complete Entry object with all fields

    The entry is not yet saved to the database — that happens separately
    when save_entry() is called from database.py.

    Args:
        project_name (str): Name of the project this entry belongs to.
        logged_by (str): Author/person creating this entry.
        status (str): One of "Idea", "In Progress", or "Completed".
        content (dict): Dictionary containing entry content fields.
        db_path (str): Path to the SQLite database for retrieving previous hash.

    Returns:
        Entry: A complete Entry object with all fields populated and hashes computed.

    Raises:
        sqlite3.Error: If database query fails.
    """
    # Generate current timestamp in ISO format
    timestamp = datetime.now().isoformat()

    # Retrieve previous entry or use genesis hash
    last_entry = get_last_entry(db_path)
    prev_hash = last_entry['entry_hash'] if last_entry else GENESIS_HASH

    # Create metadata string combining date, author, and status
    metadata_str = f"{timestamp}|{logged_by}|{status}"

    # Compute all hashes using the cryptographic chain process
    merkle_hash, entry_hash = _create_hashes(content, prev_hash, metadata_str)

    # Construct and return the complete Entry
    entry = Entry(
        entry_number=None,  # Will be auto-assigned by database
        date=timestamp,
        project_name=project_name,
        logged_by=logged_by,
        status=status,
        prev_hash=prev_hash,
        entry_hash=entry_hash,
        content=content
    )

    return entry


def entry_to_dict(entry):
    """
    Converts an Entry object to a dictionary for database storage.

    This function transforms an Entry dataclass instance into a plain dictionary
    that can be passed directly to database.py's save_entry() function. This
    abstraction keeps the Entry representation separate from how it's stored.

    Args:
        entry (Entry): The Entry object to convert.

    Returns:
        dict: Dictionary with keys matching the database schema and entry_dict
              parameter of save_entry().
    """
    return {
        'date': entry.date,
        'project_name': entry.project_name,
        'logged_by': entry.logged_by,
        'status': entry.status,
        'prev_hash': entry.prev_hash,
        'entry_hash': entry.entry_hash,
        'content': entry.content
    }
