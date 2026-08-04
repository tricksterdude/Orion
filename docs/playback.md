# Playback Subsystem

## Purpose

The Playback subsystem is responsible for detecting media playback and preparing the Home Cinema environment for optimal viewing.

---

## Responsibilities

- Detect playback sessions
- Track active playback
- Analyse media properties
- Coordinate the Cinema Engine
- Restore desktop settings after playback

---

## Planned Components

### Playback Session

Maintains information about the current playback session.

Stores:

- Title
- Resolution
- Frame rate
- HDR format
- Audio format

---

### Playback Detector

Detects when playback starts and stops.

Initially developed for Stremio but intended to support additional media players in the future.

---

### Cinema Engine

Coordinates playback optimisation.

Responsibilities include:

- Refresh-rate switching
- HDR verification
- Audio verification
- Desktop restoration

---

## Future Goals

- Automatic playback optimisation
- Playback history
- Playback statistics
- Multi-player support