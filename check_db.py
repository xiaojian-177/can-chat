import sqlite3

# 连接到数据库
conn = sqlite3.connect('chat.db')
cursor = conn.cursor()

# 查询messages表的结构
print("Checking messages table structure...")
cursor.execute("PRAGMA table_info(messages)")
columns = cursor.fetchall()

print("\nMessages table columns:")
for column in columns:
    print(f"ID: {column[0]}, Name: {column[1]}, Type: {column[2]}, Not Null: {column[3]}, Default: {column[4]}, Primary Key: {column[5]}")

# 查询所有表
print("\nAll tables in database:")
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
for table in tables:
    print(table[0])

# 关闭连接
cursor.close()
conn.close()
print("\nDone!")
