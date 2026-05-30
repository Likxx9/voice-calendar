import psycopg2
conn = psycopg2.connect(host='localhost', port=5432, user='postgres', password='123456')
conn.autocommit = True
cur = conn.cursor()
cur.execute("SELECT 1 FROM pg_database WHERE datname='voice_calendar'")
if not cur.fetchone():
    cur.execute("CREATE DATABASE voice_calendar")
    print('Database created')
else:
    print('Database exists')
conn.close()
