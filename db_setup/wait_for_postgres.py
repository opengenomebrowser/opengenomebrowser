import psycopg2
import os
import time

DB_HOST = os.environ.get('DB_HOST', 'db')
DB_PORT = os.environ.get('DB_PORT', '5432')
DB_NAME = os.environ.get('DB_NAME', 'opengenomebrowser_db')
DB_USER = os.environ.get('DB_USER', 'postgres')
DB_PASSWORD = os.environ.get('DB_PASSWORD', 'postgres')


def postgres_up() -> bool:
    try:
        conn = psycopg2.connect(host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASSWORD, database=DB_NAME, connect_timeout=1)
        conn.close()
        return True
    except:
        return False


counter = 1
while not postgres_up():
    print(f'waiting for postgresql... {counter}')
    time.sleep(1)

    if counter >= 50:
        print(f'could not connect to postgresql! {DB_HOST=} {DB_PORT=} {DB_USER=} {DB_PASSWORD=}')
        exit(1)
    counter += 1

print('postgres ready!')
