import psycopg2
conn = psycopg2.connect(host='localhost', port=5432, user='postgres', password='123456')
conn.autocommit = True
cur = conn.cursor()

# Drop and recreate database
cur.execute("DROP DATABASE IF EXISTS voice_calendar")
cur.execute("CREATE DATABASE voice_calendar")
print('Database recreated')

conn.close()
