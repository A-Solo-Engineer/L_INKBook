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
from backend.database import get_all_entries


def _extract_text_content(content_dict):
    """
    Extracts and combines all text fields from the content dictionary.

    Helper function to gather all free-form text fields for hashing.
    Matches the extraction logic used in entry.py to ensure consistent
    hash calculations during verification.

    Args:
        content_dict (dict): Dictionary containing content fields.

    Returns:
        str: Combined text from all text fields.
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

    Helper function to retrieve image data for hashing. Matches the extraction
    logic used in entry.py to ensure consistent hash calculations.

    Args:
        content_dict (dict): Dictionary containing content fields.

    Returns:
        bytes or None: Image data as bytes, or None if no image exists.
    """
    image_data = content_dict.get('image', None)

    if image_data is None:
        return None

    if isinstance(image_data, str):
        try:
            return base64.b64decode(image_data)
        except Exception:
            return None

    if isinstance(image_data, bytes):
        return image_data

    return None


def _extract_table_data(content_dict):
    """
    Extracts table data from the content dictionary.

    Helper function to retrieve table data for hashing. Matches the extraction
    logic used in entry.py to ensure consistent hash calculations.

    Args:
        content_dict (dict): Dictionary containing content fields.

    Returns:
        str or None: Table data as string, or None if no table exists.
    """
    table_data = content_dict.get('table', None)

    if table_data is None:
        return None

    if isinstance(table_data, (dict, list)):
        return json.dumps(table_data)

    if isinstance(table_data, str):
        return table_data

    return None


def _recalculate_entry_hash(entry_dict):
    """
    Recalculates the entry hash from raw entry data.

    This helper function recomputes the complete cryptographic hash of an entry
    following the exact same process used during entry creation in entry.py:
    1. Hash text, image, and table content
    2. Combine into Merkle root hash
    3. Combine with prev_hash and metadata into final entry hash

    Args:
        entry_dict (dict): Entry dictionary with all fields.

    Returns:
        str: The recalculated entry_hash.
    """
    content_dict = entry_dict.get('content', {})

    # Extract and hash text fields
    text_content = _extract_text_content(content_dict)
    text_hash = hash_text(text_content)

    # Extract and hash image data or use default
    image_data = _extract_image_data(content_dict)
    if image_data is not None:
        image_hash = hash_bytes(image_data)
    else:
        image_hash = hash_text("no_images")

    # Extract and hash table data or use default
    table_data = _extract_table_data(content_dict)
    if table_data is not None:
        table_hash = hash_table(table_data)
    else:
        table_hash = hash_text("no_tables")

    # Combine into Merkle root hash
    merkle_hash = create_merkle_hash(text_hash, image_hash, table_hash)

    # Reconstruct metadata string in same format as entry creation
    metadata_str = f"{entry_dict['date']}|{entry_dict['logged_by']}|{entry_dict['status']}"

    # Combine with previous hash and metadata into final entry hash
    recalculated_hash = create_entry_hash(merkle_hash, entry_dict['prev_hash'], metadata_str)

    return recalculated_hash


def verify_entry(entry_dict):
    """
    Verifies the integrity of a single entry.

    This function recalculates the entry hash from all content, metadata, and
    the previous hash. If the recalculated hash matches the stored hash, the
    entry is intact. If it differs, the entry has been tampered with.

    Args:
        entry_dict (dict): Entry dictionary retrieved from database.

    Returns:
        bool: True if entry is intact and unmodified, False if tampered.
    """
    # Recalculate the entry hash from current content
    recalculated_hash = _recalculate_entry_hash(entry_dict)

    # Compare to stored hash
    stored_hash = entry_dict.get('entry_hash', '')

    return recalculated_hash == stored_hash


