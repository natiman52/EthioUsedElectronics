import mysql.connector
import json
import dotenv 
import os

dotenv.load_dotenv()
# --- Configuration for MySQL Connection ---
# !! IMPORTANT !! Replace these with your actual MySQL database credentials
DB_CONFIG = {
    "host": os.getenv("USEDELECTRONICS_DB_HOST"),
    "user": os.getenv("USEDELECTRONICS_DB_USER"),
    "password": os.getenv("USEDELECTRONICS_DB_PASSWORD"),
    "database":os.getenv("USEDELECTRONICS_DB_NAME")
}

def get_db_connection():
    return mysql.connector.connect(**DB_CONFIG)

def init_db():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # 1. Create users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id BIGINT PRIMARY KEY,
                full_name VARCHAR(255),
                phone VARCHAR(255),
                username VARCHAR(255),
                front_id TEXT,
                back_id TEXT,
                bank_account TEXT,
                location TEXT,
                status VARCHAR(50) DEFAULT 'pending'
            ) ENGINE=InnoDB
        """)

        # 2. Create items table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS items (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id BIGINT,
                category VARCHAR(255),
                answers JSON,
                photos JSON,
                edited_answers JSON,
                status VARCHAR(50) DEFAULT 'pending',
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            ) ENGINE=InnoDB
        """)

        # Note on ALTER TABLE:
        # The original SQLite code included logic to add 'bank_account' and 'location' 
        # if they didn't exist. In the MySQL setup above, they are included 
        # in the initial CREATE TABLE statement for simplicity and best practice.
        # If you need similar dynamic column checking, you would use 
        # 'SHOW COLUMNS FROM users LIKE 'column_name'' and an ALTER TABLE if needed.
        # The original SQLite version's column check logic is omitted here as 
        # the columns are defined in the initial table creation.

        conn.commit()
        print("MySQL database initialization complete.")
    except mysql.connector.Error as err:
        print(f"Error during MySQL initialization: {err}")
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

def save_user(user_id, name, phone, username, front_id, back_id, bank_account, location):
    """Inserts a new user record."""
    conn = get_db_connection()
    cursor = conn.cursor()
    sql = """
        INSERT INTO users (user_id, full_name, phone, username, front_id, back_id, bank_account, location, status) 
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'pending')
    """
    try:
        cursor.execute(sql, (user_id, name, phone, username, front_id, back_id, bank_account, location))
        conn.commit()
    except mysql.connector.Error as err:
        print(f"Error saving user: {err}")
    finally:
        cursor.close()
        conn.close()

def update_status(user_id, new_status):
    """Updates the status of a user."""
    conn = get_db_connection()
    cursor = conn.cursor()
    sql = "UPDATE users SET status=%s WHERE user_id=%s"
    try:
        cursor.execute(sql, (new_status, user_id))
        conn.commit()
    finally:
        cursor.close()
        conn.close()

async def get_user_info(identifier,update):
    conn = get_db_connection()
    c = conn.cursor()
    if identifier.startswith("@"):
        username = identifier[1:].lower()
        c.execute("SELECT * FROM users WHERE LOWER(username)=%s", (username,))
    else:
        try:
            user_id = int(identifier)
            c.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
        except ValueError:
            conn.close()
            await update.message.reply_text("❌ Invalid user ID format.")
            return False
    user = c.fetchone()
    if not user:
        conn.close()
        await update.message.reply_text("❌ User not found in database.")
        return False
    c.execute("SELECT COUNT(*) FROM items WHERE user_id=?", (user_id,))
    posts = c.fetchone()[0]
    conn.close()
    return user

def fetchall_ids():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT user_id FROM users WHERE status='approved'")
    users = [row[0] for row in c.fetchall()]
    conn.close()
    return users
def get_status(user_id):
    """Fetches the status of a user."""
    conn = get_db_connection()
    cursor = conn.cursor()
    sql = "SELECT status FROM users WHERE user_id=%s"
    try:
        cursor.execute(sql, (user_id,))
        result = cursor.fetchone()
        return result[0] if result else None
    finally:
        cursor.close()
        conn.close()

