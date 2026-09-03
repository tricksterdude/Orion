# Audio and AVR subsystem

## Goal

Verify the audio path from the selected media through Windows and HDMI to an
AV receiver, then optionally coordinate the receiver as part of a cinema
session.

## Current status

The common playback model already has fields for audio codec, channel layout
and bitrate, but current probes do not yet populate or verify them. AVR
control is planned and has not been implemented.

## Delivery stages

### 1. Observe media and Windows

- Extract codec, channels, sample rate and bitrate from the selected stream
- Identify the active Windows output endpoint
- Confirm that the expected HDMI device is active
- Report expected versus observed audio without changing the system

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
