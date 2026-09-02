# Health and Diagnostics

Orion's diagnostics page provides a read-only readiness check for the
components used during playback. Open **Health & Diagnostics** from the
homepage to see the overall state and the result of each check.

## States

- **Healthy** means every check completed successfully.
- **Warning** means Orion can continue running, but a configured service or
  background-process check may need attention.
- **Action required** means a dependency needed for playback detection,
  Docker management, or display switching is unavailable.

## Checks

Orion checks:

- Configuration files can be read as valid JSON.
- Docker Desktop is available to Orion's background process.
- FFprobe is available for playback metadata analysis.
- The current Windows display mode can be read.
- Only one independent Orion runtime is active.
- Stremio is installed or AIOStreams detection is ready when Stremio is open.
- Configured service health endpoints are responding.

The checks do not start or stop containers, launch or close Stremio, change
the display mode, or modify Orion's configuration.

Results are cached briefly so normal homepage refreshes do not repeatedly
start dependency checks. Use **Run checks again** on the diagnostics page to
request a fresh result.

## Safe diagnostic report

The diagnostics page can copy or download a text report for troubleshooting.
The report contains Orion's version, the overall result, check summaries, and
suggested actions. It intentionally excludes:

- Configuration values and API keys
- Passwords, tokens, and other credentials
- Windows account names and host addresses
- Stream URLs and source hosts
- Playback titles and playback history

Review the report before sharing it, just as you would any diagnostic file.

## Pull-request checks

The Windows test workflow runs a curated regression suite for changes proposed
against `main`. It includes dependency resolution, diagnostics, web rendering,
single-instance protection, Stremio compatibility, playback history, service
discovery, and a simulated playback cycle. The simulated test never changes a
real display or Docker container.
