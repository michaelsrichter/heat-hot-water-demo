# Morning decisions

These decisions block a public or scheduled release.

| Decision | Why it is needed | Current safe state |
|---|---|---|
| Who owns external connector credentials? | The public Bicep code does not provision a Strategy credential. | Configure the connector outside the repository under the organization's identity and secret controls. |
| Who approves the heat classification and review rule? | Text matching is not an approved heat class. | All candidates are `needs_review` and `needs_verification`. |
| Can the public UI name Strategy? | The EPS template normally prohibits partner names. | Current public UI stays generic; technical details name the architecture. |
| Can public pages show real building addresses? | Addresses may identify residents or owners. | ADLS and Strategy snapshot exclude addresses and apartments. |
| What is the hard monthly or run quota? | Budget alerts do not stop a workload. | USD 50 is a template alert, not an approved cap. |
| Who owns Strategy refresh, source updates, alerts, and archive retention? | A scheduled demo needs an operator. | The Daily Strategy refresh is active; source and archive operations remain operator-owned. |
| Which public repository name should be used? | Publication is separate from implementation. | Public source is maintained at `michaelsrichter/heat-hot-water-demo`. |
| Is official HPD subject-matter review available? | The model must not present a provisional rule as policy. | All candidate classifications route to human verification. |

