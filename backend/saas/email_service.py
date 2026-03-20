"""
Email Service for SaaS notifications using Resend
"""
import os
import asyncio
import logging
from datetime import datetime
from typing import Optional

# Try to import resend, handle if not installed
try:
    import resend
    RESEND_AVAILABLE = True
except ImportError:
    RESEND_AVAILABLE = False
    logging.warning("Resend not installed, email notifications disabled")

# Email templates
TEMPLATES = {
    "welcome": {
        "subject": "Bine ai venit la SEO Automation! 🚀",
        "html": """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background-color: #050505;">
    <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #050505; padding: 40px 20px;">
        <tr>
            <td align="center">
                <table width="600" cellpadding="0" cellspacing="0" style="background-color: #0A0A0A; border-radius: 12px; border: 1px solid #262626;">
                    <!-- Header -->
                    <tr>
                        <td style="padding: 40px 40px 20px; text-align: center;">
                            <div style="width: 60px; height: 60px; background-color: #00E676; border-radius: 12px; display: inline-block; line-height: 60px; font-size: 30px;">⚡</div>
                            <h1 style="color: #FFFFFF; margin: 20px 0 0; font-size: 28px;">Bine ai venit, {name}!</h1>
                        </td>
                    </tr>
                    <!-- Content -->
                    <tr>
                        <td style="padding: 20px 40px;">
                            <p style="color: #A1A1AA; font-size: 16px; line-height: 1.6; margin: 0 0 20px;">
                                Mulțumim că te-ai alăturat SEO Automation! Ai acum <strong style="color: #00E676;">7 zile gratuite</strong> să explorezi toate funcționalitățile platformei.
                            </p>
                            <p style="color: #A1A1AA; font-size: 16px; line-height: 1.6; margin: 0 0 20px;">
                                În perioada de trial poți:
                            </p>
                            <ul style="color: #A1A1AA; font-size: 15px; line-height: 1.8; padding-left: 20px; margin: 0 0 30px;">
                                <li>Genera până la <strong style="color: #FFFFFF;">10 articole SEO</strong> cu AI</li>
                                <li>Conecta <strong style="color: #FFFFFF;">5 site-uri WordPress</strong></li>
                                <li>Accesa calendarul editorial și keyword research</li>
                                <li>Testa publicarea automată</li>
                            </ul>
                        </td>
                    </tr>
                    <!-- CTA -->
                    <tr>
                        <td style="padding: 0 40px 40px; text-align: center;">
                            <a href="{frontend_url}/app/dashboard" style="display: inline-block; background-color: #00E676; color: #000000; padding: 16px 40px; border-radius: 8px; text-decoration: none; font-weight: 600; font-size: 16px;">
                                Începe Acum →
                            </a>
                        </td>
                    </tr>
                    <!-- Footer -->
                    <tr>
                        <td style="padding: 30px 40px; border-top: 1px solid #262626; text-align: center;">
                            <p style="color: #525252; font-size: 13px; margin: 0;">
                                © 2026 SEO Automation. Toate drepturile rezervate.
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
"""
    },
    
    "trial_reminder": {
        "subject": "⏰ Trial-ul tău expiră în {days_left} zile",
        "html": """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background-color: #050505;">
    <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #050505; padding: 40px 20px;">
        <tr>
            <td align="center">
                <table width="600" cellpadding="0" cellspacing="0" style="background-color: #0A0A0A; border-radius: 12px; border: 1px solid #262626;">
                    <!-- Header -->
                    <tr>
                        <td style="padding: 40px 40px 20px; text-align: center;">
                            <div style="width: 60px; height: 60px; background-color: #FFA726; border-radius: 12px; display: inline-block; line-height: 60px; font-size: 30px;">⏰</div>
                            <h1 style="color: #FFFFFF; margin: 20px 0 0; font-size: 24px;">Trial-ul tău expiră în {days_left} zile</h1>
                        </td>
                    </tr>
                    <!-- Content -->
                    <tr>
                        <td style="padding: 20px 40px;">
                            <p style="color: #A1A1AA; font-size: 16px; line-height: 1.6; margin: 0 0 20px;">
                                Salut {name},
                            </p>
                            <p style="color: #A1A1AA; font-size: 16px; line-height: 1.6; margin: 0 0 20px;">
                                Ai mai rămas <strong style="color: #FFA726;">{days_left} zile</strong> din perioada de trial. Pentru a continua să folosești SEO Automation fără întrerupere, alege un plan care ți se potrivește.
                            </p>
                            <!-- Usage Stats -->
                            <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #171717; border-radius: 8px; margin: 20px 0;">
                                <tr>
                                    <td style="padding: 20px;">
                                        <p style="color: #71717A; font-size: 13px; margin: 0 0 10px; text-transform: uppercase;">Ce ai realizat în trial:</p>
                                        <p style="color: #FFFFFF; font-size: 15px; margin: 0;">
                                            📝 {articles_generated} articole generate<br>
                                            🌐 {sites_connected} site-uri conectate
                                        </p>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    <!-- CTA -->
                    <tr>
                        <td style="padding: 0 40px 40px; text-align: center;">
                            <a href="{frontend_url}/pricing" style="display: inline-block; background-color: #00E676; color: #000000; padding: 16px 40px; border-radius: 8px; text-decoration: none; font-weight: 600; font-size: 16px;">
                                Alege un Plan
                            </a>
                            <p style="color: #525252; font-size: 13px; margin: 15px 0 0;">
                                Planurile încep de la doar €19/lună
                            </p>
                        </td>
                    </tr>
                    <!-- Footer -->
                    <tr>
                        <td style="padding: 30px 40px; border-top: 1px solid #262626; text-align: center;">
                            <p style="color: #525252; font-size: 13px; margin: 0;">
                                © 2026 SEO Automation. Toate drepturile rezervate.
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
"""
    },
    
    "payment_success": {
        "subject": "✅ Plata a fost procesată cu succes!",
        "html": """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background-color: #050505;">
    <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #050505; padding: 40px 20px;">
        <tr>
            <td align="center">
                <table width="600" cellpadding="0" cellspacing="0" style="background-color: #0A0A0A; border-radius: 12px; border: 1px solid #262626;">
                    <!-- Header -->
                    <tr>
                        <td style="padding: 40px 40px 20px; text-align: center;">
                            <div style="width: 60px; height: 60px; background-color: #00E676; border-radius: 12px; display: inline-block; line-height: 60px; font-size: 30px;">✅</div>
                            <h1 style="color: #FFFFFF; margin: 20px 0 0; font-size: 24px;">Plata confirmată!</h1>
                        </td>
                    </tr>
                    <!-- Content -->
                    <tr>
                        <td style="padding: 20px 40px;">
                            <p style="color: #A1A1AA; font-size: 16px; line-height: 1.6; margin: 0 0 20px;">
                                Salut {name},
                            </p>
                            <p style="color: #A1A1AA; font-size: 16px; line-height: 1.6; margin: 0 0 20px;">
                                Mulțumim pentru plata ta! Subscripția <strong style="color: #00E676;">{plan_name}</strong> este acum activă.
                            </p>
                            <!-- Receipt -->
                            <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #171717; border-radius: 8px; margin: 20px 0;">
                                <tr>
                                    <td style="padding: 20px;">
                                        <table width="100%" cellpadding="0" cellspacing="0">
                                            <tr>
                                                <td style="color: #71717A; font-size: 14px; padding: 5px 0;">Plan:</td>
                                                <td style="color: #FFFFFF; font-size: 14px; text-align: right; padding: 5px 0;">{plan_name}</td>
                                            </tr>
                                            <tr>
                                                <td style="color: #71717A; font-size: 14px; padding: 5px 0;">Sumă:</td>
                                                <td style="color: #FFFFFF; font-size: 14px; text-align: right; padding: 5px 0;">€{amount}</td>
                                            </tr>
                                            <tr>
                                                <td style="color: #71717A; font-size: 14px; padding: 5px 0;">Data:</td>
                                                <td style="color: #FFFFFF; font-size: 14px; text-align: right; padding: 5px 0;">{date}</td>
                                            </tr>
                                            <tr>
                                                <td style="color: #71717A; font-size: 14px; padding: 5px 0;">Următoarea facturare:</td>
                                                <td style="color: #FFFFFF; font-size: 14px; text-align: right; padding: 5px 0;">{next_billing}</td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>
                            </table>
                            <!-- New Limits -->
                            <p style="color: #A1A1AA; font-size: 16px; line-height: 1.6; margin: 20px 0;">
                                <strong style="color: #FFFFFF;">Noile tale limite:</strong>
                            </p>
                            <ul style="color: #A1A1AA; font-size: 15px; line-height: 1.8; padding-left: 20px; margin: 0;">
                                <li>{sites_limit} site-uri WordPress</li>
                                <li>{articles_limit} articole/lună</li>
                            </ul>
                        </td>
                    </tr>
                    <!-- CTA -->
                    <tr>
                        <td style="padding: 20px 40px 40px; text-align: center;">
                            <a href="{frontend_url}/app/dashboard" style="display: inline-block; background-color: #00E676; color: #000000; padding: 16px 40px; border-radius: 8px; text-decoration: none; font-weight: 600; font-size: 16px;">
                                Mergi la Dashboard
                            </a>
                        </td>
                    </tr>
                    <!-- Footer -->
                    <tr>
                        <td style="padding: 30px 40px; border-top: 1px solid #262626; text-align: center;">
                            <p style="color: #525252; font-size: 13px; margin: 0;">
                                © 2026 SEO Automation. Toate drepturile rezervate.
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
"""
    },
    
    "trial_expired": {
        "subject": "😢 Perioada de trial s-a încheiat",
        "html": """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background-color: #050505;">
    <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #050505; padding: 40px 20px;">
        <tr>
            <td align="center">
                <table width="600" cellpadding="0" cellspacing="0" style="background-color: #0A0A0A; border-radius: 12px; border: 1px solid #262626;">
                    <!-- Header -->
                    <tr>
                        <td style="padding: 40px 40px 20px; text-align: center;">
                            <h1 style="color: #FFFFFF; margin: 0; font-size: 24px;">Perioada de trial s-a încheiat</h1>
                        </td>
                    </tr>
                    <!-- Content -->
                    <tr>
                        <td style="padding: 20px 40px;">
                            <p style="color: #A1A1AA; font-size: 16px; line-height: 1.6; margin: 0 0 20px;">
                                Salut {name},
                            </p>
                            <p style="color: #A1A1AA; font-size: 16px; line-height: 1.6; margin: 0 0 20px;">
                                Perioada ta de trial de 7 zile s-a încheiat. Pentru a continua să generezi articole și să folosești toate funcționalitățile, te invităm să alegi un plan.
                            </p>
                            <p style="color: #A1A1AA; font-size: 16px; line-height: 1.6; margin: 0 0 20px;">
                                <strong style="color: #FFFFFF;">Datele tale sunt în siguranță</strong> - articolele și setările sunt păstrate și vei putea accesa totul după activarea unui plan.
                            </p>
                        </td>
                    </tr>
                    <!-- CTA -->
                    <tr>
                        <td style="padding: 0 40px 40px; text-align: center;">
                            <a href="{frontend_url}/pricing" style="display: inline-block; background-color: #00E676; color: #000000; padding: 16px 40px; border-radius: 8px; text-decoration: none; font-weight: 600; font-size: 16px;">
                                Alege un Plan
                            </a>
                            <p style="color: #525252; font-size: 13px; margin: 15px 0 0;">
                                Planurile încep de la doar €19/lună
                            </p>
                        </td>
                    </tr>
                    <!-- Footer -->
                    <tr>
                        <td style="padding: 30px 40px; border-top: 1px solid #262626; text-align: center;">
                            <p style="color: #525252; font-size: 13px; margin: 0;">
                                © 2026 SEO Automation. Toate drepturile rezervate.
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
"""
    }
}


