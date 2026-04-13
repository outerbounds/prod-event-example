"""
Chained Reporter Flow
---------------------
Triggered when EventProcessorFlow finishes, using @trigger_on_finish.

Key behavior:
- @trigger_on_finish is ALREADY branch-scoped in projects — no special
  configuration needed. It only fires when the flow on the SAME branch
  completes.
"""

from metaflow import step, current, trigger_on_finish
from obproject import ProjectFlow


@trigger_on_finish(flow="EventProcessorFlow")
class ChainedReporterFlow(ProjectFlow):

    @step
    def start(self):
        upstream = current.trigger.run
        print(f"EventProcessorFlow finished: {upstream.data.result}")
        self.next(self.end)

    @step
    def end(self):
        print("Report complete.")


if __name__ == "__main__":
    ChainedReporterFlow()
