"""
Scheduled Ingest Flow
---------------------
Runs on a daily cron schedule via Argo CronWorkflow.

Key behavior:
- Each deployed branch gets its OWN CronWorkflow (isolated).
- Publishes a branch-scoped project event on completion, so only
  the EventProcessor deployed on the SAME branch is triggered.

If you want ONLY the prod branch to run on schedule, see the README
for the branch-filtering approach.
"""

from metaflow import step, schedule, current
from obproject import ProjectFlow


@schedule(cron="0 8 * * 1-5", timezone="America/New_York")
class ScheduledIngestFlow(ProjectFlow):

    @step
    def start(self):
        print(f"Ingesting data on branch: {current.branch_name}")
        self.record_count = 42  # placeholder for real ingest logic
        self.next(self.end)

    @step
    def end(self):
        print(f"Ingested {self.record_count} records.")
        # Publish a branch-scoped event to trigger downstream processing.
        # On prod  -> fires: prj.prod_event_example.main.ingest_complete
        # On feat  -> fires: prj.prod_event_example.<branch>.ingest_complete
        # This means only the EventProcessor on the SAME branch reacts.
        self.prj.safe_publish_event(
            "ingest_complete", payload={"record_count": self.record_count}
        )
        print("Published 'ingest_complete' project event.")


if __name__ == "__main__":
    ScheduledIngestFlow()
