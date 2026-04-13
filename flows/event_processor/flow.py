"""
Event Processor Flow
--------------------
Triggered by an external event (e.g. from another service, an app, or a CI job).

Uses @project_trigger — the branch-aware variant of @trigger.

Key behavior:
- @project_trigger scopes the Argo Sensor to:
      prj.<project>.<branch>.<event_name>
- So the prod deployment listens on:
      prj.prod_event_example.main.external_signal
- A feature branch deployment listens on:
      prj.prod_event_example.<feature_branch>.external_signal

External systems that publish to `prj.prod_event_example.main.external_signal`
will ONLY trigger the prod version. Feature branch sensors ignore it.

Contrast with plain @trigger(event="external_signal"), which would create
a sensor for the SAME event name on every branch — all branches would fire.
"""

from metaflow import step, Parameter
from obproject import ProjectFlow, project_trigger


@project_trigger(event="external_signal")
class EventProcessorFlow(ProjectFlow):

    record_count = Parameter("record_count", default=0, type=int)

    @step
    def start(self):
        print(f"Received external signal with record_count={self.record_count}")
        self.result = f"Processed {self.record_count} records"
        self.next(self.end)

    @step
    def end(self):
        print(self.result)


if __name__ == "__main__":
    EventProcessorFlow()
