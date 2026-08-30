import sqlite3

DB_NAME = "quicksplit.db"


def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Table for Group Participants
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS participants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        )
    """
    )

    # Table for Expenses
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            description TEXT NOT NULL,
            amount REAL NOT NULL,
            payer TEXT NOT NULL,
            split_among TEXT NOT NULL,
            split_amount REAL NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """
    )

    # Seed default participants if empty
    cursor.execute("SELECT COUNT(*) FROM participants")
    if cursor.fetchone()[0] == 0:
        default_names = ["Alice", "Bob", "Charlie", "David"]
        cursor.executemany(
            "INSERT INTO participants (name) VALUES (?)",
            [(name,) for name in default_names],
        )

    conn.commit()
    conn.close()


def get_participants():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM participants")
    rows = cursor.fetchall()
    conn.close()
    return [row[0] for row in rows]


def add_participant_db(name: str):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO participants (name) VALUES (?)", (name,))
    conn.commit()
    conn.close()


def remove_participant_db(name: str):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM participants WHERE name = ?", (name,))
    conn.commit()
    conn.close()


def save_expense_db(
    description, amount, payer, split_among_str, split_amount, timestamp
):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO expenses (description, amount, payer, split_among, split_amount, timestamp)
        VALUES (?, ?, ?, ?, ?, ?)
    """,
        (description, amount, payer, split_among_str, split_amount, timestamp),
    )
    conn.commit()
    conn.close()


def load_expenses_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, description, amount, payer, split_among, split_amount, timestamp FROM expenses ORDER BY id DESC"
    )
    rows = cursor.fetchall()
    conn.close()

    expenses = []
    for row in rows:
        expenses.append(
            {
                "id": row[0],
                "description": row[1],
                "amount": row[2],
                "payer": row[3],
                "split_among": row[4].split(", "),
                "split_amount": row[5],
                "timestamp": row[6],
            }
        )
    return expenses
