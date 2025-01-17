import psycopg2

conn = psycopg2.connect(host="localhost", dbname="postgres", user="postgres",
                        password="1234", port=5432)

cur = conn.cursor()

cur.execute("""CREATE TABLE IF NOT EXISTS person (
                id INT PRIMARY KEY,
                name VARCHAR(255),
                age INT,
                gender CHAR);""")

cur.execute("""INSERT INTO person (id,name,age,gender) VALUES
                (1, 'Mike', 30, 'm')""")
conn.commit()

cur.close()
conn.close()


def init_db():
    return 0


def insert_comments(comments):
    return 0