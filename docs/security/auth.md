# Identity and access

Public visitors do not sign in.

## Azure writer

The ingestion process uses the developer or managed identity with Storage Blob
Data Contributor. It can write current and archive files.

## Strategy connector

The public source does not create or store a Strategy credential. A connector
must be configured by the deployment operator with an identity approved by the
organization. Connector names, resource IDs, users, and secrets remain outside
the repository.

## Shared-key protection

The Bicep deployment disables storage shared-key authentication. Public access
does not mean credential-free access: anonymous Blob access is off, and
Microsoft Entra role-based access controls the data plane.
