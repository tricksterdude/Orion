# Display Subsystem

## Purpose

The Display subsystem manages all interaction with Windows display devices.

Its primary responsibility is to ensure that the display configuration matches the requirements of the media being played.

---

## Current Features

- Display detection
- Resolution detection
- Refresh-rate detection
- Safe refresh-rate switching
- Automatic display restoration
- Atomic crash-recovery checkpoints
- Startup recovery after interrupted cinema sessions

---

## Planned Features

- Display mode enumeration
- HDR state verification
- Multi-monitor awareness

---

## Recovery Safety

Before Orion can change the Windows display mode, it writes the
original mode to `data/display_recovery.json` using atomic file
replacement. If this checkpoint cannot be saved, Orion continues
monitoring playback but does not change the display.

After a normal playback session, Orion restores the original mode and
removes the checkpoint. If Orion is interrupted, the next startup reads
the checkpoint and attempts restoration before the API or playback
providers start. Failed recovery checkpoints are retained for retry and
reported on the homepage.

---

## Design

Only the Display Controller should be permitted to change Windows display settings.

Other Orion components request changes through the Display Controller.

This separation keeps display management isolated and easy to maintain.

---

## Long-Term Goal

Provide seamless display optimisation requiring no user interaction during playback.
