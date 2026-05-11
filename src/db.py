import sqlite3
from datetime import datetime, timedelta

DB_FILE = "users.db"

def get_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

# create the users table if it doesnt exist yet
def init_db():
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id       TEXT PRIMARY KEY,
            username TEXT NOT NULL,
            password TEXT NOT NULL,
            profile_pic TEXT,
            color    TEXT,
            role     TEXT DEFAULT 'user'
        )
    """)
    c.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_username_id ON users(username, id)")
    conn.commit()
    conn.close()

def create_friends_table():
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS friends (
            user1 TEXT,
            user2 TEXT,
            status TEXT, -- pending, accepted, blocked
            PRIMARY KEY (user1, user2)
        )
    """)
    conn.commit()
    conn.close()

# Neue Tabellen für server-spezifische Moderation (Mute/Ban mit Zeit und Grund)
def create_server_moderation_tables():
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS server_banned_users (
            server_id INTEGER,
            username TEXT,
            until DATETIME,
            reason TEXT,
            PRIMARY KEY (server_id, username)
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS server_muted_users (
            server_id INTEGER,
            username TEXT,
            until DATETIME,
            reason TEXT,
            PRIMARY KEY (server_id, username)
        )
    """)
    conn.commit()
    conn.close()

# Freundesanfrage senden
def send_friend_request(user1, user2):
    # Status ist 'pending'
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT OR IGNORE INTO friends (user1, user2, status) VALUES (?, ?, 'pending')
    """, (user1, user2))
    conn.commit()
    conn.close()

# Freundesanfrage annehmen
def accept_friend_request(user1, user2):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        UPDATE friends SET status = 'accepted' WHERE user1 = ? AND user2 = ?
    """, (user1, user2))
    # Gegenseitige Freundschaft eintragen
    c.execute("""
        INSERT OR IGNORE INTO friends (user1, user2, status) VALUES (?, ?, 'accepted')
    """, (user2, user1))
    conn.commit()
    conn.close()

# Freundesanfrage ablehnen oder Freund entfernen
def remove_friend(user1, user2):
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM friends WHERE (user1 = ? AND user2 = ?) OR (user1 = ? AND user2 = ?)", (user1, user2, user2, user1))
    conn.commit()
    conn.close()

# Alle Freunde eines Users abrufen
def get_friends(username):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT user2 FROM friends WHERE user1 = ? AND status = 'accepted'
    """, (username,))
    friends = [row["user2"] for row in c.fetchall()]
    conn.close()
    return friends

# Offene Freundesanfragen abrufen
def get_pending_friend_requests(username):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT user1 FROM friends WHERE user2 = ? AND status = 'pending'
    """, (username,))
    requests = [row["user1"] for row in c.fetchall()]
    conn.close()
    return requests

# Server-spezifisch: User muten
def server_mute_user(server_id, username, minutes, reason):
    until = datetime.utcnow() + timedelta(minutes=minutes)
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT OR REPLACE INTO server_muted_users (server_id, username, until, reason)
        VALUES (?, ?, ?, ?)
    """, (server_id, username, until.isoformat(), reason))
    conn.commit()
    conn.close()

# Server-spezifisch: User entmuten
def server_unmute_user(server_id, username):
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM server_muted_users WHERE server_id = ? AND username = ?", (server_id, username))
    conn.commit()
    conn.close()

# Prüfen, ob User auf Server gemutet ist (und wie lange noch)
def is_server_muted(server_id, username):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT until, reason FROM server_muted_users WHERE server_id = ? AND username = ?
    """, (server_id, username))
    row = c.fetchone()
    conn.close()
    if row:
        until = datetime.fromisoformat(row["until"])
        if until > datetime.utcnow():
            return True, until, row["reason"]
    return False, None, None

# Server-spezifisch: User bannen
def server_ban_user(server_id, username, minutes, reason):
    until = datetime.utcnow() + timedelta(minutes=minutes)
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT OR REPLACE INTO server_banned_users (server_id, username, until, reason)
        VALUES (?, ?, ?, ?)
    """, (server_id, username, until.isoformat(), reason))
    conn.commit()
    conn.close()

