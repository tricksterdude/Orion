# Orion Architecture

## Overview

Orion is built using a modular architecture where each subsystem has a single responsibility.

```
                 Orion

              Main Application
                     │
 ┌───────────────────┼───────────────────┐
 │                   │                   │
Dashboard        Diagnostics        Playback
 │                   │                   │
Services        Orion Doctor     Cinema Engine
 │                   │                   │
Docker          Health Score     Display Controller
 │                   │                   │
Health          Recommendations  Audio Manager
```

---

## Core Modules

### Dashboard

Displays the current health and status of the system.

---

### Service Manager

Maintains the list of monitored services.

Examples:

- UsenetStreamer
- NZBHydra2
- NZBDAV
- AIOStreams
- AIOMetadata

---

### Health Manager

Checks HTTP endpoints and measures:

- Availability
- Response time
- Status code

---

### Orion Doctor

Runs diagnostic checks against:

- Hardware
- Services
- System resources
- Playback components

Produces recommendations and a health score.

---

### Hardware Manager

Collects information about:

- CPU
- GPU
- Memory
- Operating System

---

### Display Manager

Reads information about the active display.

Examples:

- Resolution
- Refresh rate
- Display name

---

### Playback Subsystem

Currently provides:

- Playback session management
- Stremio process detection

Future versions will introduce the Cinema Engine, responsible for automatic playback optimisation.

---

## Design Principles

- Single Responsibility Principle
- Modular components
- Easy to test
- Easy to extend
- Minimal external dependencies