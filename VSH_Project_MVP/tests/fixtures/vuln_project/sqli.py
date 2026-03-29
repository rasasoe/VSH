import sqlite3
conn = sqlite3.connect(":memory:")
cursor = conn.cursor()
cursor.execute("CREATE TABLE users(id INT, name TEXT)")
name = input("Enter name: ")
query = f"SELECT * FROM users WHERE name = '{name}'"
print(query)
cursor.execute(query)  # SQL Injection 취약점 예시
