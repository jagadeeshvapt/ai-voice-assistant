import re
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from .base import Skill, register_skill
from ..config import config
from ..utils import logger

@register_skill
class CommunicationSkill(Skill):
    name = "communication"
    description = "Sends emails, WhatsApp messages"
    keywords = ["email", "send email", "mail", "whatsapp", "send message", "message"]
    patterns = [
        r"send (?:an )?email(?: to (.+))?",
        r"send (?:a )?whatsapp (?:message )?(?:to )?(.+)",
        r"email (.+)",
    ]

    def handle(self, text, context=None):
        low = text.lower()

        if "email" in low:
            return self._handle_email(text, low)

        if "whatsapp" in low:
            return self._handle_whatsapp(text, low)

        return None

    def _handle_email(self, text: str, low: str):
        # Check if configured
        if not config.EMAIL_ADDRESS or not config.EMAIL_PASSWORD:
            return "Email not configured, sir. Please set EMAIL_ADDRESS and EMAIL_PASSWORD in .env to use this feature"

        # Extract recipient and content
        # Simple pattern: "send email to john@example.com saying hello"
        m = re.search(r"send (?:an )?email to (\S+)(?: saying (.+))?", low)
        if not m:
            m = re.search(r"email (\S+)(?: saying (.+))?", low)
        
        if not m:
            return "To send email, say 'send email to recipient@example.com saying your message'"

        recipient = m.group(1).strip()
        # Basic validation
        if "@" not in recipient:
            return f"Invalid email address: {recipient}"

        message_body = m.group(2) if len(m.groups()) > 1 and m.group(2) else None
        if not message_body:
            # Extract original casing for message
            # Find "saying" in original text
            orig_low = text.lower()
            if "saying" in orig_low:
                idx = orig_low.find("saying") + len("saying")
                message_body = text[idx:].strip()
            else:
                message_body = "Hello, this is a message from JARVIS, your AI assistant."

        try:
            msg = MIMEMultipart()
            msg['From'] = config.EMAIL_ADDRESS
            msg['To'] = recipient
            msg['Subject'] = f"Message from JARVIS Assistant"
            msg.attach(MIMEText(message_body, 'plain'))

            server = smtplib.SMTP(config.SMTP_SERVER, config.SMTP_PORT)
            server.starttls()
            server.login(config.EMAIL_ADDRESS, config.EMAIL_PASSWORD)
            server.send_message(msg)
            server.quit()
            return f"Email sent to {recipient}, sir"
        except Exception as e:
            logger.error(f"Email send failed: {e}")
            return f"Failed to send email: {e}"

    def _handle_whatsapp(self, text: str, low: str):
        # Uses pywhatkit or web.whatsapp.com
        try:
            # Parse "send whatsapp to +919xxxxxxxxx message hello"
            m = re.search(r"send whatsapp (?:message )?(?:to )?(\+?\d+)?(?: message)? (.+)", low)
            if m:
                number = m.group(1) or ""
                msg_text = m.group(2) if len(m.groups()) > 1 else ""
                if not msg_text:
                    msg_text = "Hello from JARVIS"
                
                # Use web.whatsapp.com
                import webbrowser
                from urllib.parse import quote
                if number:
                    # Ensure country code? Assume as given
                    url = f"https://wa.me/{number.replace('+','').replace(' ','')}?text={quote(msg_text)}"
                else:
                    url = f"https://wa.me/?text={quote(msg_text)}"
                webbrowser.open(url)
                return f"Opening WhatsApp for sending: {msg_text}"
            else:
                # Open WhatsApp Web
                import webbrowser
                webbrowser.open("https://web.whatsapp.com")
                return "Opening WhatsApp Web, sir"
        except Exception as e:
            return f"WhatsApp send failed: {e}"
