# L_INKBook

A tamper-proof digital logbook where every entry is cryptographically locked using SHA-256 hashing and Merkle Trees. 
Once saved, entries cannot be silently edited. Any tampering breaks the cryptographic chain and becomes visible.

Built on the same core architecture as Bitcoin — but stripped down to one property.
---

## Status

🔧 Backend — Complete  
🚧 Frontend — In Development  
⬜ Tests — Pending  
⬜ Documentation — Pending  

---

## How It Works

Each entry is hashed using SHA-256. The hash of every entry includes 
the hash of the previous entry — forming an immutable chain. Tampering 
with any entry breaks every subsequent hash, making it immediately 
detectable.

Content hashing follows a Merkle Tree structure:
- Text, images, and tables are hashed separately
- Combined into a single Merkle root hash
- Chained with the previous entry's hash and metadata

---

## Tech Stack

- Python 3.13
- PyQt5
- SQLite
- SHA-256 Merkle Tree hashing
- Standard library only for backend

---

## Project Structure
L_INKBook/
│
├── backend/
│   ├── hasher.py       —  hashing engine
│   ├── database.py     — SQLite storage/retrieval
│   ├── entry.py        — Entry blueprint/creation
│   └── verify.py       — Chain tamper detection
│
├── frontend/           — In development
│
├── config.py           — Global configuration
├── main.py             — Application entry point
└── requirements.txt    — Dependencies

---

## Installation

```bash
git clone https://github.com/A-Solo-Engineer/L_INKBook.git
cd L_INKBook
pip install -r requirements.txt
python main.py
```

---

## Author

Aarav (A-Solo-Engineer)

---