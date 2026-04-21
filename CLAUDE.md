# Prod-Only Event Triggering

Production ML systems need to react to external signals (new data landed, model retrain requested, upstream pipeline completed) — but only the production deployment should respond. Feature branches should be isolated so development doesn't interfere with prod event processing.

This project demonstrates branch-scoped event triggering: the same flow code deploys to every branch, but events are namespaced per-branch so external systems can target production specifically.

## Architecture

```
ScheduledIngestFlow (@schedule weekday mornings)
  → publishes "ingest_complete" event
  → scoped to prj.prod_event_example.<branch>.ingest_complete

EventProcessorFlow (@project_trigger "external_signal")
  → listens for prj.prod_event_example.<branch>.external_signal
  → only the deployment matching the event's branch responds

ChainedReporterFlow (@trigger_on_finish EventProcessorFlow)
  → auto-triggers when EventProcessorFlow completes on same branch
  → accesses upstream results via current.trigger.run.data
```

## Platform features used

- **@project_trigger**: Branch-scoped event sensors — the key differentiator from `@trigger`
- **@trigger_on_finish**: Completion-based chaining (already branch-scoped in projects)
- **@schedule**: Cron-based scheduling, isolated per branch
- **prj.safe_publish_event()**: Programmatic event publishing from within flows
- **[dev-assets]**: Read production data from feature branches

## Flows

| Flow | Trigger | What it does |
|------|---------|-------------|
| ScheduledIngestFlow | `@schedule(cron="0 8 * * 1-5")` | Weekday morning data ingest, publishes `ingest_complete` |
| EventProcessorFlow | `@project_trigger(event="external_signal")` | Processes external events, branch-isolated |
| ChainedReporterFlow | `@trigger_on_finish(flow="EventProcessorFlow")` | Reports on processed events, accesses upstream artifacts |

## CI strategy

Deploy + teardown. All pushes trigger deploy (not just main — intentional, because the demo needs feature branch deployments to show branch isolation). On PR merge or branch delete, teardown removes the branch's Argo resources (CronWorkflows, Sensors, Workflows).

Uses `--from-obproject-toml` for auth. Teardown still extracts project name via `python3 tomllib` because `teardown-branch` doesn't support `--from-obproject-toml` yet.

## Run locally

```bash
python flows/scheduled_ingest/flow.py run
python flows/event_processor/flow.py run
# ChainedReporterFlow needs a trigger context — can't run standalone locally
```

## Event scoping explained

`@project_trigger` creates sensors scoped to `prj.<project>.<branch>.<event>`:
- Main: `prj.prod_event_example.main.external_signal`
- Feature: `prj.prod_event_example.my_feature.external_signal`

External systems target prod by publishing to the main-scoped event name. Feature branch sensors never see it. This is WHY you use `@project_trigger` instead of `@trigger` — plain `@trigger` would create sensors for the same global event name on every branch.

## Good to know

- `@trigger_on_finish` is already branch-scoped in projects — no extra config needed. It only fires when the upstream flow on the SAME branch completes.
- `@schedule` creates per-branch CronWorkflows. Every deployed branch gets its own schedule. If you want only main to run on schedule, use `obproject_deploy.toml` branch filtering (see ob-project-deploy-lifecycle).
- ChainedReporterFlow accesses upstream data via `current.trigger.run.data` — this is the completion-based pattern where you don't need explicit payloads.
