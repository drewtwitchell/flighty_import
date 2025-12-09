#!/usr/bin/env python3
"""
Flighty Email Forwarder - Main Runner

Usage:
    python3 run.py              # Run normally
    python3 run.py --dry-run    # Test without forwarding
    python3 run.py --setup      # Run setup wizard
"""

import imaplib
import smtplib
import email
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import re
import json
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path

CONFIG_FILE = Path(__file__).parent / "config.json"

# Airline patterns to detect flight confirmation emails
AIRLINE_PATTERNS = [
    {
        "name": "JetBlue",
        "from_patterns": [r"jetblue", r"@.*jetblue\.com"],
        "subject_patterns": [r"booking confirmation", r"itinerary", r"flight confirmation"]
    },
    {
        "name": "Delta",
        "from_patterns": [r"delta", r"@.*delta\.com"],
        "subject_patterns": [r"ereceipt", r"trip confirmation", r"itinerary", r"booking confirmation"]
    },
    {
        "name": "United",
        "from_patterns": [r"united", r"@.*united\.com"],
        "subject_patterns": [r"confirmation", r"itinerary", r"trip details"]
    },
    {
        "name": "American Airlines",
        "from_patterns": [r"american", r"@.*aa\.com", r"americanairlines"],
        "subject_patterns": [r"reservation", r"confirmation", r"itinerary"]
    },
    {
        "name": "Southwest",
        "from_patterns": [r"southwest", r"@.*southwest\.com"],
        "subject_patterns": [r"confirmation", r"itinerary", r"trip"]
    },
    {
        "name": "Alaska Airlines",
        "from_patterns": [r"alaska", r"@.*alaskaair\.com"],
        "subject_patterns": [r"confirmation", r"itinerary"]
    },
    {
        "name": "Spirit",
        "from_patterns": [r"spirit", r"@.*spirit\.com"],
        "subject_patterns": [r"confirmation", r"itinerary"]
    },
    {
        "name": "Frontier",
        "from_patterns": [r"frontier", r"@.*flyfrontier\.com"],
        "subject_patterns": [r"confirmation", r"itinerary"]
    },
    {
        "name": "Hawaiian Airlines",
        "from_patterns": [r"hawaiian", r"@.*hawaiianairlines\.com"],
        "subject_patterns": [r"confirmation", r"itinerary"]
    },
    {
        "name": "Air Canada",
        "from_patterns": [r"aircanada", r"@.*aircanada\.com"],
        "subject_patterns": [r"confirmation", r"itinerary"]
    },
    {
        "name": "British Airways",
        "from_patterns": [r"british", r"@.*britishairways\.com", r"@.*ba\.com"],
        "subject_patterns": [r"confirmation", r"booking", r"itinerary"]
    },
    {
        "name": "Lufthansa",
        "from_patterns": [r"lufthansa", r"@.*lufthansa\.com"],
        "subject_patterns": [r"confirmation", r"booking"]
    },
    {
        "name": "Emirates",
        "from_patterns": [r"emirates", r"@.*emirates\.com"],
        "subject_patterns": [r"confirmation", r"booking", r"itinerary"]
    },
    {
        "name": "KLM",
        "from_patterns": [r"klm", r"@.*klm\.com"],
        "subject_patterns": [r"confirmation", r"booking", r"itinerary"]
    },
    {
        "name": "Air France",
        "from_patterns": [r"airfrance", r"@.*airfrance\.com"],
        "subject_patterns": [r"confirmation", r"booking", r"itinerary"]
    },
    {
        "name": "Qantas",
        "from_patterns": [r"qantas", r"@.*qantas\.com"],
        "subject_patterns": [r"confirmation", r"booking", r"itinerary"]
    },
    {
        "name": "Singapore Airlines",
        "from_patterns": [r"singapore", r"@.*singaporeair\.com"],
        "subject_patterns": [r"confirmation", r"booking", r"itinerary"]
    },
    # Generic patterns - match any sender with flight-related subject
    {
        "name": "Generic Flight",
        "from_patterns": [r".*"],
        "subject_patterns": [
            r"flight.*confirmation",
            r"booking.*confirmation.*flight",
            r"e-?ticket",
            r"itinerary.*flight",
            r"your.*trip.*confirmation",
            r"airline.*confirmation"
        ]
    }
]


