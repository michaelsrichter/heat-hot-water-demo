# Secrets

The public repository and app settings contain no storage keys, client secrets,
passwords, or access tokens.

The application reads and writes ADLS with Microsoft Entra managed identity.
Shared-key storage authentication is disabled in the public Bicep deployment.

An external Strategy connector is an optional, environment-specific
integration. Configure it outside this repository with the organization's
approved identity and secret-management controls. Never copy connector values,
screenshots of credential screens, or temporary passwords into source control.

