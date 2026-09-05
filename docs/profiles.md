# Local system profiles

Orion keeps installation-specific choices in `data/profile`, away from
tracked repository defaults. This allows the same application to support different Docker
containers, ports, displays and playback choices without forking the code.

## Local files

The first component that needs configuration copies the existing installation
into `data/profile`:

- `services.json` — monitored service names, containers, ports and addresses
- `providers.json` — enabled playback-provider adapters
- `media.json` — display baseline, automatic audio policy and player
- `setup.json` — whether the guided setup has been reviewed

The whole directory is ignored by Git. Existing installations keep their
current values during migration; new installations begin with neutral safe
defaults.

## Guided setup

Open **Setup** directly from the homepage. Orion detects the current Windows
resolution and refresh rate, default audio output, Stremio readiness, known
playback providers and published Docker services. On a new installation it
pre-fills safe detected values and preselects recognised cinema containers so
the whole local profile can be confirmed once. Existing completed profiles are
never overwritten by later detection.

Confirm that **Desktop Hz** is the normal non-playback refresh rate that Orion
must restore after playback. If playback is active while setup is opened,
Orion preserves the stored desktop baseline rather than treating the temporary
cinema refresh rate as a new default.
Movie and television refresh targets are not profile settings: Orion measures
each stream's FPS and selects the closest supported display mode for that
playback session.

Saving creates a timestamped ZIP backup, validates every field, writes the
local files atomically, and verifies the result. Restart Orion before the next
playback session so all runtime components reload the profile.

Receiver network monitoring is optional. Select a supported receiver family
and enter only a private/local IP address or host name. Orion's first
Denon/Marantz adapter sends documented status queries and does not expose
controls or change receiver state.

Docker services continue to be discovered and added from the homepage. Their
container names, ports and addresses are included in the local profile.
Unknown published containers remain unselected during onboarding and can be
added deliberately later.

## Export and import

The Settings page exports `orion-profile.json`. Its versioned, allow-listed
schema contains only:

- Media/display preferences
- Receiver description, optional local adapter/address, automatic
  content-directed audio and playback preferences
- Configured Docker service endpoints
- Enabled Orion playback providers

It does not include API keys, passwords, AIOStreams sessions, playback
history, recovery checkpoints or backup data.

Imports are limited to 256 KB. Orion validates the complete profile before
creating a backup and changing any local file. Unsupported providers,
malformed service URLs, invalid ports and duplicate services are rejected.
