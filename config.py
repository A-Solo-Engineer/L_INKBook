from pathlib import Path

# ============================================================================
# Application Metadata
# ============================================================================

# Application name displayed in UI and logs
APP_NAME = "L_INKBook"

# Version number following semantic versioning (major.minor.patch)
VERSION = "1.0.0"

# Author/creator of the application
AUTHOR = "Aarav"

# Brief description of the application's purpose and features
DESCRIPTION = "A tamper-proof digital logbook where every entry is cryptographically locked using SHA-256 hashing and Merkle Trees."

# ============================================================================
# Database Configuration
# ============================================================================

# Filename of the SQLite database
DB_NAME = "linkbook.db"

# Full path to the database file, constructed dynamically using pathlib.
# This ensures the path works correctly on any operating system (Windows, Linux, macOS).
# The database is stored in the project root directory.
DB_PATH = Path(__file__).parent / DB_NAME

# ============================================================================
# Cryptography
# ============================================================================

# Genesis hash used as the starting point of the hash chain.
# This is the prev_hash value for the very first entry when no previous entry exists.
# All zeros indicate the beginning of the chain.
GENESIS_HASH = "0000000000000000000000000000000000000000000000000000000000000000"

# ============================================================================
# Entry Status Options
# ============================================================================

# List of valid status values for logbook entries.
# Every entry must have one of these statuses to indicate its current state.
STATUS_OPTIONS = ["Idea", "In Progress", "Completed"]

# ============================================================================
# Logging Configuration
# ============================================================================

# Standard logging format for all application logs.
# Format: timestamp | log level | logger name | message
LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"

# ============================================================================
# Date and Time Format
# ============================================================================

# ISO 8601 format for all timestamps stored in the database and entries.
# Format: YYYY-MM-DDTHH:MM:SS
# This ensures consistent, machine-readable timestamps across all platforms.
DATE_FORMAT = "%Y-%m-%dT%H:%M:%S"
