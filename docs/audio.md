# Audio and AVR subsystem

## Goal

Verify the audio path from the selected media through Windows and HDMI to an
AV receiver, then optionally coordinate the receiver as part of a cinema
session.

## Current status

The AIOStreams and UsenetStreamer probes now populate codec, profile, channel
layout, sample rate, audio bitrate and immersive-format hints from FFprobe.
Orion reads the default Windows multimedia output through the Core Audio API,
compares its name with the configured receiver description, and records the
observed endpoint with playback history.

Dolby Access and DTS Sound Unbound are treated as optional Windows processing
adapters, not AVR brands. Orion detects whether each app is installed and
maps Atmos or DTS:X content to the relevant processor in playback history.
Guided mode does not change the Windows spatial-sound mode. An explicitly
enabled automatic mode can coordinate the endpoint through separately
installed NirSoft helpers.

This is an observation layer, not proof of the signal received or decoded by
the AVR. That comparison requires a receiver adapter capable of reporting its
input and output formats. AVR control remains planned and is not enabled.
Receiver listening-mode observation is not proof of the exact input signal.
Orion therefore distinguishes an exact immersive mode from a compatible
Dolby or DTS family. A Denon without configured height speakers may report
`DOLBY AUDIO-DSUR` for the correct Dolby path instead of `DOLBY ATMOS`.

Windows' public Spatial Audio APIs let applications render spatial objects and
test whether spatial streams are available. Microsoft documents the selected
output format as a user-controlled endpoint setting; it does not publish an
application setter for switching between Dolby Access and DTS Sound Unbound.
Orion therefore does not use undocumented registry edits or simulated Settings
clicks for automatic switching. See Microsoft's
[Spatial Sound guidance](https://learn.microsoft.com/windows/win32/coreaudio/spatial-sound).

For users who opt in, Orion can use NirSoft SoundVolumeView to read the exact
current endpoint and spatial-format GUID, and SoundVolumeCommandLine's
documented `/SetSpatial` command to select the GUID required by the stream.
The tools are not bundled with Orion and must be installed separately from
NirSoft's [SoundVolumeView documentation](https://www.nirsoft.net/utils/sound_volume_view.html).
Orion looks for the two executables at these per-user locations:

- `%LOCALAPPDATA%\Orion\tools\SoundVolumeView\SoundVolumeView.exe`
- `%LOCALAPPDATA%\Orion\tools\SoundVolumeCommandLine\svcl.exe`

Orion writes an atomic recovery checkpoint first, changes only the active
default multimedia endpoint, verifies the selected GUID, and restores the
previous GUID after normal, manual, or interrupted playback termination.

While playback is active, Orion publishes a live audio-guidance state on the
homepage. It waits for the receiver mode to settle, identifies a confirmed
Atmos/DTS:X mismatch, names the installed processor suited to the stream, and
offers a protected button that opens the official `ms-settings:sound` page.
In guided mode the user still selects the endpoint's spatial format. In
automatic mode the panel reports the verified switch and falls back to the
same guided action if automation cannot be completed. The guidance disappears
when playback ends.

## Delivery stages

### 1. Observe media and Windows — implemented

- Extract codec, channels, sample rate and bitrate from the selected stream
- Identify the default active Windows multimedia output endpoint
- Compare the configured receiver description with that endpoint
- Detect Dolby Access and DTS Sound Unbound for the current Windows account
- Report stream and Windows observations without changing the system
- Guide confirmed mismatches through the supported Windows sound-settings page
- Optionally checkpoint, switch, verify and restore Atmos/DTS:X endpoint GUIDs
  with separately installed SoundVolume helpers

### 2. Define a vendor-neutral AVR contract — implemented

Adapters will expose only capabilities actually supported by a receiver:

- Availability and identity
- Power state
- Selected input
- Volume and mute state
- Listening/sound mode
- Reported input and output signal format where available

Orion’s cinema logic will call this common interface. Vendor command formats,
authentication and discovery remain inside individual adapters.

### 3. Add vendor adapters — Denon/Marantz observation implemented

- Denon/Marantz status is read through its documented network-control protocol
- The first adapter reports power, input, volume, mute and sound mode without
  sending state-changing commands
- Playback history distinguishes exact immersive modes, compatible Dolby/DTS
  family modes and confirmed cross-family mismatches
- Yamaha and Onkyo/Pioneer next where their network APIs permit
- Additional manufacturers without changes to the playback pipeline
- Manual IP configuration whenever automatic discovery is unavailable

### 4. Optional cinema coordination

- Let the user opt into power, input or listening-mode changes separately
- Record the previous receiver state before making a reversible change
- Restore only settings Orion changed and only when safe
- Keep read-only verification available when control is disabled

## Formats to recognise

- Dolby Digital and Dolby Digital Plus
- Dolby TrueHD and Dolby Atmos
- DTS, DTS-HD Master Audio and DTS:X
- PCM and multichannel PCM
- FLAC and other decoded formats exposed by the player

## Safety principles

- No assumption that every AVR supports every command
- Guided audio handling remains the default; automatic spatial switching is
  explicit and requires locally installed helpers
- Every automatic endpoint change is checkpointed, verified and recoverable
- Conservative volume handling with configurable limits
- Timeouts and fail-safe behaviour for network loss
- Credentials stored through Orion’s private settings layer
