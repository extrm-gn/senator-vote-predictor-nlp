import pandas as pd
from text_utils import get_translation
from database_utils import connection_postgres


def translate_text():
    db_host, db_name, db_user, db_password, db_port, conn, cur = connection_postgres()

    try:
        query = "SELECT comment_id, comment_text FROM comment WHERE translated_comment_text IS NULL;"
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
                    WHERE id = %s;
                """
            cur.execute(update_query, (row['translated_comment_text'], row['id']))

        conn.commit()
        print("Translated comments updated successfully.")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        cur.close()
        conn.close()

translate_text()