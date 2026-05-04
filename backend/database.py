import sqlite3
import json


def initialize_db(db_path):
    """
    Creates the SQLite database and the entries table if they don't exist.

    This function checks if the database file exists. If not, it creates a new one
    and initializes the entries table with all required columns. The entries table
    stores all logbook entries with their cryptographic hashes, metadata, and
    free-form content stored as JSON.

    Args:
        db_path (str): The file path where the SQLite database should be created or accessed.

    Returns:
        None

    Raises:
        sqlite3.Error: If there's an issue creating the database or table.
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Create the entries table with all required columns
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS entries (
                entry_number INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                project_name TEXT NOT NULL,
                logged_by TEXT NOT NULL,
                status TEXT NOT NULL,
                prev_hash TEXT,
                entry_hash TEXT NOT NULL UNIQUE,
                content TEXT NOT NULL
            )
        ''')

        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        raise sqlite3.Error(f"Database initialization failed: {e}")


def save_entry(db_path, entry_dict):
    """
    Saves a complete entry dictionary to the database.

    This function takes an entry dictionary containing all required fields and
    inserts it into the entries table. The content field (which contains multiple
    free-form fields like problem, idea, objectives, etc.) is stored as a JSON blob.
    This ensures data integrity and makes it easy to retrieve and manipulate complex
    entry data.

    Args:
        db_path (str): The file path to the SQLite database.
        entry_dict (dict): A dictionary containing the entry data with keys:
            - date: Timestamp of entry creation
            - project_name: Name of the project
            - logged_by: Author name
            - status: One of 'Idea', 'In Progress', 'Completed'
            - prev_hash: Hash of previous entry (can be empty string for first entry)
            - entry_hash: The final immutable hash of this entry
            - content: A dictionary containing free-form fields

    Returns:
        int: The entry_number (primary key) of the newly inserted entry.

    Raises:
        sqlite3.Error: If the insert operation fails (e.g., duplicate entry_hash).
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Convert content dictionary to JSON string for storage
        content_json = json.dumps(entry_dict.get('content', {}))

        cursor.execute('''
            INSERT INTO entries (date, project_name, logged_by, status, prev_hash, entry_hash, content)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            entry_dict['date'],
            entry_dict['project_name'],
            entry_dict['logged_by'],
            entry_dict['status'],
            entry_dict.get('prev_hash', ''),
            entry_dict['entry_hash'],
            content_json
        ))

        entry_number = cursor.lastrowid
        conn.commit()
        conn.close()

        return entry_number
    except sqlite3.Error as e:
        raise sqlite3.Error(f"Failed to save entry: {e}")


def get_entry(db_path, entry_number):
    """
    Retrieves a single entry from the database by its entry number.

    This function queries the database for an entry with the specified entry_number
    and returns all its data. The content field is parsed back from JSON to a dictionary
    for easy access to individual free-form fields.

    Args:
        db_path (str): The file path to the SQLite database.
        entry_number (int): The primary key (entry_number) of the entry to retrieve.

    Returns:
        dict: A dictionary containing the entry data, or None if the entry doesn't exist.
              The content field is a dictionary.

    Raises:
        sqlite3.Error: If the query fails.
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM entries WHERE entry_number = ?', (entry_number,))
        row = cursor.fetchone()
        conn.close()

        if row is None:
            return None

        # Convert row to dictionary and parse JSON content
        entry_dict = {
            'entry_number': row[0],
            'date': row[1],
            'project_name': row[2],
            'logged_by': row[3],
            'status': row[4],
            'prev_hash': row[5],
            'entry_hash': row[6],
            'content': json.loads(row[7])
        }

        return entry_dict
    except sqlite3.Error as e:
        raise sqlite3.Error(f"Failed to retrieve entry: {e}")


def get_all_entries(db_path):
    """
    Retrieves all entries from the database in chain order (oldest to newest).

    This function queries all entries sorted by entry_number in ascending order,
    which represents the chronological chain of entries. Each entry's content
    field is parsed back from JSON to a dictionary.

    Args:
        db_path (str): The file path to the SQLite database.

    Returns:
        list: A list of dictionaries, each representing an entry. Returns an empty
              list if the database is empty. Each entry's content field is a dictionary.

    Raises:
        sqlite3.Error: If the query fails.
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM entries ORDER BY entry_number ASC')
        rows = cursor.fetchall()
        conn.close()

        entries = []
        for row in rows:
            entry_dict = {
                'entry_number': row[0],
                'date': row[1],
                'project_name': row[2],
                'logged_by': row[3],
                'status': row[4],
                'prev_hash': row[5],
                'entry_hash': row[6],
                'content': json.loads(row[7])
            }
            entries.append(entry_dict)

        return entries
    except sqlite3.Error as e:
        raise sqlite3.Error(f"Failed to retrieve all entries: {e}")


def get_last_entry(db_path):
    """
    Retrieves the most recent entry from the database.

    This function queries the entry with the highest entry_number, which is the
    most recently added entry. This is essential for obtaining the prev_hash value
    needed when creating the next entry in the chain. Returns None if the database
    is empty (no entries exist yet).

    Args:
        db_path (str): The file path to the SQLite database.

    Returns:
        dict: A dictionary containing the most recent entry data, or None if no
              entries exist. The content field is a dictionary.

    Raises:
        sqlite3.Error: If the query fails.
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM entries ORDER BY entry_number DESC LIMIT 1')
        row = cursor.fetchone()
        conn.close()

        if row is None:
            return None

        # Convert row to dictionary and parse JSON content
        entry_dict = {
            'entry_number': row[0],
            'date': row[1],
            'project_name': row[2],
            'logged_by': row[3],
            'status': row[4],
            'prev_hash': row[5],
            'entry_hash': row[6],
            'content': json.loads(row[7])
        }

        return entry_dict
    except sqlite3.Error as e:
        raise sqlite3.Error(f"Failed to retrieve last entry: {e}")


def get_entries_by_project(db_path, project_name):
    """
    Retrieves all entries filtered by a specific project name.

    This function queries all entries that belong to a specific project, returning
    them in chronological order (oldest to newest by entry_number). This is useful
    for viewing all logbook entries related to a particular project. Each entry's
    content field is parsed back from JSON to a dictionary.

    Args:
        db_path (str): The file path to the SQLite database.
        project_name (str): The name of the project to filter by.

    Returns:
        list: A list of dictionaries, each representing an entry belonging to the
              specified project. Returns an empty list if no entries match the project.
              Each entry's content field is a dictionary.

    Raises:
        sqlite3.Error: If the query fails.
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute(
            'SELECT * FROM entries WHERE project_name = ? ORDER BY entry_number ASC',
            (project_name,)
        )
        rows = cursor.fetchall()
        conn.close()

        entries = []
        for row in rows:
            entry_dict = {
                'entry_number': row[0],
                'date': row[1],
                'project_name': row[2],
                'logged_by': row[3],
                'status': row[4],
                'prev_hash': row[5],
                'entry_hash': row[6],
                'content': json.loads(row[7])
            }
            entries.append(entry_dict)

        return entries
    except sqlite3.Error as e:
        raise sqlite3.Error(f"Failed to retrieve entries by project: {e}")