# Server-spezifisch: User entbannen
def server_unban_user(server_id, username):
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM server_banned_users WHERE server_id = ? AND username = ?", (server_id, username))
    conn.commit()
    conn.close()

# Prüfen, ob User auf Server gebannt ist (und wie lange noch)
def is_server_banned(server_id, username):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT until, reason FROM server_banned_users WHERE server_id = ? AND username = ?
    """, (server_id, username))
    row = c.fetchone()
    conn.close()
    if row:
        until = datetime.fromisoformat(row["until"])
        if until > datetime.utcnow():
            return True, until, row["reason"]
    return False, None, None

def create_messages_table():
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            username  TEXT NOT NULL,
            message   TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


def create_moderation_tables():
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS banned_users (
            username TEXT PRIMARY KEY
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS muted_users (
            username TEXT PRIMARY KEY
        )
    """)
    conn.commit()
    conn.close()


def create_servers_table():
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS servers (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            name     TEXT UNIQUE NOT NULL COLLATE NOCASE,
            owner    TEXT NOT NULL,
            password TEXT
        )
    """)
    # each server has members with their own role inside that server
    c.execute("""
        CREATE TABLE IF NOT EXISTS server_members (
            server_id INTEGER,
            username  TEXT,
            role      TEXT DEFAULT 'user',
            PRIMARY KEY (server_id, username)
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS server_messages (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            server_id INTEGER,
            username  TEXT,
            message   TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


def create_private_messages_table():
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS private_messages (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            sender    TEXT NOT NULL,
            receiver  TEXT NOT NULL,
            message   TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


# user functions

def user_code_exists(username, code):
    conn = get_connection()
    c = conn.cursor()
    user_id = f"{username}#{code}"
    c.execute("SELECT 1 FROM users WHERE id = ?", (user_id,))
    exists = c.fetchone() is not None
    conn.close()
    return exists


def create_user(user_id, username, password, profile_pic=None, color="red", role="user"):
    try:
        conn = get_connection()
        c = conn.cursor()
        c.execute(
            "INSERT INTO users (id, username, password, profile_pic, color, role) VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, username, password, profile_pic, color, role),
        )
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False


def get_user_by_username(username):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username = ?", (username,))
    row = c.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None


def get_username_by_id(user_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT username FROM users WHERE id = ?", (user_id,))
    row = c.fetchone()
    conn.close()
    return row["username"] if row else None


def set_user_role(username, role):
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE users SET role = ? WHERE username = ?", (role, username))
    conn.commit()
    conn.close()


def get_all_users():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT username, role FROM users")
    users = c.fetchall()
    conn.close()
    return users


# global chat

def save_message(username, message):
    conn = get_connection()
    c = conn.cursor()
    c.execute("INSERT INTO messages (username, message) VALUES (?, ?)", (username, message))
    conn.commit()
    conn.close()


def get_last_messages(limit=10):
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "SELECT username, message, timestamp FROM messages ORDER BY id DESC LIMIT ?",
        (limit,),
    )
    rows = c.fetchall()
    conn.close()
    # reverse so the oldest message shows at the top
    return rows[::-1]


# moderation

def ban_user(username):
    conn = get_connection()
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO banned_users (username) VALUES (?)", (username,))
    conn.commit()
    conn.close()


def is_banned(username):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT 1 FROM banned_users WHERE username = ?", (username,))
    result = c.fetchone()
    conn.close()
    return result is not None


def unban_user(username):
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM banned_users WHERE username = ?", (username,))
    conn.commit()
    conn.close()


def mute_user(username):
    conn = get_connection()
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO muted_users (username) VALUES (?)", (username,))
    conn.commit()
    conn.close()


def is_muted(username):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT 1 FROM muted_users WHERE username = ?", (username,))
    result = c.fetchone()
    conn.close()
    return result is not None


def unmute_user(username):
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM muted_users WHERE username = ?", (username,))
    conn.commit()
    conn.close()


# server functions

def count_user_servers(owner):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM servers WHERE owner = ?", (owner,))
    count = c.fetchone()[0]
    conn.close()
    return count


def create_server(name, owner, password=None):
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "INSERT INTO servers (name, owner, password) VALUES (?, ?, ?)",
        (name, owner, password),
    )
    server_id = c.lastrowid
    # owner gets added as a member automatically with role owner
    c.execute(
        "INSERT INTO server_members (server_id, username, role) VALUES (?, ?, ?)",
        (server_id, owner, "owner"),
    )
    conn.commit()
    conn.close()
    return server_id


def get_server_by_name(name):
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "SELECT id, name, owner, password FROM servers WHERE LOWER(name) = LOWER(?)",
        (name,),
    )
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None


def get_server_by_id(server_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id, name, owner, password FROM servers WHERE id = ?", (server_id,))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None


def get_servers_for_user(username):
    conn = get_connection()
    c = conn.cursor()
    # join servers with server_members to get the user role in each server
    c.execute("""
        SELECT s.id, s.name, m.role
        FROM servers s
        JOIN server_members m ON s.id = m.server_id
        WHERE m.username = ?
    """, (username,))
    servers = c.fetchall()
    conn.close()
    return servers


def join_server(server_id, username, role="user"):
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "INSERT OR IGNORE INTO server_members (server_id, username, role) VALUES (?, ?, ?)",
        (server_id, username, role),
    )
    conn.commit()
    conn.close()


def leave_server(server_id, username):
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "DELETE FROM server_members WHERE server_id = ? AND username = ?",
        (server_id, username),
    )
    conn.commit()
    conn.close()