def verify_chain(db_path):
    """
    Verifies the integrity of the entire entry chain.

    This function performs a comprehensive chain verification:
    1. Retrieves all entries from the database
    2. Verifies each entry individually
    3. Verifies the chain links (each entry's prev_hash matches previous entry's entry_hash)
    4. Checks first entry has genesis hash as prev_hash

    Returns a detailed report of any tampering or broken links found.

    Args:
        db_path (str): Path to the SQLite database.

    Returns:
        dict: Verification report containing:
            - valid (bool): True if entire chain is intact
            - tampered_entries (list): Entry numbers with modified content
            - broken_links (list): Entry numbers with broken chain links
            - total_entries (int): Total entries verified
            - message (str): Human-readable summary
    """
    try:
        # Retrieve all entries in chain order
        entries = get_all_entries(db_path)

        if not entries:
            return {
                'valid': True,
                'tampered_entries': [],
                'broken_links': [],
                'total_entries': 0,
                'message': 'Database is empty — no entries to verify.'
            }

        tampered = []
        broken_links = []

        # Verify each entry
        for entry in entries:
            entry_num = entry['entry_number']

            # Check if entry content has been modified
            if not verify_entry(entry):
                tampered.append(entry_num)

            # Verify chain link integrity
            if entry_num == 1:
                # First entry should have genesis hash as prev_hash
                if entry['prev_hash'] != GENESIS_HASH:
                    broken_links.append(entry_num)
            else:
                # Other entries should link to previous entry's hash
                prev_entry = entries[entry_num - 2]  # entry_number is 1-indexed
                if entry['prev_hash'] != prev_entry['entry_hash']:
                    broken_links.append(entry_num)

        # Determine overall validity
        is_valid = len(tampered) == 0 and len(broken_links) == 0

        # Build human-readable message
        if is_valid:
            message = f"Chain is VALID. All {len(entries)} entries are intact and properly linked."
        else:
            issues = []
            if tampered:
                issues.append(f"{len(tampered)} entry(ies) tampered: {tampered}")
            if broken_links:
                issues.append(f"{len(broken_links)} broken link(s): {broken_links}")
            message = "Chain is COMPROMISED. " + " | ".join(issues)

        return {
            'valid': is_valid,
            'tampered_entries': tampered,
            'broken_links': broken_links,
            'total_entries': len(entries),
            'message': message
        }

    except Exception as e:
        return {
            'valid': False,
            'tampered_entries': [],
            'broken_links': [],
            'total_entries': 0,
            'message': f'Verification failed with error: {str(e)}'
        }


def find_tampered_entry(db_path):
    """
    Finds the first tampered entry in the chain.

    This function walks through the chain from oldest to newest entry and
    returns the entry_number of the first entry that has been tampered with.
    Useful for pinpointing where integrity was compromised.

    Args:
        db_path (str): Path to the SQLite database.

    Returns:
        int or None: The entry_number of the first tampered entry, or None if
                     the entire chain is intact.
    """
    try:
        entries = get_all_entries(db_path)

        # Walk through entries in order
        for entry in entries:
            if not verify_entry(entry):
                # Found first tampered entry
                return entry['entry_number']

        # No tampered entries found
        return None

    except Exception as e:
        # Return None on error to indicate verification couldn't complete
        return None


def get_chain_status(db_path):
    """
    Returns the current chain integrity status as a simple string.

    This is a convenience function for quick status checks. Use verify_chain()
    for detailed information about what's wrong.

    Args:
        db_path (str): Path to the SQLite database.

    Returns:
        str: One of:
            - "VALID" — Chain is intact and unmodified
            - "TAMPERED" — Chain has been compromised (content modified or links broken)
            - "EMPTY" — Database has no entries
    """
    try:
        entries = get_all_entries(db_path)

        # Check if database is empty
        if not entries:
            return "EMPTY"

        # Run full verification
        result = verify_chain(db_path)

        # Return status based on result
        if result['valid']:
            return "VALID"
        else:
            return "TAMPERED"

    except Exception as e:
        # Return TAMPERED for any unexpected errors
        return "TAMPERED"
