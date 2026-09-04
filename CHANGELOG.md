# Changelog

All notable changes to Orion will be documented in this file.

The format is based on **Keep a Changelog** and follows **Semantic Versioning** where practical.

---

## [Unreleased]

### Added

- Vendor-neutral, read-only AV receiver adapter contract
- Optional Denon/Marantz network status monitoring for power, input, volume,
  mute and sound mode
- Expected-versus-reported immersive audio comparison in playback history
- Read-only FFprobe audio metadata for AIOStreams and UsenetStreamer playback
- Default Windows audio-output observation and configured-receiver diagnostics
- Read-only Dolby Access and DTS Sound Unbound detection with content mapping
- Stream audio and observed Windows output details in playback history
- Guided system setup for display, playback-provider and content-directed audio
- Stream-derived playback refresh with only the desktop restoration rate configured
- Local installation profiles that survive repository updates
- Validated non-secret profile import/export with pre-change ZIP backups
- Windows-protected storage and a local Settings page for private values
- Roadmap architecture for reusable profiles, vendor-neutral AVR adapters,
  Nuvio Desktop and an optional self-hosted control plane

- Atomic display recovery checkpoints before cinema-mode switching
- Automatic display restoration after an interrupted Orion session
- Homepage recovery and failure status messages
- Fail-closed display switching when recovery state cannot be saved
- Existing MediaProfile desktop baseline kept independent of temporary stream FPS
- User-controlled Stremio launch with AIOStreams playback detection enabled
- Homepage health indicator and read-only system diagnostics page
- Safe diagnostic reports that exclude private configuration and playback data
- Windows pull-request regression checks for critical Orion workflows
- Simulated playback lifecycle coverage from 120 Hz through cinema mode and restoration
- Tamtaro AIOStreams template version detection on the AIOStreams service page
- One-time secure AIOStreams configuration linking using Windows-protected credentials
- Authenticated template update launch with the latest Tamtaro template preselected

### Fixed

- Removed the TMDb API key from tracked application configuration
- Missing TMDb credentials no longer cause playback metadata lookup errors

- Playback metadata is retained when display switching is safely blocked
- Console and background launchers now enforce the same single Orion instance
- AIOStreams service page reports whether Stremio playback detection is ready
- Updated Stremio WebView2 security requirements are included when launching playback detection
- Background playback analysis resolves per-user WinGet FFprobe installations
- AIOStreams 2.33 template updates now guide users through loading the existing
  configuration before application so saved services are preselected
- Playback detection accepts streams served by Orion's configured local
  AIOStreams service while continuing to ignore unrelated local services

---

## [0.8.0] - 2026-08-04

### Summary

This release establishes Orion's new playback architecture and completes the foundation for Orion's cinema engine.

Orion can now detect playback, identify media selected through AIOStreams, retrieve TMDb metadata, perform technical analysis, analyse the optimal display mode, and maintain a shared playback context throughout the application.

---

### Added

#### Core

- OrionEngine
- MovieContext
- PlaybackSession
- MediaSession
- ProviderManager
- Configuration management

#### Playback

- Playback detection
- Playback session lifecycle
- Playback start/stop monitoring
- AIOStreams integration

#### Metadata

- TMDb API integration
- IMDb lookup
- Movie metadata model
- Automatic poster and backdrop retrieval

#### Technical Analysis

- TechnicalManager
- TechnicalExtractor
- TechnicalMetadata model

(Currently uses placeholder values ready for MediaInfo and FFprobe.)

#### Cinema

- CinemaEngine
- CinemaSession
- Display analysis
- Refresh-rate recommendation engine

#### Display

- Display mode detection
- Display restore system
- Display switching framework

#### Events

- MovieContext
- Event-driven playback pipeline
- MediaSession subscriptions

#### Diagnostics

- System dashboard
- Docker service monitoring
- Service health checks
- Hardware detection
- Display detection
- Orion Doctor
- Recommendation engine

---

### Changed

- Introduced OrionEngine as the central orchestration layer.
- Introduced MovieContext as the shared playback model.
- PlaybackSession now owns the active playback context.
- Runtime responsibilities have been simplified.
- Managers are being standardised around the `analyse(context)` pattern.
- Improved modular architecture throughout the application.
- Reduced duplicated application state.

---

### Fixed

- Playback pipeline stability
- Movie detection workflow
- TMDb metadata integration
- Technical metadata processing
- Display recommendation workflow
- Runtime architecture consistency

---

## Current Workflow

Playback Detection

↓

Movie Selection

↓

TMDb Metadata

↓

Technical Analysis

↓

Cinema Analysis

↓

Display Recommendation

↓

Playback End

↓

Display Restore

---

## Known Limitations

- Technical metadata currently uses placeholder values.
- Frame-rate detection is currently hard-coded to 23.976 fps.
- TV episode metadata requires additional handling.
- Playback recovery after Orion starts mid-playback is not yet implemented.
- Automatic Windows refresh-rate switching has not yet been enabled.

---

## Upcoming (0.9.0)

### Planned

- Playback recovery
- MediaInfo integration
- FFprobe integration
- Accurate FPS detection
- Automatic Windows refresh-rate switching
- HDR and Dolby Vision detection
- Audio codec detection
- TV episode support
- Live playback dashboard

---

## [0.9.0] - 2026-08-05

### Added

- Orion Engine introduced as the central orchestration layer
- Local Orion REST API
- Playback API endpoint (`POST /playback`)
- API controller architecture
- Playback request model
- API routing framework
- Engine package structure

### Changed

- Refactored runtime to use Orion Engine
- Simplified playback pipeline
- Consolidated engine architecture
- Prepared playback providers for API-driven integration

### Fixed

- Runtime engine duplication
- Package import structure
- Playback session flow

**Project Status**

Foundation Complete ✅
