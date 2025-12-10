# Flighty Email Forwarder

Automatically find flight booking confirmation emails in your inbox and forward them to [Flighty](https://flightyapp.com) for automatic trip tracking.

## Features

- Connects to any email provider (AOL, Gmail, Yahoo, Outlook, iCloud, or custom IMAP)
- Detects flight confirmations from 15+ airlines
- Forwards emails to Flighty's import service
- **Smart deduplication** - tracks confirmation codes and flight details to avoid forwarding the same flight multiple times
- Allows booking changes through (same confirmation code with different flights)
- Simple interactive setup - no coding required

## Supported Airlines

JetBlue, Delta, United, American Airlines, Southwest, Alaska Airlines, Spirit, Frontier, Hawaiian Airlines, Air Canada, British Airways, Lufthansa, Emirates, KLM, Air France, Qantas, Singapore Airlines, and generic flight confirmation emails.

## Requirements

- Python 3.6+
- An email account with IMAP access
- An App Password from your email provider (not your regular password)

## Installation

```bash
git clone https://github.com/drewtwitchell/flighty_import.git
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

### Reset Processed Flights

If you want to re-process all flights (e.g., after fixing an issue):

```bash
python3 run.py --reset
```

### Help

```bash
python3 run.py --help
```

## How Deduplication Works

The script uses multiple methods to avoid forwarding duplicate flights:

1. **Confirmation Code Tracking** - Extracts airline confirmation codes (e.g., `DJWNTF`) from emails and tracks which codes have been forwarded
2. **Flight Change Detection** - If the same confirmation code appears with different flight numbers, it's treated as a booking change and forwarded
3. **Content Hashing** - Creates a fingerprint of email content to catch exact duplicates
4. **Email ID Tracking** - Remembers which specific emails have been processed

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
| `config.json` | Your configuration (created by setup, not tracked in git) |
| `processed_flights.json` | Tracks confirmation codes and processed flights (not tracked in git) |

## Privacy & Security

- Your credentials are stored locally in `config.json`
- No data is sent anywhere except to your email provider and Flighty
- Sensitive files (`config.json`, `processed_flights.json`) are excluded from git

## Troubleshooting

**Login failed**
- Make sure you're using an App Password, not your regular password
- Check that IMAP is enabled in your email settings

**No emails found**
- Try increasing the "days back" setting
- Check that you're searching the correct folder
- Run with `--dry-run` to see what's being detected

**Same flight forwarded multiple times**
- Run `python3 run.py --reset` to clear history and start fresh
- The script now tracks by confirmation code, not just email ID

**Emails not appearing in Flighty**
- Verify the forwarding email is correct (`track@my.flightyapp.com`)
- Check that Flighty email import is enabled in the app

## License

MIT License - feel free to modify and share.
