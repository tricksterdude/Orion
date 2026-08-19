# Changelog

All notable changes to Orion will be documented in this file.

The format is based on **Keep a Changelog** and follows **Semantic Versioning** where practical.

---

## [Unreleased]

### Added

- Atomic display recovery checkpoints before cinema-mode switching
- Automatic display restoration after an interrupted Orion session
- Homepage recovery and failure status messages
- Fail-closed display switching when recovery state cannot be saved
- Configured 120 Hz desktop baseline independent of temporary stream FPS

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