def load_config():
    """Load configuration from file."""
    if not CONFIG_FILE.exists():
        return None

    with open(CONFIG_FILE, 'r') as f:
        return json.load(f)


def load_processed_emails(config):
    """Load list of already processed email IDs."""
    processed_file = Path(__file__).parent / config.get("processed_file", "processed_emails.json")
    if processed_file.exists():
        with open(processed_file, 'r') as f:
            return set(json.load(f))
    return set()


def save_processed_emails(config, processed_ids):
    """Save list of processed email IDs."""
    processed_file = Path(__file__).parent / config.get("processed_file", "processed_emails.json")
    with open(processed_file, 'w') as f:
        json.dump(list(processed_ids), f)


def is_flight_email(from_addr, subject):
    """Check if an email appears to be a flight confirmation."""
    from_addr = from_addr.lower() if from_addr else ""
    subject = subject.lower() if subject else ""

    for airline in AIRLINE_PATTERNS:
        from_match = any(re.search(pattern, from_addr, re.IGNORECASE)
                        for pattern in airline["from_patterns"])

        subject_match = any(re.search(pattern, subject, re.IGNORECASE)
                           for pattern in airline["subject_patterns"])

        if airline["name"] == "Generic Flight":
            if subject_match:
                return True, airline["name"]
        elif from_match and subject_match:
            return True, airline["name"]

    return False, None


def get_email_body(msg):
    """Extract the email body."""
    body = ""
    html_body = ""

    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition", ""))

            if "attachment" not in content_disposition:
                if content_type == "text/plain":
                    try:
                        body = part.get_payload(decode=True).decode('utf-8', errors='replace')
                    except:
                        pass
                elif content_type == "text/html":
                    try:
                        html_body = part.get_payload(decode=True).decode('utf-8', errors='replace')
                    except:
                        pass
    else:
        content_type = msg.get_content_type()
        try:
            payload = msg.get_payload(decode=True).decode('utf-8', errors='replace')
            if content_type == "text/plain":
                body = payload
            elif content_type == "text/html":
                html_body = payload
        except:
            pass

    return body, html_body


def forward_email(config, original_msg, from_addr, subject):
    """Forward an email to Flighty."""
    forward_msg = MIMEMultipart('mixed')
    forward_msg['From'] = config['email']
    forward_msg['To'] = config['flighty_email']
    forward_msg['Subject'] = f"Fwd: {subject}"

    body, html_body = get_email_body(original_msg)

    forward_text = f"""
---------- Forwarded message ---------
From: {from_addr}
Date: {original_msg.get('Date', 'Unknown')}
Subject: {subject}
To: {original_msg.get('To', 'Unknown')}

"""

    if body:
        forward_text += body
        text_part = MIMEText(forward_text, 'plain')
        forward_msg.attach(text_part)

    if html_body:
        html_forward = f"""
<div style="border-left: 2px solid #ccc; padding-left: 10px; margin: 10px 0;">
<p><strong>---------- Forwarded message ---------</strong></p>
<p>From: {from_addr}<br>
Date: {original_msg.get('Date', 'Unknown')}<br>
Subject: {subject}<br>
To: {original_msg.get('To', 'Unknown')}</p>
</div>
{html_body}
"""
        html_part = MIMEText(html_forward, 'html')
        forward_msg.attach(html_part)

    if original_msg.is_multipart():
        for part in original_msg.walk():
            content_disposition = str(part.get("Content-Disposition", ""))
            if "attachment" in content_disposition:
                forward_msg.attach(part)

    try:
        with smtplib.SMTP(config['smtp_server'], config['smtp_port']) as server:
            server.starttls()
            server.login(config['email'], config['password'])
            server.send_message(forward_msg)
        return True
    except Exception as e:
        print(f"    Error sending: {e}")
        return False


def connect_imap(config):
    """Connect to the IMAP server."""
    try:
        mail = imaplib.IMAP4_SSL(config['imap_server'], config['imap_port'])
        mail.login(config['email'], config['password'])
        return mail
    except imaplib.IMAP4.error as e:
        print(f"\nLogin failed: {e}")
        print("\nMake sure you're using an App Password, not your regular password.")
        print("Run 'python3 setup.py' to reconfigure.")
        return None


