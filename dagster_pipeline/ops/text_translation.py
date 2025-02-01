import pandas as pd
from text_utils import get_translation
from database_utils import connection_postgres
from dagster import op

@op
def translate_text():
    db_host, db_name, db_user, db_password, db_port, conn, cur = connection_postgres()

    try:
        query = "SELECT comment_id, comment_text FROM comment JOIN date ON(comment.date_id=date.date_id) WHERE translated_comment_text IS NULL ORDER BY year ASC, month ASC, day ASC LIMIT 10;"
        cur.execute(query)

        results = cur.fetchall()

        if not results:
            print("No results found.")
            return

        col_names = [desc[0] for desc in cur.description]

        df = pd.DataFrame(results, columns=col_names)

        df['translated_comment_text'] = df['comment_text'].apply(lambda x: get_translation(x))

        for index, row in df.iterrows():
            update_query = f"""
                    UPDATE comment
                    SET translated_comment_text = %s
                    WHERE comment_id = %s;
                """
            cur.execute(update_query, (row['translated_comment_text'], row['comment_id']))

        conn.commit()
        print("Translated comments updated successfully.")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        cur.close()
        conn.close()

if __name__ == '__main__':
    db_host, db_name, db_user, db_password, db_port, conn, cur = connection_postgres()

    query = "SELECT comment_id, comment_text FROM comment JOIN date ON(comment.date_id=date.date_id) WHERE translated_comment_text IS NULL ORDER BY year ASC, month ASC, day ASC LIMIT 50;"
    cur.execute(query)
    conn.commit()

    results = cur.fetchall()

    while True:
        if not results:
            print("no more text to translate")
            break
        else:
            translate_text()

    cur.close()
    conn.close()