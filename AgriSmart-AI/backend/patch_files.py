import os
import re

files_to_patch = [
    r"c:\Users\r6875\OneDrive\Desktop\project_Agri(Data_set)\AgriSmart-AI\backend\routes\dashboard.py",
    r"c:\Users\r6875\OneDrive\Desktop\project_Agri(Data_set)\AgriSmart-AI\backend\services\auth_service.py"
]

for file in files_to_patch:
    with open(file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace imports
    content = content.replace("from models.database import get_db", "from models.database import get_db, execute_query")
    
    # Replace conn.cursor() sequence
    # Since we are doing selects, we can just replace cursor.execute(query, params)
    # with cursor, _ = execute_query(conn, dialect, query, params)
    
    # Add dialect to conn = get_db()
    content = content.replace("conn = get_db()", "conn, dialect = get_db()")
    content = content.replace("cursor = conn.cursor()", "")
    
    # Replace cursor.execute(...)
    # We will use regex to find cursor.execute("...", (...))
    content = re.sub(r'cursor\.execute\((.*?),\s*\((.*?)\)\)', r'cursor, _ = execute_query(conn, dialect, \1, (\2))', content, flags=re.DOTALL)
    
    # Specifically fix dashboard timestamp queries which dont have ? but use execute
    # Actually wait, execute_query takes a query and params=(). If no params exist, we just pass ().
    # Let's manually review after.
    
    with open(file, 'w', encoding='utf-8') as f:
        f.write(content)

print("Patched remaining files for universal DB execution.")