def search_folder(mail, config, folder, processed_ids, dry_run):
    """Search a single folder for flight emails."""
    try:
        result, _ = mail.select(folder)
        if result != 'OK':
            print(f"  Could not open folder: {folder}")
            return 0, 0, processed_ids
    except:
        print(f"  Could not open folder: {folder}")
        return 0, 0, processed_ids

    since_date = (datetime.now() - timedelta(days=config['days_back'])).strftime("%d-%b-%Y")
    result, data = mail.search(None, f'(SINCE {since_date})')

    if result != 'OK':
        return 0, 0, processed_ids

    email_ids = data[0].split()
    found = 0
    forwarded = 0

    for email_id in email_ids:
        email_id_str = f"{folder}:{email_id.decode()}"

        if email_id_str in processed_ids:
            continue

        result, msg_data = mail.fetch(email_id, '(RFC822)')
        if result != 'OK':
            continue

        raw_email = msg_data[0][1]
        msg = email.message_from_bytes(raw_email)

        from_addr = msg.get('From', '')
        subject = msg.get('Subject', '')

        if subject:
            decoded_parts = email.header.decode_header(subject)
            subject = ''.join(
                part.decode(charset or 'utf-8') if isinstance(part, bytes) else part
                for part, charset in decoded_parts
            )

        is_flight, airline = is_flight_email(from_addr, subject)

        if is_flight:
            found += 1
            print(f"\n  {'[DRY RUN] ' if dry_run else ''}Found: {airline}")
            print(f"    From: {from_addr[:60]}...")
            print(f"    Subject: {subject[:60]}...")

            if not dry_run:
                if forward_email(config, msg, from_addr, subject):
                    print(f"    -> Forwarded to Flighty")
                    forwarded += 1
                    processed_ids.add(email_id_str)

                    if config.get('mark_as_read'):
                        mail.store(email_id, '+FLAGS', '\\Seen')
            else:
                processed_ids.add(email_id_str)
                forwarded += 1

    return found, forwarded, processed_ids


def run(dry_run=False):
    """Main run function."""
    config = load_config()

    if not config:
        print("No configuration found!")
        print("Run 'python3 setup.py' to set up your email.")
        return

    if not config.get('email') or not config.get('password'):
        print("Email or password not configured!")
        print("Run 'python3 setup.py' to set up your email.")
        return

    print()
    print("=" * 50)
    print("  Flighty Email Forwarder")
    print("=" * 50)
    print()
    print(f"  Account:     {config['email']}")
    print(f"  Forward to:  {config['flighty_email']}")
    print(f"  Days back:   {config['days_back']}")
    if dry_run:
        print(f"  Mode:        DRY RUN (no emails will be sent)")
    print()

    mail = connect_imap(config)
    if not mail:
        return

    try:
        processed_ids = load_processed_emails(config)
        folders = config.get('check_folders', ['INBOX'])

        total_found = 0
        total_forwarded = 0

        for folder in folders:
            print(f"Searching: {folder}")
            found, forwarded, processed_ids = search_folder(
                mail, config, folder, processed_ids, dry_run
            )
            total_found += found
            total_forwarded += forwarded

        if not dry_run:
            save_processed_emails(config, processed_ids)

        print()
        print("-" * 50)
        print(f"  Flight emails found:    {total_found}")
        if dry_run:
            print(f"  Would be forwarded:     {total_forwarded}")
        else:
            print(f"  Successfully forwarded: {total_forwarded}")
        print("-" * 50)
        print()

    finally:
        mail.logout()


def main():
    args = sys.argv[1:]

    if "--setup" in args or "-s" in args:
        os.system(f"python3 {Path(__file__).parent / 'setup.py'}")
        return

    dry_run = "--dry-run" in args or "-d" in args

    if "--help" in args or "-h" in args:
        print("""
Flighty Email Forwarder

Usage:
    python3 run.py              Run and forward flight emails
    python3 run.py --dry-run    Test without forwarding
    python3 run.py --setup      Run setup wizard
    python3 run.py --help       Show this help

First time? Run: python3 setup.py
""")
        return

    run(dry_run=dry_run)


if __name__ == "__main__":
    main()
