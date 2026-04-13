# Test & Verification Plan

## Goal

Verify that external events and schedules only trigger the **prod** (main branch)
version of flows, while feature branches remain isolated.

---

## Phase 1: Local Smoke Test

Run each flow locally to confirm they parse and execute without errors.

```bash
cd prod-event-example

# 1. Scheduled ingest (runs start → end)
python flows/scheduled_ingest/flow.py run

# 2. Event processor (runs with default params since no event fires locally)
python flows/event_processor/flow.py run

# 3. Chained reporter — skip locally (requires upstream run in Argo)
```

**Expected**: Both flows complete successfully with printed output.

---

## Phase 2: Deploy (main branch)

```bash
# From the prod-event-example directory, on main branch
obproject-deploy
```

### Verify Argo resources created

After deploy, check the UI for:

| Resource | Flow | Type |
|---|---|---|
| CronWorkflow | `ScheduledIngestFlow` | `prod_event_example.prod.scheduledingestflow` |
| Sensor | `EventProcessorFlow` | listens on `prj.prod_event_example.main.external_signal` |
| Sensor | `ChainedReporterFlow` | listens on `EventProcessorFlow` finish (same branch) |

---

## Phase 3: Deploy a feature branch

```bash
git checkout -b feature/test-isolation
obproject-deploy
```

### Verify branch isolation

The feature branch should create **separate** Argo resources:

| Resource | Scoped event name |
|---|---|
| CronWorkflow | `prod_event_example.test.feature_test_isolation.scheduledingestflow` |
| Sensor | `prj.prod_event_example.feature_test_isolation.external_signal` |
| Sensor | `EventProcessorFlow` finish on `test.feature_test_isolation` branch |

---

## Phase 4: Fire an external event targeting prod

From a workstation or any environment with Metaflow configured:

```python
from obproject.project_events import ProjectEvent

# Target prod explicitly
ProjectEvent(
    "external_signal",
    project="prod_event_example",
    branch="main",
).safe_publish(payload={"record_count": 100})
```

### Expected results

| Check | Expected |
|---|---|
| Prod `EventProcessorFlow` triggered? | YES — new run appears |
| Feature branch `EventProcessorFlow` triggered? | NO — sensor is on a different event name |
| Prod `ChainedReporterFlow` triggered? | YES — fires after prod `EventProcessorFlow` finishes |
| Feature `ChainedReporterFlow` triggered? | NO — only fires on same-branch completion |

### How to verify

```bash
# Check prod runs
python -c "
from metaflow import Flow
for run in Flow('EventProcessorFlow').runs():
    if 'prod' in run.parent.id:
        print(run, run.created_at, run.data.result)
        break
"
```

Or check the Outerbounds UI: navigate to the project, confirm only the prod
branch shows new runs.

---

## Phase 5: Fire an event targeting the feature branch

```python
from obproject.project_events import ProjectEvent

# Target feature branch explicitly
ProjectEvent(
    "external_signal",
    project="prod_event_example",
    branch="feature_test_isolation",
).safe_publish(payload={"record_count": 999})
```

### Expected results

| Check | Expected |
|---|---|
| Feature `EventProcessorFlow` triggered? | YES |
| Prod `EventProcessorFlow` triggered? | NO |

This confirms full bidirectional isolation.

---

## Phase 6: Teardown feature branch

```bash
git checkout main
obproject-deploy --teardown --branch feature/test-isolation
```

### Verify cleanup

- Feature branch CronWorkflow removed
- Feature branch Sensors removed
- Feature branch workflow templates removed
- Prod resources **untouched**

---

## Summary of What This Proves

1. **`@project_trigger`** scopes external events to `prj.<project>.<branch>.<event>` —
   external publishers control which branch they target.
2. **`@trigger_on_finish`** is automatically branch-scoped — no configuration needed.
3. **`@schedule`** creates per-branch CronWorkflows that are isolated and cleaned up
   on teardown.
4. **CircleCI** deploys both prod and feature branches; branch isolation is handled
   by the Outerbounds platform, not CI/CD logic.