class EmailService:
    """Service for sending transactional emails"""
    
    def __init__(self):
        self.api_key = os.environ.get('RESEND_API_KEY')
        self.sender_email = os.environ.get('SENDER_EMAIL', 'onboarding@resend.dev')
        self.frontend_url = os.environ.get('FRONTEND_URL', 'https://login-auth-test.preview.emergentagent.com')
        
        if self.api_key and RESEND_AVAILABLE:
            resend.api_key = self.api_key
            self.enabled = True
            logging.info("[EMAIL] Resend email service initialized")
        else:
            self.enabled = False
            logging.warning("[EMAIL] Email service disabled (no API key or resend not installed)")
    
    async def send_email(self, to_email: str, template_name: str, variables: dict) -> bool:
        """Send an email using a template"""
        if not self.enabled:
            logging.info(f"[EMAIL] Would send '{template_name}' to {to_email} (disabled)")
            return False
        
        template = TEMPLATES.get(template_name)
        if not template:
            logging.error(f"[EMAIL] Template '{template_name}' not found")
            return False
        
        # Add frontend_url to variables
        variables['frontend_url'] = self.frontend_url
        
        # Format subject and HTML
        subject = template['subject'].format(**variables)
        html = template['html'].format(**variables)
        
        params = {
            "from": self.sender_email,
            "to": [to_email],
            "subject": subject,
            "html": html
        }
        
        try:
            result = await asyncio.to_thread(resend.Emails.send, params)
            logging.info(f"[EMAIL] Sent '{template_name}' to {to_email}, ID: {result.get('id')}")
            return True
        except Exception as e:
            logging.error(f"[EMAIL] Failed to send '{template_name}' to {to_email}: {e}")
            return False
    
    async def send_welcome_email(self, email: str, name: str) -> bool:
        """Send welcome email to new user"""
        return await self.send_email(email, "welcome", {"name": name})
    
    async def send_trial_reminder(self, email: str, name: str, days_left: int, 
                                   articles_generated: int, sites_connected: int) -> bool:
        """Send trial expiration reminder"""
        return await self.send_email(email, "trial_reminder", {
            "name": name,
            "days_left": days_left,
            "articles_generated": articles_generated,
            "sites_connected": sites_connected
        })
    
    async def send_trial_expired(self, email: str, name: str) -> bool:
        """Send trial expired notification"""
        return await self.send_email(email, "trial_expired", {"name": name})
    
    async def send_payment_success(self, email: str, name: str, plan_name: str, 
                                    amount: float, sites_limit: int, articles_limit: int) -> bool:
        """Send payment confirmation email"""
        from datetime import datetime, timedelta
        
        now = datetime.now()
        next_billing = now + timedelta(days=30)
        
        sites_str = "Nelimitate" if sites_limit == -1 else str(sites_limit)
        articles_str = "Nelimitate" if articles_limit == -1 else str(articles_limit)
        
        return await self.send_email(email, "payment_success", {
            "name": name,
            "plan_name": plan_name,
            "amount": f"{amount:.2f}",
            "date": now.strftime("%d.%m.%Y"),
            "next_billing": next_billing.strftime("%d.%m.%Y"),
            "sites_limit": sites_str,
            "articles_limit": articles_str
        })


# Global email service instance
email_service = EmailService()
