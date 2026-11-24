# Strategy interface views

This page uses rebuilt HTML views instead of raw portal screenshots. The views
show the current model, dashboard totals, and refresh settings without exposing
connector secrets.

## Why use rebuilt views

A raw screenshot becomes hard to read on a phone and can include private
connection details. These views keep only the facts that help explain the demo.
They are not live Strategy screens.

## Mosaic model

The Heat and Hot Water Review Model has four ADLS source tables. They share
`building_id` and follow the Borough-to-Building relationship.

- Buildings are the shared location record.
- Complaint problems remain one row per problem.
- Candidate violations remain provisional.
- 311 requests remain supporting context.

## Reconciled dashboard

The dashboard counts distinct complaints and candidate violations by borough.
The HTML chart on this page is rebuilt from the current governed pipeline
manifest.

The candidate violation screen is not proof that a complaint caused a
violation. It is a queue for staff review.

## Scheduled refresh

Strategy runs **Heat and Hot Water Daily Refresh** on a Daily schedule. It
replaces data from all four one-file ADLS folders.

The stable path for each table does not change between runs:

- `strategy-buildings/`
- `strategy-complaints/`
- `strategy-violations/`
- `strategy-requests-311/`

## Screenshot rule

Do not capture a storage key, Strategy password, OAuth secret, or callback
token. If a raw screen is needed later, crop or hide every connection and
identity detail before publishing it.
