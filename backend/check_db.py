import psycopg2
conn = psycopg2.connect(host='localhost', port=5432, user='postgres', password='123456', dbname='voice_calendar')
cur = conn.cursor()
cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public'")
print('Tables:', [t[0] for t in cur.fetchall()])
conn.close()
