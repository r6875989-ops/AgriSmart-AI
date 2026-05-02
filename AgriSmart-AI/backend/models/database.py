import os
import bcrypt
import urllib.parse
from config import Config

def get_db():
    """Get database connection (PostgreSQL or SQLite fallback)"""
    db_url = os.getenv('DATABASE_URL')
    
    if db_url and db_url.startswith('postgres'):
        import psycopg2
        from psycopg2.extras import RealDictCursor
        # Fix Render dialect 
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
    """Initialize database with all tables"""
    conn, dialect = get_db()
    cursor = conn.cursor()
    
    # Define Types Based on Dialect
    AUTOINCREMENT = "SERIAL" if dialect == 'postgres' else "INTEGER PRIMARY KEY AUTOINCREMENT"
    DATETIME_DEFAULT = "TIMESTAMP DEFAULT CURRENT_TIMESTAMP" if dialect == 'postgres' else "DATETIME DEFAULT CURRENT_TIMESTAMP"
    
    if dialect == 'postgres':
        # PostgreSQL Queries
        cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS users (
                user_id SERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                created_at {DATETIME_DEFAULT}
            )
        ''')
        cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS crop_analysis (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(user_id),
                image_path TEXT,
                disease TEXT,
                confidence INTEGER,
                affected_crop TEXT,
                severity TEXT,
                symptoms TEXT,
                treatment TEXT,
                prevention TEXT,
                is_healthy INTEGER DEFAULT 0,
                timestamp {DATETIME_DEFAULT}
            )
        ''')
        cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS fertilizer_logs (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(user_id),
                crop TEXT,
                soil_type TEXT,
                stage TEXT,
                region TEXT,
                problem TEXT,
                fertilizer TEXT,
                quantity TEXT,
                advice TEXT,
                full_response TEXT,
                timestamp {DATETIME_DEFAULT}
            )
        ''')
        cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS price_predictions (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(user_id),
                crop TEXT,
                state TEXT,
                current_price TEXT,
                predicted_price TEXT,
                trend TEXT,
                advice TEXT,
                full_response TEXT,
                timestamp {DATETIME_DEFAULT}
            )
        ''')
        cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS voice_logs (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(user_id),
                transcript TEXT,
                language TEXT DEFAULT 'hi',
                intent TEXT,
                response_text TEXT,
                module_triggered TEXT,
                timestamp {DATETIME_DEFAULT}
            )
        ''')
        cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS rate_limits (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(user_id),
                endpoint TEXT,
                timestamp {DATETIME_DEFAULT}
            )
        ''')
    else:
        # SQLite Queries
        cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS crop_analysis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER REFERENCES users(user_id),
                image_path TEXT,
                disease TEXT,
                confidence INTEGER,
                affected_crop TEXT,
                severity TEXT,
                symptoms TEXT,
                treatment TEXT,
                prevention TEXT,
                is_healthy INTEGER DEFAULT 0,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS fertilizer_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER REFERENCES users(user_id),
                crop TEXT,
                soil_type TEXT,
                stage TEXT,
                region TEXT,
                problem TEXT,
                fertilizer TEXT,
                quantity TEXT,
                advice TEXT,
                full_response TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS price_predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER REFERENCES users(user_id),
                crop TEXT,
                state TEXT,
                current_price TEXT,
                predicted_price TEXT,
                trend TEXT,
                advice TEXT,
                full_response TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS voice_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER REFERENCES users(user_id),
                transcript TEXT,
                language TEXT DEFAULT 'hi',
                intent TEXT,
                response_text TEXT,
                module_triggered TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS rate_limits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER REFERENCES users(user_id),
                endpoint TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
    conn.commit()
    seed_demo_user(conn, dialect)
    conn.close()
    print(f"✅ Database initialized successfully ({dialect})")

def seed_demo_user(conn, dialect):
    """Seed the database with a demo user"""
    cursor = conn.cursor()
    
    q = "SELECT * FROM users WHERE email = %s" if dialect == 'postgres' else "SELECT * FROM users WHERE email = ?"
    cursor.execute(q, ("demo@agrismart.in",))
    
    if cursor.fetchone() is None:
        hashed = bcrypt.hashpw("kisan123".encode('utf-8'), bcrypt.gensalt())
        
        ins = "INSERT INTO users (name, email, password) VALUES (%s, %s, %s)" if dialect == 'postgres' else "INSERT INTO users (name, email, password) VALUES (?, ?, ?)"
        cursor.execute(ins, ("Demo Kisan", "demo@agrismart.in", hashed.decode('utf-8')))
        conn.commit()
        print("✅ Demo user created: demo@agrismart.in / kisan123")
    else:
        print("ℹ️  Demo user already exists")

def execute_query(conn, dialect, query, params=(), fetch_id=False):
    """Helper to safely execute SQL and get row ID across both dialects"""
    cursor = conn.cursor()
    
    # Translate query if Postgres
    if dialect == 'postgres':
        query = query.replace('?', '%s')
        if fetch_id:
            # We assume the PK is usually 'id' or 'user_id'
            # Look for table name to guess PK
            pk = "user_id" if "INTO users" in query.upper() else "id"
            query += f" RETURNING {pk}"
            
    cursor.execute(query, params)
    
    row_id = None
    if fetch_id:
        if dialect == 'postgres':
            res = cursor.fetchone()
            if res:
                row_id = list(res.values())[0] if type(res) == dict else res[0]
        else:
            row_id = cursor.lastrowid
            
    return cursor, row_id

if __name__ == '__main__':
    init_db()
