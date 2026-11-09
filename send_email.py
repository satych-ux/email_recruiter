#!/usr/bin/env python3
"""
Recruiter Email Automation Dispatcher
Sends a templated email with attachment via SMTP.
Supports config.json and Environment Variables (for Render/Cloud hosting).
"""

import os
import sys
import json
import smtplib
import argparse
from email.message import EmailMessage
import mimetypes

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")
DEFAULT_RESUME_PATH = os.path.join(BASE_DIR, "resume.pdf")

def load_config():
    config = {}
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                config = json.load(f)
        except Exception as e:
            print(f"Warning: Could not read config.json: {e}", file=sys.stderr)

    # Environment variables take precedence (ideal for Render/Cloud)
    return {
        "smtp_server": os.environ.get("SMTP_SERVER", config.get("smtp_server", "smtp.gmail.com")),
        "smtp_port": int(os.environ.get("SMTP_PORT", config.get("smtp_port", 587))),
        "sender_email": os.environ.get("SENDER_EMAIL", config.get("sender_email", "")).strip(),
        "sender_password": os.environ.get("SENDER_PASSWORD", config.get("sender_password", "")).strip().replace(" ", ""),
        "subject": os.environ.get("SUBJECT", config.get("subject", "Senior Flutter Engineer - Immediately Available to join | 6+ YOE")),
        "template": os.environ.get("TEMPLATE", config.get("template", "")),
        "attachment_path": os.environ.get("ATTACHMENT_PATH", config.get("attachment_path", DEFAULT_RESUME_PATH))
    }

def send_email_smtp(to_email, recipient_name=None, custom_subject=None, custom_body=None, custom_attachment=None):
    config = load_config()

    smtp_server = config.get("smtp_server")
    smtp_port = config.get("smtp_port")
    sender_email = config.get("sender_email")
    sender_password = config.get("sender_password")

    if not sender_email or not sender_password:
        print("Error: 'sender_email' and 'sender_password' must be configured in config.json or Environment Variables.", file=sys.stderr)
        return False

    subject = custom_subject or config.get("subject")
    body_template = custom_body or config.get("template", "")
    
    # Resolve attachment
    attachment_path = custom_attachment or config.get("attachment_path")
    if attachment_path:
        attachment_path = os.path.expanduser(attachment_path)
    if not attachment_path or not os.path.isfile(attachment_path):
        if os.path.isfile(DEFAULT_RESUME_PATH):
            attachment_path = DEFAULT_RESUME_PATH

    # Format template
    body = body_template
    if recipient_name and "{name}" in body:
        body = body.replace("{name}", recipient_name)
    elif "{name}" in body:
        body = body.replace("{name}", "")

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = to_email
    msg.set_content(body)

    # Attach file if found
    if attachment_path and os.path.isfile(attachment_path):
        ctype, encoding = mimetypes.guess_type(attachment_path)
        if ctype is None or encoding is not None:
            ctype = "application/octet-stream"
        maintype, subtype = ctype.split("/", 1)
        with open(attachment_path, "rb") as f:
            msg.add_attachment(
                f.read(),
                maintype=maintype,
                subtype=subtype,
                filename="Satyam_Chourasia_Flutter_Resume.pdf"
            )
        print(f"Attached resume from: {attachment_path}")
    else:
        print(f"Warning: No valid attachment file found. Sending without attachment.", file=sys.stderr)

    try:
        if smtp_port == 465:
            with smtplib.SMTP_SSL(smtp_server, smtp_port, timeout=15) as server:
                server.login(sender_email, sender_password)
                server.send_message(msg)
        else:
            with smtplib.SMTP(smtp_server, smtp_port, timeout=15) as server:
                server.ehlo()
                server.starttls()
                server.ehlo()
                server.login(sender_email, sender_password)
                server.send_message(msg)
        print(f"SUCCESS: Email successfully sent to {to_email}")
        return True
    except Exception as e:
        print(f"Error sending email: {e}", file=sys.stderr)
        return False

def main():
    parser = argparse.ArgumentParser(description="Send recruiter email with attachment via SMTP.")
    parser.add_argument("--to", required=True, help="Recipient recruiter email address")
    parser.add_argument("--name", default=None, help="Recruiter name if detected")
    parser.add_argument("--subject", default=None, help="Custom subject line")
    parser.add_argument("--attachment", default=None, help="Custom attachment path")
    args = parser.parse_args()

    success = send_email_smtp(
        to_email=args.to,
        recipient_name=args.name,
        custom_subject=args.subject,
        custom_attachment=args.attachment
    )
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()
