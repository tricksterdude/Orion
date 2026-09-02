# AIOStreams template updates

Orion treats AIOStreams application updates and configuration-template
updates as separate operations.

- A container update replaces the AIOStreams Docker image.
- A template update changes the saved filtering, sorting, formatter and
  variant choices inside an AIOStreams configuration.

## Linking a configuration

Open the AIOStreams service page in Orion and use **Link securely** once.
Enter the UUID and password for the saved AIOStreams configuration. Orion
uses the password only for that request and never writes it to disk.

AIOStreams returns a revocable remembered-session token. Orion protects the
token with Windows Data Protection API (DPAPI), which binds it to the current
Windows account, and saves only the protected value.

The link can be removed at any time from the same service page.

## Installing an update

Orion compares the version recorded in the configuration's
`appliedTemplates` entry with the current public Tamtaro Complete template.
When a newer version exists, **Update template** creates an authenticated
local AIOStreams session and opens its import wizard with the correct template
selected.

The final review and save remain inside AIOStreams. This is intentional:
Tamtaro updates can introduce new choices or change filtering behaviour, so
Orion does not silently overwrite personalised settings.

## Safety boundaries

- Only the `tamtaro.complete` template from the official Tam-Taro GitHub
  repository is accepted.
- The downloaded file must remain on HTTPS, be valid JSON and stay below the
  configured size limit.
- Orion connects only to an AIOStreams instance on the local computer.
- Every link, unlink and update action requires Orion's per-process security
  token.
- The configuration password is never stored, logged or placed in a URL.
