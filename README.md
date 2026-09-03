# Orion

> A local-first Home Cinema Operations Centre for Windows.

Orion watches supported media players, analyses the selected stream,
switches the display to the content frame rate, and safely restores the
desktop when playback ends. Its local dashboard also discovers and manages
the Docker services that support the cinema system.

## Available today

### Playback and cinema mode

- AIOStreams/Stremio and UsenetStreamer playback detection
- FFprobe stream analysis for resolution, codec and frame rate
- Automatic display refresh-rate switching
- Restoration to the configured desktop mode when playback ends
- Crash-safe display recovery after an interrupted Orion session
- A maximum of 15 local playback-history entries with individual and bulk
  deletion

### Operations

- Responsive local dashboard and per-service pages
- Docker service discovery and safe registration
- Service health, start, stop and restart controls
- Container update detection and controlled one-click updates
- AIOStreams Tamtaro template update assistance
- Privacy-safe health diagnostics and downloadable support report
- Windows pull-request regression checks for critical workflows

### Safety

- Local-only web server on `127.0.0.1`
- Per-process form tokens for actions that change state
- Atomic configuration updates with backups where appropriate
- Windows-protected storage for private settings
- Display recovery checkpoints before temporary mode changes

## Evolution roadmap

The roadmap is ordered by dependency and risk rather than by marketing
version numbers.

### 1. Secure setup and reusable profiles — in progress

- Move private values out of tracked configuration files
- Manage encrypted credentials from Orion’s Settings page
- Add a first-run setup wizard
- Make Docker container names, ports and service addresses configurable
- Add import/export for non-secret system profiles
- Validate a profile before applying it and explain required fixes clearly

### 2. Complete playback verification

- Extract audio codec, channel layout and bitrate
- Improve HDR and Dolby Vision identification
- Verify the active Windows audio device and HDMI route
- Compare expected media properties with the actual display and audio state
- Surface mismatches in the live session and playback history

### 3. Vendor-neutral AVR control

- Define one AVR capability interface for power, input, volume, mute,
  listening mode and status
- Add network discovery and a safe manual-address fallback
- Build Denon/Marantz as the first adapter, then add Yamaha, Onkyo/Pioneer
  and other vendors without changing Orion’s cinema logic
- Allow read-only monitoring before users opt into control
- Restore AVR state after playback where that is safe and supported

### 4. More playback providers

- Add Nuvio Desktop for Windows through the existing playback-provider
  interface
- Retain Stremio/AIOStreams and UsenetStreamer as independent providers
- Add Jellyfin and Plex adapters after the provider contract is stable

### 5. Broader cinema hardware

- Display profiles and multi-display support
- Optional television adapters, beginning with LG OLED where useful
- Per-device capabilities so unsupported controls are never offered

### 6. Public application experience

- Guided installation and dependency checks
- Friendly desktop launcher and lifecycle controls
- User-defined services and container-update policies
- Portable documentation for different Windows, Docker and home-cinema
  arrangements
- Stable upgrade, backup and recovery path

### 7. Optional hybrid/self-hosted mode

- Keep playback detection, credentials and hardware control on a local
  Windows agent
- Add an optional self-hosted control plane suitable for Oracle Cloud or
  another private server
- Provide remote status and notifications through authenticated,
  user-controlled connections
- Never require cloud access for local cinema operation

## Design principles

- Local operation remains fully useful without a cloud service.
- Private credentials are encrypted and excluded from diagnostics and Git.
- Hardware integrations advertise capabilities instead of assuming a brand.
- External actions are explicit, validated and recoverable where possible.
- New players and devices are adapters around stable Orion contracts.
- Configuration should describe the user’s system; the code should not be
  tied to one installation.

See [the architecture guide](docs/architecture.md) for subsystem boundaries
and [the audio roadmap](docs/audio.md) for the planned AVR design.
