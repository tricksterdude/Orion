# Orion Architecture

## Overview

Orion is a local-first Windows application. Playback and hardware decisions
remain on the cinema PC even if an optional remote control plane is added in
the future.

```text
                         Orion runtime
                               |
         +---------------------+---------------------+
         |                     |                     |
     Local API            Playback pipeline      Operations
         |                     |                     |
 Dashboard/settings      Provider adapters       Docker services
 History/diagnostics     FFprobe analysis        Health and updates
         |                     |
 Encrypted secrets       Cinema coordinator
                               |
                    +----------+----------+
                    |                     |
              Display adapter       Audio/AVR adapters
```

## Current subsystems

### Local API and dashboard

The Flask server listens on `127.0.0.1`. It renders the dashboard, service
pages, settings, diagnostics and playback history. State-changing forms use
per-process security tokens.

### Service operations

Configured Docker services are monitored through their Windows host
addresses. Orion can discover published containers, register them safely,
control an explicitly configured container, and perform guarded image
updates with configuration backups.

### Playback providers

Provider adapters translate player-specific observations into Orion’s common
playback model. AIOStreams/Stremio and UsenetStreamer are currently
supported. Nuvio Desktop is planned as another adapter rather than a separate
cinema engine.

### Technical analysis

FFprobe resolves the selected stream’s resolution, video codec, frame rate,
audio codec/profile, channel layout, sample rate and bitrate. The Windows
Core Audio observer reports the active default multimedia output without
changing it. A vendor-neutral receiver boundary supports optional read-only
Denon/Marantz monitoring while keeping its network protocol out of cinema
logic. Stronger signal-format and HDR/Dolby Vision identification remain
later analysis layers.

### Cinema and display

The cinema coordinator chooses a display refresh rate from the analysed
media. Orion saves a recovery checkpoint before switching and restores the
configured desktop baseline after normal, manual or interrupted playback
termination.

### Private settings

Non-secret defaults remain in tracked JSON configuration. Private settings
are encrypted with Windows Data Protection API for the current Windows
account and stored only in ignored local data files. They are never rendered
back into a page or included in diagnostic reports.

## Planned extension contracts

### AVR adapters

Cinema logic will depend on a common AVR interface, not a Denon-specific
implementation. Each adapter will report supported capabilities such as
status, power, input, mute, volume and listening mode. Denon/Marantz is the
first intended adapter because it can be tested on the original system.

### Installation profiles

Service identities, ports, player choices and display baselines are stored
in ignored local profile files under `data/profile`. Existing installations
are migrated from the legacy tracked files on first use. Profiles can be
validated, backed up, imported and exported; exports omit secrets,
machine-private playback history and recovery state. Future device adapters
will extend this versioned schema.

### Optional remote control plane

A later self-hosted component may provide remote status and notifications.
The local Windows agent will retain all playback detection and hardware
control. Loss of the remote service must not interrupt local playback.

## Design rules

- One responsibility per subsystem
- Stable common models with replaceable provider/device adapters
- Capability checks before offering hardware actions
- Local-only and read-only behaviour by default
- Atomic writes and recovery data around risky state changes
- Secrets excluded from source control, templates, URLs, logs and reports
- External dependencies isolated behind small, testable boundaries
