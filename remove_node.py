import sqlite3

try:
    conn = sqlite3.connect('d:/NG/neuroguard.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM servers WHERE server_slug IN ('json-node', 'manual-input')")
    conn.commit()
    print(f"Deleted {cursor.rowcount} rows related to fallbacks.")
    conn.close()
except Exception as e:
    print("Database error:", e)
