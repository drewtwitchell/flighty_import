# Flighty Email Forwarder

Automatically find flight booking confirmation emails in your inbox and forward them to [Flighty](https://flightyapp.com) for automatic trip tracking.

## Features

- Connects to any email provider (AOL, Gmail, Yahoo, Outlook, iCloud, or custom IMAP)
- Detects flight confirmations from 15+ airlines
- Forwards emails to Flighty's import service
- Remembers processed emails to avoid duplicates
- Simple interactive setup - no coding required

## Supported Airlines

JetBlue, Delta, United, American Airlines, Southwest, Alaska Airlines, Spirit, Frontier, Hawaiian Airlines, Air Canada, British Airways, Lufthansa, Emirates, KLM, Air France, Qantas, Singapore Airlines, and generic flight confirmation emails.

## Requirements

- Python 3.6+
- An email account with IMAP access
- An App Password from your email provider (not your regular password)

## Installation

```bash
git clone https://github.com/yourusername/flighty_import.git
cd flighty_import
```

No additional dependencies required - uses only Python standard library.

## Setup

Run the interactive setup wizard:

```bash
python3 setup.py
```

The wizard will ask you for:
1. **Email provider** - Select from AOL, Gmail, Yahoo, Outlook, iCloud, or enter custom IMAP settings
2. **Email address** - Your full email address
3. **App Password** - A special password for third-party apps (see below)
4. **Flighty email** - Where to forward emails (default: `track@my.flightyapp.com`)
5. **Folders to search** - Which email folders to scan (default: INBOX)
6. **Time range** - How far back to search for emails

### Getting an App Password

Most email providers require an "App Password" instead of your regular password:

| Provider | How to get App Password |
|----------|------------------------|
| AOL | [AOL Account Security](https://login.aol.com/account/security) → Generate app password |
| Gmail | [Google App Passwords](https://myaccount.google.com/apppasswords) (requires 2FA) |
| Yahoo | [Yahoo Account Security](https://login.yahoo.com/account/security) → Generate app password |
| Outlook | May work with regular password, or use [Microsoft Account](https://account.microsoft.com/security) |
| iCloud | [Apple ID](https://appleid.apple.com/account/manage) → App-Specific Passwords |

## Usage

### Test Mode (Dry Run)

See what emails would be forwarded without actually sending anything:

```bash
python3 run.py --dry-run
```

### Normal Mode

Find and forward flight emails to Flighty:

```bash
python3 run.py
```

### Re-run Setup

```bash
python3 setup.py
# or
python3 run.py --setup
```

### Help

```bash
python3 run.py --help
```

## Automation (Optional)

To run automatically on a schedule, add a cron job:

```bash
# Edit crontab
crontab -e

# Run every hour
0 * * * * cd /path/to/flighty_import && python3 run.py >> forwarder.log 2>&1

# Run every 6 hours
0 */6 * * * cd /path/to/flighty_import && python3 run.py >> forwarder.log 2>&1
```

## Files

| File | Description |
|------|-------------|
| `setup.py` | Interactive setup wizard |
| `run.py` | Main script to find and forward emails |
| `config.json` | Your configuration (created by setup) |
| `processed_emails.json` | Tracks which emails have been forwarded |

## Privacy & Security

- Your credentials are stored locally in `config.json`
- No data is sent anywhere except to your email provider and Flighty
- Add `config.json` to `.gitignore` if you plan to share your fork

## Troubleshooting

**Login failed**
- Make sure you're using an App Password, not your regular password
- Check that IMAP is enabled in your email settings

**No emails found**
- Try increasing the "days back" setting
- Check that you're searching the correct folder
- Run with `--dry-run` to see what's being detected

**Emails not appearing in Flighty**
- Verify the forwarding email is correct (`track@my.flightyapp.com`)
- Check that Flighty email import is enabled in the app

## License

MIT License - feel free to modify and share.