def save_item(user_id, category, answers, photos):
    """Inserts a new item record and returns its ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    # MySQL uses JSON type for storing JSON objects, but the connector handles Python dicts/lists.
    sql = """
        INSERT INTO items (user_id, category, answers, photos, status)
        VALUES (%s, %s, %s, %s, 'pending')
    """
    try:
        # Pass Python objects directly, connector handles serialization for JSON columns
        cursor.execute(sql, (user_id, category, answers, photos))
        item_id = cursor.lastrowid
        conn.commit()
        print(f"Saved item for user {user_id} with item_id={item_id}")
        return item_id
    except mysql.connector.Error as err:
        print(f"Error saving item: {err}")
        return None
    finally:
        cursor.close()
        conn.close()

def get_user_full_name(user_id):
    """Fetches the full name of a user."""
    conn = get_db_connection()
    cursor = conn.cursor()
    sql = "SELECT full_name FROM users WHERE user_id=%s"
    try:
        cursor.execute(sql, (user_id,))
        result = cursor.fetchone()
        return result[0] if result else "Unknown"
    finally:
        cursor.close()
        conn.close()

def update_item_field(item_id, field, new_value):
    """Updates a single field in the 'edited_answers' JSON column of an item."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # 1. Fetch current edited_answers
        cursor.execute("SELECT edited_answers FROM items WHERE id=%s", (item_id,))
        row = cursor.fetchone()
        
        # MySQL JSON column returns a string/dict depending on connector/version, 
        # so we'll treat it as a dict/None.
        # Use JSON_SET for an atomic update (preferred) or re-read/update/re-write (as done in the original logic)
        
        # Option A: Re-read, Update in Python, Re-write (follows original logic)
        edited = row[0] if row and row[0] else {}
        if isinstance(edited, str): # Handle cases where it's a JSON string
            edited = json.loads(edited)
        
        edited[field] = new_value
        
        # 2. Update the column
        sql_update = "UPDATE items SET edited_answers=%s WHERE id=%s"
        cursor.execute(sql_update, (json.dumps(edited), item_id))
        conn.commit()
        
    except mysql.connector.Error as err:
        print(f"Error updating item field: {err}")
    finally:
        cursor.close()
        conn.close()

def get_user_location(user_id):
    """Fetches the location of a user."""
    conn = get_db_connection()
    cursor = conn.cursor()
    sql = "SELECT location FROM users WHERE user_id=%s"
    try:
        cursor.execute(sql, (user_id,))
        result = cursor.fetchone()
        return result[0] if result else "Unknown"
    finally:
        cursor.close()
        conn.close()

def get_final_item(item_id):
    """Fetches item data, merging original answers with edited answers."""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True) # Fetch as a dictionary for easier access
    sql = "SELECT user_id, category, answers, photos, edited_answers FROM items WHERE id=%s"
    try:
        cursor.execute(sql, (item_id,))
        row = cursor.fetchone()
        
        if not row:
            return None
            
        user_id = row['user_id']
        category = row['category']
        # Connector can return JSON columns as Python dicts/lists directly
        answers = row['answers'] or {}
        photos = row['photos'] or []
        edited = row['edited_answers'] or {}

        # Ensure they are dicts if they came as None from an empty JSON column
        if not isinstance(answers, dict): answers = {}
        if not isinstance(edited, dict): edited = {}

        final_answers = answers.copy()
        final_answers.update(edited)
        
        return {
            "user_id": user_id,
            "category": category, 
            "answers": final_answers, 
            "photos": photos
        }
    finally:
        cursor.close()
        conn.close()

def mark_item_posted(item_id):
    """Sets the status of an item to 'posted'."""
    conn = get_db_connection()
    cursor = conn.cursor()
    sql = "UPDATE items SET status='posted' WHERE id=%s"
    try:
        cursor.execute(sql, (item_id,))
        conn.commit()
    finally:
        cursor.close()
        conn.close()

def fetch_user(identifier):
    """Fetches a user by user_id or username."""
    conn = get_db_connection()
    cursor = conn.cursor()
    sql = ""
    param = None
    
    if str(identifier).startswith("@"):
        sql = "SELECT user_id, full_name, phone, username, front_id, back_id, bank_account, location, status FROM users WHERE username=%s"
        param = identifier[1:]
    else:
        sql = "SELECT user_id, full_name, phone, username, front_id, back_id, bank_account, location, status FROM users WHERE user_id=%s"
        param = identifier
        
    try:
        cursor.execute(sql, (param,))
        user = cursor.fetchone()
        return user
    finally:
        cursor.close()
        conn.close()

def get_bot_stats():
    """Calculates and returns key statistics for users and items."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        stats = {}
        
        cursor.execute("SELECT COUNT(*) FROM users")
        stats["total_users"] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM users WHERE status='approved'")
        stats["approved"] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM users WHERE status='pending'")
        stats["pending"] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM users WHERE status='banned'")
        stats["banned"] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM items")
        stats["total_items"] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM items WHERE status='posted'")
        stats["posted"] = cursor.fetchone()[0]
        
        return stats
    finally:
        cursor.close()
        conn.close()

def update_user_status(user_id, status):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("UPDATE users SET status=%s WHERE user_id=%s", (status, user_id))
    conn.commit()
    conn.close()
def set_user_status(identifier, status):
    """Updates a user's status based on user_id or username."""
    conn = get_db_connection()
    cursor = conn.cursor()
    sql = ""
    params = []
    
    if str(identifier).startswith("@"):
        sql = "UPDATE users SET status=%s WHERE username=%s"
        params = (status, identifier[1:])
    else:
        sql = "UPDATE users SET status=%s WHERE user_id=%s"
        params = (status, identifier)
        
    try:
        cursor.execute(sql, params)
        conn.commit()
    finally:
        cursor.close()
        conn.close()

# Example of how to use it:
# if __name__ == '__main__':
#     # Make sure you have created the 'users_items_db' database in MySQL
#     init_db()