def delete_server(server_id):
    conn = get_connection()
    c = conn.cursor()
    # delete everything related to this server
    c.execute("DELETE FROM servers WHERE id = ?", (server_id,))
    c.execute("DELETE FROM server_members WHERE server_id = ?", (server_id,))
    c.execute("DELETE FROM server_messages WHERE server_id = ?", (server_id,))
    conn.commit()
    conn.close()


def get_server_members(server_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT username, role FROM server_members WHERE server_id = ?", (server_id,))
    members = c.fetchall()
    conn.close()
    return members


def set_server_member_role(server_id, username, role):
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "UPDATE server_members SET role = ? WHERE server_id = ? AND username = ?",
        (role, server_id, username),
    )
    conn.commit()
    conn.close()


def update_server_password(server_id, password):
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE servers SET password = ? WHERE id = ?", (password, server_id))
    conn.commit()
    conn.close()


def save_server_message(server_id, username, message):
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "INSERT INTO server_messages (server_id, username, message) VALUES (?, ?, ?)",
        (server_id, username, message),
    )
    conn.commit()
    conn.close()


def get_server_messages(server_id, limit=10):
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "SELECT username, message, timestamp FROM server_messages WHERE server_id = ? ORDER BY id DESC LIMIT ?",
        (server_id, limit),
    )
    rows = c.fetchall()
    conn.close()
    return rows[::-1]


# private messages

def save_private_message(sender, receiver, message):
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "INSERT INTO private_messages (sender, receiver, message) VALUES (?, ?, ?)",
        (sender, receiver, message),
    )
    conn.commit()
    conn.close()


def get_private_messages_for_user(user_id, limit=20):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT sender, receiver, message, timestamp
        FROM private_messages
        WHERE sender = ? OR receiver = ?
        ORDER BY id DESC LIMIT ?
    """, (user_id, user_id, limit))
    rows = c.fetchall()
    conn.close()
    return rows[::-1]

