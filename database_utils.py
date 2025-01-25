import psycopg2
from datetime import date, timedelta, datetime
import pandas as pd
import os
from dotenv import load_dotenv

def create_date_dimension():
    start_date = datetime(2020, 10, 1)
    end_date = datetime(2029, 5, 12)

    date_list = []

    while start_date < end_date:
        date_list.append(start_date)
        start_date += timedelta(days=1)

    date_data = []

    for date in date_list:
        date_dict = {
            'date_id': f"{date.month:02}{date.day:02}{date.year}",
            'month': date.month,
            'day': date.day,
            'year': date.year
        }
        date_data.append(date_dict)

    date_df = pd.DataFrame(date_data)

    return date_df


def connection_postgres():

    load_dotenv()

    db_host = os.getenv("DB_HOST")
    db_name = os.getenv("DB_NAME")
    db_user = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD")
    db_port = os.getenv("DB_PORT")

    conn = psycopg2.connect(dbname=db_name,
                            user=db_user,
                            password=db_password,
                            host=db_host,
                            port=db_port)

    cursor = conn.cursor()

    return db_host, db_name, db_user, db_password, db_port, conn, cursor

def insert_code(df, table_name):
    # Generate SQL statements
    sql_statements = []
    for index, row in df.iterrows():
        # Escape single quotes in string values
        values = [
            f"'{str(value).replace("'", "''")}'" if isinstance(value, str) else str(value)
            for value in row
        ]

        if table_name == 'video':
            sql = f"INSERT INTO {table_name} ({', '.join(df.columns)}) VALUES ({', '.join(values)}) ON CONFLICT (video_id) DO NOTHING;"
            sql_statements.append(sql)
        elif table_name == 'author':
            sql = f"INSERT INTO {table_name} ({', '.join(df.columns)}) VALUES ({', '.join(values)}) ON CONFLICT (author_id) DO NOTHING;"
            sql_statements.append(sql)
        elif table_name == 'comment':
            sql = f"INSERT INTO {table_name} ({', '.join(df.columns)}) VALUES ({', '.join(values)}) ON CONFLICT (video_id, author_id, comment_text) DO NOTHING;"
            sql_statements.append(sql)
        elif table_name == 'date':
            sql = f"INSERT INTO {table_name} ({', '.join(df.columns)}) VALUES ({', '.join(values)}) ON CONFLICT (date_id) DO NOTHING;"
            sql_statements.append(sql)


    # Combine all SQL statements
    sql_script = "\n".join(sql_statements)

    print(sql_script)

    return sql_script


#create function that would insert in training_metadata and update video table in training_id
def insert_training_metadata(list_of_table, model_name):
    db_host, db_name, db_user, db_password, db_port, conn, cur = connection_postgres()

    query = "SELECT * FROM training_metadata WHERE status = 'active'"
    cur.execute(query)
    rows = cur.fetchall()

    if not rows:
        print("No active rows found.")
    else:
        print(f"Found {len(rows)} active rows.")
        update_command = """UPDATE training_metadata SET status = 'inactive' WHERE status = 'active'"""

        cur.execute(update_command)
        conn.commit()

    train_data = [{'video_ids': list_of_table, 'model_name': model_name, 'status': 'active', 'training_date': datetime.now()}]
    df = pd.DataFrame(train_data)

    sql_command = insert_code(df, 'training_metadata')
    cur.execute(sql_command)

    conn.commit()
    cur.close()
    conn.close()


def main():
    conn = None
    try:
        db_host, db_name, db_user, db_password, db_port, conn, cur = connection_postgres()

        cur.close()
        conn.close()
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if conn:
            conn.close()
            print("Connection closed.")


if __name__ == "__main__":
    main()