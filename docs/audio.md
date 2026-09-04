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
It does not yet change the Windows spatial-sound mode.

This is an observation layer, not proof of the signal received or decoded by
the AVR. That comparison requires a receiver adapter capable of reporting its
input and output formats. AVR control remains planned and is not enabled.
Automatic processor selection also remains disabled until Orion can read the
current spatial mode, switch it through a reliable interface, and restore the
previous mode after playback or recovery.

## Delivery stages

### 1. Observe media and Windows — implemented

- Extract codec, channels, sample rate and bitrate from the selected stream
- Identify the default active Windows multimedia output endpoint
- Compare the configured receiver description with that endpoint
- Detect Dolby Access and DTS Sound Unbound for the current Windows account
- Report stream and Windows observations without changing the system

### 2. Define a vendor-neutral AVR contract

Adapters will expose only capabilities actually supported by a receiver:

- Availability and identity
- Power state
- Selected input
- Volume and mute state
- Listening/sound mode
- Reported input and output signal format where available

Orion’s cinema logic will call this common interface. Vendor command formats,
authentication and discovery remain inside individual adapters.

### 3. Add vendor adapters

- Denon/Marantz first, tested against the original system
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
- No automatic control until the user enables it
- Conservative volume handling with configurable limits
- Timeouts and fail-safe behaviour for network loss
- Credentials stored through Orion’s private settings layer
