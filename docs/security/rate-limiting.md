# Rate limiting

Practice review runs are limited to six starts per minute for each combination of
source address and random browser session ID. A request must name a saved
scenario. Arbitrary prompts and building IDs are not accepted.

The in-memory limit is suitable for local testing only. Before public release,
use a shared server-side store so the limit cannot be bypassed by starting a new
container replica.

The app must also enforce:

- maximum request bytes;
- maximum run duration;
- maximum records per run;
- maximum output and citation size;
- bounded concurrent runs; and
- a global quota with a server-enforced stop.

