"""
Email worker for background email processing.
"""
from typing import List, Dict, Any, Optional
import logging
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
from email.mime.base import MimeBase
from email import encoders
import smtplib
import ssl

from .celery_app import celery_app
from app.config.settings import settings

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 3, 'countdown': 60})
def send_email(
    self,
    to_email: str,
    subject: str,
    body: str,
    from_email: Optional[str] = None,
    html_body: Optional[str] = None,
    attachments: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Send email asynchronously.
    
    Args:
        to_email: Recipient email address
        subject: Email subject
        body: Plain text email body
        from_email: Sender email (optional)
        html_body: HTML email body (optional)
        attachments: List of attachments (optional)
        
    Returns:
        Dict with send status and message ID
    """
    try:
        if not settings.smtp_host:
            logger.warning("SMTP not configured, skipping email send")
            return {"status": "skipped", "reason": "SMTP not configured"}
        
        # Create message
        message = MimeMultipart("alternative")
        message["Subject"] = subject
        message["From"] = from_email or settings.smtp_username
        message["To"] = to_email
        
        # Add text part
        text_part = MimeText(body, "plain")
        message.attach(text_part)
        
        # Add HTML part if provided
        if html_body:
            html_part = MimeText(html_body, "html")
            message.attach(html_part)
        
        # Add attachments if provided
        if attachments:
            for attachment in attachments:
                part = MimeBase("application", "octet-stream")
                part.set_payload(attachment["content"])
                encoders.encode_base64(part)
                part.add_header(
                    "Content-Disposition",
                    f"attachment; filename= {attachment['filename']}"
                )
                message.attach(part)
        
        # Send email
        context = ssl.create_default_context()
        
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
            if settings.smtp_use_tls:
                server.starttls(context=context)
            
            if settings.smtp_username and settings.smtp_password:
                server.login(settings.smtp_username, settings.smtp_password)
            
            text = message.as_string()
            server.sendmail(from_email or settings.smtp_username, to_email, text)
        
        logger.info(f"Email sent successfully to {to_email}")
        return {
            "status": "sent",
            "to_email": to_email,
            "subject": subject,
            "task_id": self.request.id
        }
        
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {e}")
        raise


@celery_app.task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 3, 'countdown': 60})
def send_bulk_email(
    self,
    email_list: List[Dict[str, Any]],
    subject: str,
    body: str,
    from_email: Optional[str] = None,
    html_body: Optional[str] = None
) -> Dict[str, Any]:
    """
    Send email to multiple recipients.
    
    Args:
        email_list: List of email dictionaries with 'email' and optional 'name'
        subject: Email subject
        body: Plain text email body
        from_email: Sender email (optional)
        html_body: HTML email body (optional)
        
    Returns:
        Dict with send results
    """
    try:
        results = {
            "total": len(email_list),
            "sent": 0,
            "failed": 0,
            "errors": []
        }
        
        for email_data in email_list:
            try:
                # Personalize subject and body if name is provided
                personalized_subject = subject
                personalized_body = body
                personalized_html = html_body
                
                if email_data.get("name"):
                    name = email_data["name"]
                    personalized_subject = subject.replace("{{name}}", name)
                    personalized_body = body.replace("{{name}}", name)
                    if html_body:
                        personalized_html = html_body.replace("{{name}}", name)
                
                # Send individual email
                send_email.delay(
                    to_email=email_data["email"],
                    subject=personalized_subject,
                    body=personalized_body,
                    from_email=from_email,
                    html_body=personalized_html
                )
                
                results["sent"] += 1
                
            except Exception as e:
                results["failed"] += 1
                results["errors"].append({
                    "email": email_data["email"],
                    "error": str(e)
                })
                logger.error(f"Failed to queue email for {email_data['email']}: {e}")
        
        logger.info(f"Bulk email processing completed: {results['sent']} sent, {results['failed']} failed")
        return results
        
    except Exception as e:
        logger.error(f"Bulk email processing failed: {e}")
        raise


@celery_app.task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 3, 'countdown': 60})
def send_template_email(
    self,
    to_email: str,
    template_name: str,
    template_data: Dict[str, Any],
    from_email: Optional[str] = None
) -> Dict[str, Any]:
    """
    Send email using a template.
    
    Args:
        to_email: Recipient email address
        template_name: Name of the email template
        template_data: Data to populate template
        from_email: Sender email (optional)
        
    Returns:
        Dict with send status
    """
    try:
        # TODO: Implement template loading and rendering
        # This would typically load templates from a template engine like Jinja2
        
        # For now, return a placeholder
        logger.info(f"Template email {template_name} queued for {to_email}")
        return {
            "status": "template_not_implemented",
            "to_email": to_email,
            "template_name": template_name,
            "task_id": self.request.id
        }
        
    except Exception as e:
        logger.error(f"Failed to send template email {template_name} to {to_email}: {e}")
        raise


@celery_app.task(bind=True)
def send_notification_email(
    self,
    to_email: str,
    notification_type: str,
    data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Send notification email based on type.
    
    Args:
        to_email: Recipient email address
        notification_type: Type of notification
        data: Notification data
        
    Returns:
        Dict with send status
    """
    try:
        # Define notification templates
        templates = {
            "welcome": {
                "subject": "Welcome to The Plugs!",
                "body": "Welcome {{name}}! Thank you for joining The Plugs platform."
            },
            "password_reset": {
                "subject": "Password Reset Request",
                "body": "Click the link to reset your password: {{reset_link}}"
            },
            "event_reminder": {
                "subject": "Event Reminder: {{event_name}}",
                "body": "Don't forget about the upcoming event: {{event_name}} on {{event_date}}"
            },
            "connection_request": {
                "subject": "New Connection Request",
                "body": "{{requester_name}} wants to connect with you on The Plugs."
            }
        }
        
        if notification_type not in templates:
            raise ValueError(f"Unknown notification type: {notification_type}")
        
        template = templates[notification_type]
        
        # Replace placeholders with actual data
        subject = template["subject"]
        body = template["body"]
        
        for key, value in data.items():
            placeholder = f"{{{{{key}}}}}"
            subject = subject.replace(placeholder, str(value))
            body = body.replace(placeholder, str(value))
        
        # Send the email
        return send_email.delay(
            to_email=to_email,
            subject=subject,
            body=body
        )
        
    except Exception as e:
        logger.error(f"Failed to send notification email {notification_type} to {to_email}: {e}")
        raise
