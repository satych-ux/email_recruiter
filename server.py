#!/usr/bin/env python3
"""
Lightweight Webhook Server for Recruiter Email Automation
Supports deployment on Render, Railway, or local Mac.
"""

import re
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from send_email import send_email_smtp

EMAIL_REGEX = re.compile(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+')

class WebhookHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({"status": "running", "service": "recruiter-mailer", "platform": "render"}).encode('utf-8'))

    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length).decode('utf-8', errors='ignore')

        target_email = None

        # Try parsing JSON
        try:
            data = json.loads(post_data)
            if "email" in data:
                target_email = data["email"].strip()
            elif "text" in data or "message" in data:
                text = data.get("text") or data.get("message")
                matches = EMAIL_REGEX.findall(text)
                if matches:
                    target_email = matches[0]
        except Exception:
            matches = EMAIL_REGEX.findall(post_data)
            if matches:
                target_email = matches[0]

        # Handle test pings or empty notification payload
        if not target_email:
            clean_data = post_data.strip()
            if clean_data in ("", "{notification}", "[not_body]", "{}") or "notification" in clean_data.lower():
                print(f"\n[Test Ping Received] MacroDroid connected successfully! (Payload: '{clean_data}')")
                sys.stdout.flush()
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "status": "success",
                    "message": "Connection verified! Webhook reached successfully. Ready for incoming job posts."
                }).encode('utf-8'))
                return

            self.send_response(400)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": "error",
                "message": "No valid email address found in request payload"
            }).encode('utf-8'))
            return

        print(f"\n[Webhook Received] Found recipient: {target_email}")
        sys.stdout.flush()
        success = send_email_smtp(to_email=target_email)

        if success:
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": "success",
                "message": f"Email successfully dispatched to {target_email}"
            }).encode('utf-8'))
        else:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": "error",
                "message": f"Failed to dispatch email to {target_email}"
            }).encode('utf-8'))
        sys.stdout.flush()

    def log_message(self, format, *args):
        print(f"[Server] {self.address_string()} - {format % args}")
        sys.stdout.flush()

def run_server():
    # Render assigns the port dynamically via PORT environment variable
    port = int(os.environ.get("PORT", 8080))
    server_address = ('0.0.0.0', port)
    httpd = HTTPServer(server_address, WebhookHandler)
    print(f" Recruiter Mailer Webhook Server running on http://0.0.0.0:{port}")
    sys.stdout.flush()
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server...")
        httpd.server_close()

if __name__ == '__main__':
    run_server()
