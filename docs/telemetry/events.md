# Telemetry events

No app telemetry exporter is wired yet. When Application Insights is connected,
send only the events below.

| Event | Trigger | Safe properties | Destination |
|---|---|---|---|
| `page.view` | Route shown | route, mode, trace ID | App Insights |
| `demo.scenario.select` | Saved scenario selected | scenario ID, rule version | App Insights |
| `demo.review.start` | Review starts | scenario ID, mode, trace ID | App Insights |
| `demo.review.complete` | Review completes | status, elapsed time, result count, rule version, trace ID | App Insights |
| `demo.review.rate_limited` | Limit reached | mode, trace ID | App Insights |
| `demo.source.degraded` | Source stale or incomplete | source ID, status, trace ID | App Insights |

Never send prompts, answers, building labels, raw records, credentials, document
text, query text, or full workload principal IDs.

