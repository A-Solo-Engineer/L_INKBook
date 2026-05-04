import json
import sys
from pathlib import Path

from backend.database import initialize_db
from backend.verify import get_chain_status
from config import APP_NAME, VERSION, DB_PATH


# Path to the user config stored in the project root
USER_FILE = Path(__file__).parent / "user.json"

# Path to the lockdown counter file stored in the project root
LOCKDOWN_FILE = Path(__file__).parent / "lockdown.json"


def is_first_launch():
    """
    Determines whether this is the first launch of the application.

    Returns True when the user configuration file does not exist.
    """
    return not USER_FILE.exists()


def get_username():
    """
    Reads the username from user.json.

    Returns the stored username if the file exists and is valid. If the file
    cannot be read or parsed, returns an empty string.
    """
    try:
        with USER_FILE.open("r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("username", "")
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return ""


def save_username(username):
    """
    Saves the entered username to user.json.

    This function writes a small JSON file containing the username in the
    project root so the application remembers the user across launches.
    """
    try:
        with USER_FILE.open("w", encoding="utf-8") as f:
            json.dump({"username": username}, f, indent=2)
    except OSError as e:
        print(f"Error saving user information: {e}")


def handle_tampered_chain():
    """
    Manages the lockdown counter when a tampered chain is detected.

    Reads or creates lockdown.json, increments the counter, persists it,
    and returns the new counter value.
    """
    counter = 0

    if LOCKDOWN_FILE.exists():
        try:
            with LOCKDOWN_FILE.open("r", encoding="utf-8") as f:
                data = json.load(f)
                counter = int(data.get("counter", 0))
        except (json.JSONDecodeError, ValueError, OSError):
            counter = 0

    counter += 1

    try:
        with LOCKDOWN_FILE.open("w", encoding="utf-8") as f:
            json.dump({"counter": counter}, f, indent=2)
    except OSError as e:
        print(f"Error saving lockdown state: {e}")

    return counter


def prompt_for_username():
    """
    Prompts the user to enter their name on first launch.

    Keeps asking until a non-empty name is entered.
    """
    while True:
        try:
            name = input("Enter your name: ").strip()
        except EOFError:
            name = ""

        if name:
            return name
        print("Name cannot be empty. Please enter a valid name.")


def main():
    # Load application configuration
    print(f"Starting {APP_NAME}...")

    # On first launch, ask the user for their name and save it
    if is_first_launch():
        print("Welcome to L_INKBook! It looks like this is your first launch.")
        username = prompt_for_username()
        save_username(username)
        print(f"Welcome to L_INKBook, {username}!")
    else:
        username = get_username()

    # Initialize the SQLite database used for entries
    try:
        initialize_db(DB_PATH)
        print(f"Database initialized at {DB_PATH}")
    except Exception as e:
        print(f"Database initialization failed: {e}")
        sys.exit(1)

    # Verify the integrity of the entry chain before startup completes
    try:
        status = get_chain_status(DB_PATH)
    except Exception as e:
        print(f"Chain verification failed: {e}")
        sys.exit(1)

    if status == "EMPTY":
        print("Chain status: EMPTY — Ready for first entry.")
    elif status == "VALID":
        print("Chain status: VALID — All entries intact.")
    elif status == "TAMPERED":
        counter = handle_tampered_chain()
        if counter >= 10:
            print("LOCKDOWN: Too many attempts. Application locked.")
            sys.exit(1)
        print(f"Chain status: TAMPERED — Integrity compromised.")
        print(f"Warning: {counter}/10 attempts before lockdown.")
        sys.exit(1)
    else:
        print(f"Chain status: {status}")

    # Final startup confirmation
    print(f"L_INKBook {VERSION} started successfully.")
    print(f"Logged in as: {username}")
    print("Ready.")


if __name__ == "__main__":
    main()
