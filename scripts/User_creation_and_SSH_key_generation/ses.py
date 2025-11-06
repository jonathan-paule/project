import boto3
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import os
import sys

def send_email(recipient_email: str, subject: str, body: str, attachment_path: str):
    ses = boto3.client("ses", region_name="us-east-1")

    sender = "jonathan.p@adcuratio.com"  # must be verified in SES

    # Build email
    msg = MIMEMultipart()
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = recipient_email

    # Body
    msg.attach(MIMEText(body, "plain"))

    # Attachment
    with open(attachment_path, "rb") as f:
        part = MIMEApplication(f.read())
        part.add_header(
            "Content-Disposition",
            f"attachment; filename={os.path.basename(attachment_path)}"
        )
        msg.attach(part)

    # Send email via SES
    response = ses.send_raw_email(
        Source=sender,
        Destinations=[recipient_email],
        RawMessage={"Data": msg.as_string()}
    )

    print(f"📧 Email sent to {recipient_email}, MessageId: {response['MessageId']}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 AWS_SES.py <attachment_path>")
        sys.exit(1)

    attachment_path = sys.argv[1]
    subject = "New User credentials"
    body = "Hello, here you can find the attachment of the private key for the new user."

    send_email("amitesh.joseph@adcuratio.com", subject, body, attachment_path) # here you can give the recepient mail where the key should be send and make sure the recepient is verified in AWS SES.
