# Cinema Checkup

Cinema Checkup is Orion's one-button readiness preflight. It gathers the
existing system checks into one clear result before a film starts.

## What it checks

- The local system profile has been reviewed and confirmed
- Orion configuration, Docker, FFprobe and single-instance protection
- Configured cinema services and supported player detection
- The current Windows display matches the saved desktop restoration baseline
- No display or spatial-audio recovery checkpoint is still pending
- Automatic spatial-audio helpers are available when automatic mode is enabled
- The most recent completed playback confirmed display and audio restoration
- The configured Windows audio output and optional AVR monitor are available

## Safety

The checkup is read-only. It does not start a title, switch refresh rate,
change the Windows spatial format, control the AVR, or modify Docker. Orion
refuses to run it during active playback so that the temporary cinema state is
never mistaken for the normal desktop baseline.

Only the latest result is saved locally in `data/cinema_checkup.json`. The file
is excluded from Git and contains no credentials or playback URLs.

## Result meanings

- **Ready** means every check passed.
- **Ready with notes** means playback can usually proceed, but Orion has advice
  such as confirming setup or completing a first playback proof.
- **Needs attention** means a required component or recovery guarantee could
  not be verified. Follow the guidance shown for that check before playback.
