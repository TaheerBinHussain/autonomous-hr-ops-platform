import json
import smtplib
import urllib.request
from email.mime.text import MIMEText


def test_mailpit():
    print("Testing Mailpit Email Delivery...")
    body = "Test email from recruitment system."
    to_email = "testcandidate@example.com"
    subject = "🎉 Test Interview Email"

    # Try SMTP
    for host in ["localhost", "127.0.0.1", "mailpit"]:
        try:
            msg = MIMEText(body)
            msg["Subject"] = subject
            msg["From"] = "recruiting@company.local"
            msg["To"] = to_email
            with smtplib.SMTP(host, 1025, timeout=2) as server:
                server.sendmail("recruiting@company.local", [to_email], msg.as_string())
            print(f"✅ SMTP success via {host}:1025")
            return
        except Exception as e:  # noqa: BLE001
            print(f"❌ SMTP {host}:1025 failed: {e}")

    # Try HTTP API
    for url in ["http://localhost:8025/api/v1/send", "http://127.0.0.1:8025/api/v1/send"]:
        try:
            payload = json.dumps({
                "From": {"Email": "recruiting@company.local", "Name": "HR Team"},
                "To": [{"Email": to_email, "Name": "Test Candidate"}],
                "Subject": subject,
                "Text": body
            }).encode("utf-8")
            req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
            urllib.request.urlopen(req, timeout=2)
            print(f"✅ HTTP API success via {url}")
            return
        except Exception as e:  # noqa: BLE001
            print(f"❌ HTTP API {url} failed: {e}")


if __name__ == "__main__":
    test_mailpit()
