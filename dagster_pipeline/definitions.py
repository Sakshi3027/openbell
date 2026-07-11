import dagster as dg
from dagster_pipeline.assets import (
    raw_stock_data,
    technical_indicators,
    ml_predictions,
    pre_market_report,
    openbell_dashboard
)
from dagster_pipeline.schedules import openbell_schedule

defs = dg.Definitions(
    assets=[
        raw_stock_data,
        technical_indicators,
        ml_predictions,
        pre_market_report,
        openbell_dashboard
    ],
    schedules=[openbell_schedule]
)
