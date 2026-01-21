import logging
from typing import Dict, Any, List
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AlertManager:
    """Manage alerts and notifications"""
    
    def __init__(self):
        self.smtp_host = os.getenv('SMTP_HOST', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', 587))
        self.alert_email = os.getenv('ALERT_EMAIL')
        self.alerts_history = []
    
    def check_inventory_alerts(self, df) -> List[Dict[str, Any]]:
        """Check for inventory-related alerts"""
        alerts = []
        
        # Low stock alerts
        if 'quantity' in df.columns and 'product_name' in df.columns:
            low_stock = df[df['quantity'] < 100]
            if len(low_stock) > 0:
                alerts.append({
                    'type': 'LOW_STOCK',
                    'severity': 'WARNING',
                    'count': len(low_stock),
                    'message': f"{len(low_stock)} products with low stock",
                    'products': low_stock['product_name'].tolist()[:5]
                })
        
        # Expiry alerts
        if 'days_until_expiry' in df.columns:
            expiring_soon = df[df['days_until_expiry'] < 30]
            critical_expiry = df[df['days_until_expiry'] < 7]
            
            if len(critical_expiry) > 0:
                alerts.append({
                    'type': 'CRITICAL_EXPIRY',
                    'severity': 'CRITICAL',
                    'count': len(critical_expiry),
                    'message': f"{len(critical_expiry)} products expiring within 7 days"
                })
            elif len(expiring_soon) > 0:
                alerts.append({
                    'type': 'EXPIRY_WARNING',
                    'severity': 'WARNING',
                    'count': len(expiring_soon),
                    'message': f"{len(expiring_soon)} products expiring within 30 days"
                })
        
        # Data quality alerts
        null_percentage = (df.isnull().sum().sum() / (len(df) * len(df.columns))) * 100
        if null_percentage > 5:
            alerts.append({
                'type': 'DATA_QUALITY',
                'severity': 'WARNING',
                'message': f"Data quality issue: {null_percentage:.2f}% missing values"
            })
        
        # Log alerts
        for alert in alerts:
            self.log_alert(alert)
        
        return alerts
    
    def log_alert(self, alert: Dict[str, Any]):
        """Log an alert"""
        alert['timestamp'] = datetime.now().isoformat()
        self.alerts_history.append(alert)
        
        severity_emoji = {
            'INFO': 'ℹ️',
            'WARNING': '⚠️',
            'CRITICAL': '🚨'
        }
        
        emoji = severity_emoji.get(alert.get('severity', 'INFO'), 'ℹ️')
        logger.warning(f"{emoji} ALERT: {alert['message']}")
    
    def send_email_alert(self, subject: str, body: str):
        """Send email alert (if configured)"""
        if not self.alert_email:
            logger.info("Email alerts not configured (ALERT_EMAIL not set)")
            return
        
        try:
            msg = MIMEMultipart()
            msg['From'] = self.alert_email
            msg['To'] = self.alert_email
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Note: This is a placeholder - requires SMTP credentials
            logger.info(f"Email alert prepared: {subject}")
            # Actual sending would require SMTP authentication
            
        except Exception as e:
            logger.error(f"Error sending email alert: {e}")
    
    def get_alerts_summary(self) -> Dict[str, Any]:
        """Get summary of recent alerts"""
        if not self.alerts_history:
            return {
                'total_alerts': 0,
                'critical': 0,
                'warnings': 0,
                'info': 0
            }
        
        return {
            'total_alerts': len(self.alerts_history),
            'critical': sum(1 for a in self.alerts_history if a.get('severity') == 'CRITICAL'),
            'warnings': sum(1 for a in self.alerts_history if a.get('severity') == 'WARNING'),
            'info': sum(1 for a in self.alerts_history if a.get('severity') == 'INFO'),
            'recent_alerts': self.alerts_history[-5:]
        }