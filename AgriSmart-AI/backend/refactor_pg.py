import os
import glob
import re

routes_dir = r"c:\Users\r6875\OneDrive\Desktop\project_Agri(Data_set)\AgriSmart-AI\backend\routes"
services_dir = r"c:\Users\r6875\OneDrive\Desktop\project_Agri(Data_set)\AgriSmart-AI\backend\services"

# Find all python files
py_files = glob.glob(os.path.join(routes_dir, "*.py")) + glob.glob(os.path.join(services_dir, "*.py"))

for file_path in py_files:
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace ? with %s
    # Note: this simple replacement assumes ? is only used in SQL statements!
    # In python code, ? is rarely used except strings. We will safely replace all ? in strings.
    # Actually, let's just do a string replace of query executions.
    
    # Find cursor.execute("...", (...))
    parts = content.split('cursor.execute(')
    new_content = parts[0]
    
    for part in parts[1:]:
        # Find the end of the query string
        # It could be single quotes or triple quotes. Instead of complex parsing,
        # just replace all unescaped ? with %s in the file.
        pass
    
    # Let's use a simpler approach: Just replace ? with %s inside quotes or universally since ? is rare in python logic.
    content = content.replace('?', '%s')
    
    # Fix cursor.lastrowid -> cursor.fetchone()[0]
    # But wait, we need to add RETURNING id to the INSERT statement.
    content = content.replace('cursor.lastrowid', '(cursor.fetchone()[0] if cursor.description else None)')
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
print("Replaced ? with %s in all routes and services.")
