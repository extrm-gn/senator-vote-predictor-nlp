from dagster import job
from dagster_pipeline.ops.gather_comments import gather_comments_op
from dagster_pipeline.ops.init_db import init_db
from dagster_pipeline.ops.text_translation import translate_text
from dagster_pipeline.ops.export_db import export_table_to_csv
from dagster import repository
from dagster import (
    AssetSelection,
    Definitions,
    ScheduleDefinition,
    define_asset_job,

)

@job
def training_pipeline():
    """Defines the Dagster pipeline flow."""
    initialize_db = init_db()
    comments = gather_comments_op()
    translate_comment_text = translate_text()
    export_data = export_table_to_csv()