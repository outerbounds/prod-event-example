# Prod Event Example (prod_event_example)

Demonstrates branch-scoped event triggering where only the production
(main branch) deployment reacts to external signals. Shows the difference
between `@project_trigger`, `@trigger_on_finish`, `@schedule`, and `@trigger`.

## Platform Features Used

- **Events**: `@project_trigger(event="external_signal")` for branch-scoped external events; `prj.safe_publish_event("ingest_complete")` for internal events
- **Schedules**: `@schedule(cron="0 8 * * 1-5")` weekday morning ingest
- **Flow chaining**: `@trigger_on_finish(flow="EventProcessorFlow")` (auto branch-scoped)
- **Dev-assets**: `[dev-assets] branch = "main"` for cross-branch data reads

## Flows

| Flow | Trigger | Purpose |
|------|---------|---------|
| ScheduledIngestFlow | @schedule(cron) | Daily ingest, publishes `ingest_complete` event |
| EventProcessorFlow | @project_trigger(external_signal) | Processes external events, branch-isolated |
| ChainedReporterFlow | @trigger_on_finish(EventProcessor) | Reports after event processing |

## Event Scoping

`@project_trigger` creates sensors scoped to `prj.<project>.<branch>.<event>`:
- Main: `prj.prod_event_example.main.external_signal`
- Feature branch: `prj.prod_event_example.<branch>.external_signal`

External systems target prod by publishing to the `main` event name explicitly.

## Run Locally

```bash
cd prod-event-example
python flows/scheduled_ingest/flow.py run
python flows/event_processor/flow.py run
# chained_reporter requires an upstream run in Argo (uses current.trigger.run)
```

## Common Pitfalls

- `@trigger(event=...)` is NOT branch-scoped -- all branches react to the same event. Use `@project_trigger` instead.
- ChainedReporterFlow cannot run locally without a trigger context (`current.trigger.run` would be None)
- External event publishers must specify both project and branch to target the correct deployment
- See TESTING.md for the full verification plan including branch isolation tests
