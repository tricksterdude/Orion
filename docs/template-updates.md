# AIOStreams template updates

Orion treats AIOStreams application updates and configuration-template
updates as separate operations.

- A container update replaces the AIOStreams Docker image.
- A template update changes the saved filtering, sorting, formatter and
  variant choices inside an AIOStreams configuration.

## Linking a configuration

Open the AIOStreams service page in Orion and use **Link securely** once.
Enter the UUID and password for the saved AIOStreams configuration.

Newer AIOStreams versions return a revocable remembered-session token. Orion
protects that token with Windows Data Protection API (DPAPI), which binds it
to the current Windows account. AIOStreams 2.33.x does not provide remembered
configuration sessions, so Orion instead protects the configuration password
with DPAPI. The password is never written as readable text and cannot be
decrypted by another Windows account.

The link can be removed at any time from the same service page.

## Installing an update

Orion compares the version recorded in the configuration's
`appliedTemplates` entry with the current public Tamtaro Complete template.
When a newer version exists, **Update template** creates an authenticated
local AIOStreams session and opens its import wizard with the correct template
selected.

AIOStreams 2.33.x predates secure remembered configuration sessions. Orion
labels its action **Prepare update** and uses the safe order required by that
version:

1. In **Confirm Import**, choose **OK**, not **Use This Template Now**. This
   refreshes the browser's trusted copy of the template without applying it.
2. Unlock the existing configuration in AIOStreams once.
3. Use the template-update prompt that AIOStreams displays. At this point the
   current services and saved template answers are available and preselected.

Orion never puts the legacy configuration password in a browser URL. A truly
password-free handoff therefore requires an AIOStreams version that supports
remembered configuration sessions; Orion switches to that flow automatically
when the capability is available.

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
- The configuration password is never stored as readable text, logged or
  placed in a URL.
- On AIOStreams 2.33.x, Orion clearly directs the user to unlock the existing
  configuration before starting template application, preventing an empty
  service selection from replacing the user's saved choices when the documented
  flow is followed.
