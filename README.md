# Branch-specific event triggering example
Demonstrates how to configure Outerbounds project flows to respond to external
events and schedules, with branch-specific behavior for events, 
in this case **only the prod (main branch) version** reacting to
external signals.

## Quickstart instructions
- Create a GitHub repository 
- Create a GitHub Actions machine user in the Outerbounds UI named `prod-event-example-cicd` with info for your GitHub org
- Push this repository to your fork/copy of this repository, you should then see a GitHub action and results of `obproject-deploy`
- Continue [testing](./TESTING.md)

## The pattern in context

| Decorator | Branch behavior | Use when |
|---|---|---|
| `@schedule(cron=...)` | Each branch gets its own CronWorkflow (isolated, cleaned up on teardown) | You want periodic runs |
| `@project_trigger(event=...)` | Sensor scoped to `prj.<project>.<branch>.<event>` — **prod-only by default** when external publishers target the main branch event | External systems should only trigger prod |
| `@trigger_on_finish(flow=...)` | Already branch-scoped — works out of the box | Flow chaining within the same project |
| `@trigger(event=...)` | 🚨 **NOT** branch-scoped — all branches react to the same event | Avoid for branch-specific use cases |

## Flows

```
flows/
  scheduled_ingest/flow.py     # @schedule — daily cron, publishes project event
  event_processor/flow.py      # @project_trigger — external event, branch-aware
  chained_reporter/flow.py     # @trigger_on_finish — fires after event_processor
```

### How external events target only prod

When `obproject-deploy` runs on `main` code branch (and translated to `prod` in the Metaflow namespace), the `@project_trigger(event="external_signal")`
sensor listens for:

```
prj.prod_event_example.main.external_signal
prj.<project-name>.<branch-name>.<event-name>
```

When deployed on a feature branch `feature/foo`, the sensor listens for:

```
prj.prod_event_example.feature_foo.external_signal
```

An external system (app, CI job, Argo Events webhook) that publishes to the
`main` event name will **only** trigger the prod flow. Feature branch sensors
are listening on a different event name entirely.

#### Publishing an event from outside (targeting prod)

```python
from obproject.project_events import ProjectEvent

# Explicitly target prod
ProjectEvent("external_signal", project="prod_event_example", branch="main").safe_publish(
    payload={"record_count": 100}
)
```

Or using the raw Argo Events API:

```python
from metaflow.integrations import ArgoEvent

ArgoEvent("prj.prod_event_example.main.external_signal").safe_publish(
    payload={"record_count": 100}
)
```