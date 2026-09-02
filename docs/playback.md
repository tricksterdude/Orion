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

### AIOStreams and Stremio

Orion reads the selected AIOStreams playback from Stremio's local metadata endpoint. Open the AIOStreams service page in Orion and use **Launch Stremio** so that endpoint is enabled. Orion does not silently start or close Stremio.

If Stremio is already open without playback detection, close it first and then use the launch action on the AIOStreams service page. UsenetStreamer detection remains independent and continues to use its Docker stream events.

Playback metadata is kept in session history even when Orion deliberately blocks a display change because a recovery checkpoint could not be created.

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
