import requests
import os
import json
import logging

logger = logging.getLogger("notification_driver")

class WebhookDriver:
    """
    Sends interactive notifications to Slack or Teams.
    """
    def __init__(self, webhook_url: str = None):
        self.webhook_url = webhook_url or os.getenv("SLACK_WEBHOOK_URL")

    def send_deployment_alert(self, score: int, status: str, summary: str, recommendations: list) -> bool:
        if not self.webhook_url:
            logger.warning("SLACK_WEBHOOK_URL not set, skipping notification.")
            return False

        # Slack Block Kit format for actionable alerts
        payload = {
            "blocks": [
                {
                    "type": "header",
                    "text": {"type": "plain_text", "text": "🚀 Deployment Readiness Alert"}
                },
                {
                    "type": "section",
                    "fields": [
                        {"type": "mrkdwn", "text": f"*Score:* {score}"},
                        {"type": "mrkdwn", "text": f"*Status:* {status}"}
                    ]
                },
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": f"*Summary:* {summary}"}
                },
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": "*Recommendations:* " + ", ".join(recommendations)}
                }
            ]
        }
        
        # Add interactive buttons if intervention is needed
        if status == "CAUTION":
            payload["blocks"].append({
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "Approve Deployment"},
                        "style": "primary",
                        "value": "approve"
                    },
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "Abort"},
                        "style": "danger",
                        "value": "abort"
                    }
                ]
            })

        try:
            response = requests.post(self.webhook_url, json=payload)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Failed to send webhook: {e}")
            return False
