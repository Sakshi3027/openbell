import dagster as dg

openbell_schedule = dg.ScheduleDefinition(
    name="openbell_morning_bell",
    cron_schedule="0 8 * * 1-5",
    target=dg.AssetSelection.groups("openbell"),
    execution_timezone="America/New_York",
)
