import os
import bcrypt
from config import Config

def get_db():
    db_url = os.getenv('DATABASE_URL')
    if db_url and 'postgres' in db_url:
        import psycopg2
        from psycopg2.extras import RealDictCursor
        if db_url.startswith('postgres://'):
            db_url = db_url.replace('postgres://', 'postgresql://', 1)
        conn = psycopg2.connect(db_url, cursor_factory=RealDictCursor)
        return conn, 'postgres'
    else:
        import sqlite3
        conn = sqlite3.connect(Config.DATABASE_PATH)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn, 'sqlite'

def init_db():
    conn, dialect = get_db()
    cursor = conn.cursor()
    DATETIME_DEFAULT = "TIMESTAMP DEFAULT CURRENT_TIMESTAMP" if dialect == 'postgres' else "DATETIME DEFAULT CURRENT_TIMESTAMP"

    if dialect == 'postgres':
        cursor.execute(f'''CREATE TABLE IF NOT EXISTS users (
            user_id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at {DATETIME_DEFAULT})''')
        cursor.execute(f'''CREATE TABLE IF NOT EXISTS crop_analysis (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(user_id),
            image_path TEXT, disease TEXT, confidence INTEGER,
            affected_crop TEXT, severity TEXT, symptoms TEXT,
            treatment TEXT, prevention TEXT, is_healthy INTEGER DEFAULT 0,
            timestamp {DATETIME_DEFAULT})''')
        cursor.execute(f'''CREATE TABLE IF NOT EXISTS fertilizer_logs (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(user_id),
            crop TEXT, soil_type TEXT, stage TEXT, region TEXT,
            problem TEXT, fertilizer TEXT, quantity TEXT, advice TEXT,
            full_response TEXT, timestamp {DATETIME_DEFAULT})''')
        cursor.execute(f'''CREATE TABLE IF NOT EXISTS price_predictions (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(user_id),
            crop TEXT, state TEXT, current_price TEXT,
            predicted_price TEXT, trend TEXT, advice TEXT,
            full_response TEXT, timestamp {DATETIME_DEFAULT})''')
        cursor.execute(f'''CREATE TABLE IF NOT EXISTS voice_logs (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(user_id),
            transcript TEXT, language TEXT DEFAULT 'hi',
            intent TEXT, response_text TEXT, module_triggered TEXT,
            timestamp {DATETIME_DEFAULT})''')
        cursor.execute(f'''CREATE TABLE IF NOT EXISTS rate_limits (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(user_id),
            endpoint TEXT, timestamp {DATETIME_DEFAULT})''')
    else:
        cursor.execute('''CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL, email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS crop_analysis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER REFERENCES users(user_id),
            image_path TEXT, disease TEXT, confidence INTEGER,
            affected_crop TEXT, severity TEXT, symptoms TEXT,
            treatment TEXT, prevention TEXT, is_healthy INTEGER DEFAULT 0,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS fertilizer_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER REFERENCES users(user_id),
            crop TEXT, soil_type TEXT, stage TEXT, region TEXT,
            problem TEXT, fertilizer TEXT, quantity TEXT, advice TEXT,
            full_response TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS price_predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER REFERENCES users(user_id),
            crop TEXT, state TEXT, current_price TEXT,
            predicted_price TEXT, trend TEXT, advice TEXT,
            full_response TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS voice_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER REFERENCES users(user_id),
            transcript TEXT, language TEXT DEFAULT 'hi',
            intent TEXT, response_text TEXT, module_triggered TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS rate_limits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER REFERENCES users(user_id),
            endpoint TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')

    conn.commit()
    seed_demo_user(conn, dialect)
    conn.close()
    print(f"✅ Database initialized successfully ({dialect})")

def seed_demo_user(conn, dialect):
    cursor = conn.cursor()
    if dialect == 'postgres':
        cursor.execute("SELECT * FROM users WHERE email = %s", ("demo@agrismart.in",))
    else:
        cursor.execute("SELECT * FROM users WHERE email = ?", ("demo@agrismart.in",))
    
    if cursor.fetchone() is None:
        hashed = bcrypt.hashpw("kisan123".encode('utf-8'), bcrypt.gensalt())
        if dialect == 'postgres':
            cursor.execute(
                "INSERT INTO users (name, email, password) VALUES (%s, %s, %s)",
                ("Demo Kisan", "demo@agrismart.in", hashed.decode('utf-8'))
            )
        else:
            cursor.execute(
                "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
                ("Demo Kisan", "demo@agrismart.in", hashed.decode('utf-8'))
            )
        conn.commit()
        print("✅ Demo user created: demo@agrismart.in / kisan123")
    else:
        print("ℹ️  Demo user already exists")

def execute_query(conn, dialect, query, params=(), fetch_id=False):
    cursor = conn.cursor()
    
    if dialect == 'postgres':
        query = query.replace('?', '%s')
        if fetch_id:
            # users table mein primary key 'user_id' hai, baaki mein 'id'
            if "INTO USERS" in query.upper():
                query += " RETURNING user_id"
                pk = "user_id"
            else:
                query += " RETURNING id"
                pk = "id"

    cursor.execute(query, params)

    row_id = None
    if fetch_id:
        if dialect == 'postgres':
            res = cursor.fetchone()
            if res:
                if isinstance(res, dict):
                    row_id = res.get(pk)
                else:
                    try:
                        row_id = res[pk]
                    except (KeyError, IndexError):
                        row_id = res[0]
        else:
            row_id = cursor.lastrowid

    return cursor, row_id

if __name__ == '__main__':
    init_db()
