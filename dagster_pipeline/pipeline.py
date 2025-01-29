from dagster import job
from ops.gather_comments import gather_comments_op
from ops.init_db import init_db
from ops.text_translation import translate_text
from ops.export_db import export_table_to_csv


@job
def training_pipeline():
    """Defines the Dagster pipeline flow."""
    initialize_db = init_db()
    comments = gather_comments_op()
    translate_comment_text = translate_text()
    export_data = export_table_to_csv()