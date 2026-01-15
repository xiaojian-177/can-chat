import sqlite3

# 连接到数据库
conn = sqlite3.connect('chat.db')
cursor = conn.cursor()

# 手动添加image字段
try:
    print("Attempting to add 'image' field to messages table...")
    cursor.execute("ALTER TABLE messages ADD COLUMN image TEXT")
    conn.commit()
    print("Successfully added 'image' field to messages table!")
    
    # 验证字段是否添加成功
    cursor.execute("PRAGMA table_info(messages)")
    columns = cursor.fetchall()
    print("\nUpdated Messages table columns:")
    for column in columns:
        print(f"ID: {column[0]}, Name: {column[1]}, Type: {column[2]}, Not Null: {column[3]}, Default: {column[4]}, Primary Key: {column[5]}")
except sqlite3.OperationalError as e:
    if "duplicate column name" in str(e):
        print("'image' field already exists in messages table!")
    else:
        print(f"Error adding 'image' field: {e}")
    # 显示当前表结构
    cursor.execute("PRAGMA table_info(messages)")
    columns = cursor.fetchall()
    print("\nCurrent Messages table columns:")
    for column in columns:
        print(f"ID: {column[0]}, Name: {column[1]}, Type: {column[2]}, Not Null: {column[3]}, Default: {column[4]}, Primary Key: {column[5]}")
except Exception as e:
    print(f"Unexpected error: {e}")
finally:
    # 关闭连接
    cursor.close()
    conn.close()
    print("\nDone!")
