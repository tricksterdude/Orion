# Local system profiles

Orion keeps installation-specific choices in `data/profile`, away from
tracked repository defaults. This allows the same application to support different Docker
containers, ports, displays and playback choices without forking the code.

## Local files

The first component that needs configuration copies the existing installation
into `data/profile`:

- `services.json` — monitored service names, containers, ports and addresses
- `providers.json` — enabled playback-provider adapters
- `media.json` — display baseline, descriptive audio preferences and player
- `setup.json` — whether the guided setup has been reviewed

The whole directory is ignored by Git. Existing installations keep their
current values during migration; new installations begin with neutral safe
defaults.

## Guided setup

Open **Settings → Review setup**. Orion shows the current Windows resolution
and refresh rate alongside the stored profile. Confirm that **Desktop Hz** is
the normal non-playback refresh rate that Orion must restore after playback.

Saving creates a timestamped ZIP backup, validates every field, writes the
local files atomically, and verifies the result. Restart Orion before the next
playback session so all runtime components reload the profile.

Docker services continue to be discovered and added from the homepage. Their
container names, ports and addresses are included in the local profile.

## Export and import

The Settings page exports `orion-profile.json`. Its versioned, allow-listed
schema contains only:

- Media/display preferences
- Descriptive audio and playback preferences
- Configured Docker service endpoints
- Enabled Orion playback providers

It does not include API keys, passwords, AIOStreams sessions, playback
history, recovery checkpoints or backup data.

Imports are limited to 256 KB. Orion validates the complete profile before
creating a backup and changing any local file. Unsupported providers,
malformed service URLs, invalid ports and duplicate services are rejected.
