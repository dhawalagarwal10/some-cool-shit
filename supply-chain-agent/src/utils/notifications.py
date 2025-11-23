import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import httpx
from typing import List, Dict
import logging
from datetime import datetime

from config.settings import settings

logger = logging.getLogger(__name__)

class NotificationService:
    """
    handles notifications via email and slack
    """

    def __init__(self):
        self.slack_client = None
        if settings.slack_bot_token:
            self.slack_client = WebClient(token=settings.slack_bot_token)

    def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        is_html: bool = False
    ) -> bool:
        """
        send email notification
        """
        if not settings.email_sender or not settings.email_password:
            logger.warning("email credentials not configured")
            return False

        try:
            msg = MIMEMultipart('alternative')
            msg['From'] = settings.email_sender
            msg['To'] = to_email
            msg['Subject'] = subject

            if is_html:
                msg.attach(MIMEText(body, 'html'))
            else:
                msg.attach(MIMEText(body, 'plain'))

            with smtplib.SMTP(settings.smtp_server, settings.smtp_port) as server:
                server.starttls()
                server.login(settings.email_sender, settings.email_password)
                server.send_message(msg)

            logger.info(f"email sent to {to_email}")
            return True

        except Exception as e:
            logger.error(f"failed to send email: {str(e)}")
            return False

    def send_slack_message(
        self,
        channel: str,
        message: str,
        blocks: List[Dict] = None
    ) -> bool:
        """
        send slack message
        """
        if not self.slack_client:
            logger.warning("slack not configured")
            return False

        try:
            response = self.slack_client.chat_postMessage(
                channel=channel,
                text=message,
                blocks=blocks
            )
            logger.info(f"slack message sent to {channel}")
            return True

        except SlackApiError as e:
            logger.error(f"slack error: {e.response['error']}")
            return False

    def send_slack_webhook(self, message: str) -> bool:
        """
        send notification via slack webhook
        simpler alternative to bot tokens
        """
        if not settings.slack_webhook_url:
            logger.warning("slack webhook not configured")
            return False

        try:
            payload = {"text": message}
            response = httpx.post(settings.slack_webhook_url, json=payload, timeout=10)
            response.raise_for_status()
            logger.info("slack webhook notification sent")
            return True

        except Exception as e:
            logger.error(f"slack webhook failed: {str(e)}")
            return False

    def notify_stockout_alert(
        self,
        product_name: str,
        current_stock: int,
        days_until_stockout: int,
        recommended_order: int
    ):
        """
        send urgent stockout alert
        """
        urgency = "🚨 CRITICAL" if days_until_stockout <= 3 else "⚠️ WARNING"

        message = f"""
{urgency}: low stock alert

product: {product_name}
current stock: {current_stock} units
estimated stockout: {days_until_stockout} days
recommended order: {recommended_order} units

action required: review and approve purchase order
        """.strip()

        # send via available channels
        if settings.slack_webhook_url:
            self.send_slack_webhook(message)

        if settings.email_sender:
            self.send_email(
                to_email="operations@company.com",  # configure as needed
                subject=f"{urgency}: {product_name} low stock",
                body=message
            )

    def notify_purchase_order_created(
        self,
        po_number: str,
        product_name: str,
        quantity: int,
        total_cost: float,
        expected_delivery: str
    ):
        """
        notify when purchase order is created
        """
        message = f"""
📦 purchase order created

PO number: {po_number}
product: {product_name}
quantity: {quantity} units
total cost: ₹{total_cost:,.2f}
expected delivery: {expected_delivery}

status: pending approval
        """.strip()

        if settings.slack_webhook_url:
            blocks = [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "📦 new purchase order"
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {"type": "mrkdwn", "text": f"*PO Number:*\n{po_number}"},
                        {"type": "mrkdwn", "text": f"*Product:*\n{product_name}"},
                        {"type": "mrkdwn", "text": f"*Quantity:*\n{quantity} units"},
                        {"type": "mrkdwn", "text": f"*Total Cost:*\n₹{total_cost:,.2f}"}
                    ]
                }
            ]

            if self.slack_client:
                self.send_slack_message(
                    channel="#supply-chain",
                    message=message,
                    blocks=blocks
                )
            else:
                self.send_slack_webhook(message)

    def send_daily_summary(
        self,
        metrics: Dict,
        critical_items: List[str],
        summary: str = None
    ):
        """
        send daily inventory summary
        """
        message = f"""
📊 daily inventory summary - {datetime.now().strftime('%Y-%m-%d')}

health score: {metrics.get('health_score', 0)}%
products at risk: {metrics.get('products_at_risk', 0)}
total inventory value: ₹{metrics.get('total_inventory_value', 0):,.2f}

critical items requiring attention:
{chr(10).join(f"  • {item}" for item in critical_items[:5])}
        """.strip()

        if summary:
            message += f"\n\nai analysis:\n{summary}"

        if settings.slack_webhook_url:
            self.send_slack_webhook(message)

        if settings.email_sender:
            self.send_email(
                to_email="leadership@company.com",
                subject=f"daily inventory summary - {datetime.now().strftime('%Y-%m-%d')}",
                body=message
            )

    def notify_anomaly_detected(
        self,
        product_name: str,
        anomaly_description: str
    ):
        """
        alert when anomaly is detected
        """
        message = f"""
🔍 anomaly detected

product: {product_name}
description: {anomaly_description}

recommendation: investigate sales pattern
        """.strip()

        if settings.slack_webhook_url:
            self.send_slack_webhook(message)
