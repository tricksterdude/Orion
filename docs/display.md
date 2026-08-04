# Display Subsystem

## Purpose

The Display subsystem manages all interaction with Windows display devices.

Its primary responsibility is to ensure that the display configuration matches the requirements of the media being played.

---

## Current Features

- Display detection
- Resolution detection
- Refresh-rate detection

---

## Planned Features

- Display mode enumeration
- Safe refresh-rate switching
- Automatic display restoration
- HDR state verification
- Multi-monitor awareness

---

## Design

Only the Display Controller should be permitted to change Windows display settings.

Other Orion components request changes through the Display Controller.

This separation keeps display management isolated and easy to maintain.

---

## Long-Term Goal

Provide seamless display optimisation requiring no user interaction during playback.