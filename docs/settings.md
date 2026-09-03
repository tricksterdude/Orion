# Private settings

Orion’s `/settings` page manages private values without placing them in
tracked configuration files.

## Storage

- Values are encrypted with Windows Data Protection API (DPAPI).
- Encryption is tied to the Windows account that saved the value.
- The encrypted file is `data/secure_settings.json`.
- The file and its temporary replacement are ignored by Git.
- Orion never returns a saved value to the browser.

Tracked `config/settings.json` contains harmless application defaults only.

## TMDb setup

1. Create or rotate the TMDb API key in the TMDb account.
2. Open **Settings** from Orion’s homepage.
3. Enter the 32-character API key and choose **Save securely**.
4. Restart Orion before the next playback session so every runtime component
   reloads the new key.

The old key previously stored in the repository should be revoked because
removing it from the latest file does not erase it from historical commits.

## Backup and transfer

An encrypted settings file cannot be decrypted by a different Windows
account. Exported Orion profiles will intentionally omit it; private values
must be entered again on a new installation.
