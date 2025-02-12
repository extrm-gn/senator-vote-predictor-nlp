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

all_assets = [init_db,
              gather_comments_op,
              translate_text,
              export_table_to_csv]

data_pipeline_job = define_asset_job("data_pipeline_job", selection=AssetSelection.all())

ingestion_schedule = ScheduleDefinition(
    job=data_pipeline_job,
    cron_schedule="0 8 * * *",  # every 5 minute
)

@repository
def my_repository():
    return [
        data_pipeline_job,
        ingestion_schedule,
        *all_assets
    ]

# @job
# def training_pipeline():
#     """Defines the Dagster pipeline flow."""
#     initialize_db = init_db()
#     comments = gather_comments_op()
#     translate_comment_text = translate_text()
#     export_data = export_table_to_csv()