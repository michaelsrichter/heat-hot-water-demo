# Privacy

The ADLS export uses an allowlist. It excludes:

- apartment;
- house number;
- street name;
- coordinates;
- 311 incident address;
- 311 resolution text;
- owner-person data;
- tenant data; and
- names, email addresses, and phone numbers.

The public app receives counts, building IDs, source dates, boroughs, rule
version, and safe process metadata. It does not receive a raw complaint problem,
raw violation candidate, or 311 resolution record.

The browser session ID is random and is not authentication. It stays in session
storage and is not persisted by the server.

Real public addresses remain blocked until privacy and template-owner review.

