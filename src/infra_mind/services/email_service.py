"""
Email service for Infra Mind.

Handles sending emails for password resets, MFA setup, and other notifications.
"""

import os
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional
from loguru import logger


class EmailService:
    """Email service for sending transactional emails."""
    
    def __init__(self):
        """Initialize email service with SMTP configuration."""
        self.smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_username = os.getenv("SMTP_USERNAME", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.from_email = os.getenv("FROM_EMAIL", self.smtp_username)
        self.from_name = os.getenv("FROM_NAME", "Infra Mind")
        
        if not self.smtp_username or not self.smtp_password:
            logger.warning("SMTP credentials not configured. Email sending will be disabled.")
    
    async def send_email(
        self, 
        to_email: str, 
        subject: str, 
        html_content: str, 
        text_content: Optional[str] = None
    ) -> bool:
        """
        Send an email using SMTP.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML content of the email
            text_content: Plain text content (optional)
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        if not self.smtp_username or not self.smtp_password:
            logger.error("Cannot send email: SMTP credentials not configured")
            return False
        
        try:
            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = f"{self.from_name} <{self.from_email}>"
            message["To"] = to_email
            
            # Add text content
            if text_content:
                text_part = MIMEText(text_content, "plain")
                message.attach(text_part)
            
            # Add HTML content
            html_part = MIMEText(html_content, "html")
            message.attach(html_part)
            
            # Send email
            async with aiosmtplib.SMTP(
                hostname=self.smtp_host,
                port=self.smtp_port,
                start_tls=True
            ) as server:
                await server.login(self.smtp_username, self.smtp_password)
                await server.send_message(message)
            
            logger.info(f"Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False
    
    async def send_password_reset_email(self, to_email: str, reset_token: str, user_name: str) -> bool:
        """
        Send password reset email.
        
        Args:
            to_email: User's email address
            reset_token: Password reset token
            user_name: User's name
            
        Returns:
            bool: True if email sent successfully
        """
        reset_url = f"{os.getenv('FRONTEND_URL', 'http://localhost:3000')}/auth/reset-password?token={reset_token}"
        
        subject = "Reset Your Infra Mind Password"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: white; padding: 30px; border-radius: 0 0 10px 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .button {{ display: inline-block; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
                .footer {{ text-align: center; margin-top: 20px; color: #666; font-size: 14px; }}
                .warning {{ background: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 20px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Password Reset Request</h1>
                </div>
                <div class="content">
                    <p>Hello {user_name},</p>
                    
                    <p>We received a request to reset your password for your Infra Mind account. If you made this request, click the button below to reset your password:</p>
                    
                    <div style="text-align: center;">
                        <a href="{reset_url}" class="button">Reset Password</a>
                    </div>
                    
                    <p>Or copy and paste this link into your browser:</p>
                    <p style="word-break: break-all; background: #f8f9fa; padding: 10px; border-radius: 5px;">{reset_url}</p>
                    
                    <div class="warning">
                        <strong>Important:</strong> This link will expire in 1 hour for security reasons.
                    </div>
                    
                    <p>If you didn't request a password reset, please ignore this email. Your password won't be changed.</p>
                    
                    <p>Best regards,<br>The Infra Mind Team</p>
                </div>
                <div class="footer">
                    <p>This email was sent from a no-reply address. Please don't reply to this email.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        Password Reset Request
        
        Hello {user_name},
        
        We received a request to reset your password for your Infra Mind account.
        
        To reset your password, please click the link below or copy and paste it into your browser:
        {reset_url}
        
        This link will expire in 1 hour for security reasons.
        
        If you didn't request a password reset, please ignore this email.
        
        Best regards,
        The Infra Mind Team
        """
        
        return await self.send_email(to_email, subject, html_content, text_content)
    
    def _get_base_email_template(self, title: str, header_color: str = "#667eea") -> str:
        """
        Base email template for consistent styling across all emails.
        
        Args:
            title: Email title for header
            header_color: Header background color
            
        Returns:
            str: Base HTML template with placeholders
        """
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{title}</title>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    margin: 0;
                    padding: 0;
                    background-color: #f5f7fa;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                    background-color: #f5f7fa;
                }}
                .email-wrapper {{
                    background: white;
                    border-radius: 12px;
                    box-shadow: 0 4px 20px rgba(0,0,0,0.08);
                    overflow: hidden;
                }}
                .header {{
                    background: linear-gradient(135deg, {header_color} 0%, #764ba2 100%);
                    color: white;
                    padding: 40px 30px;
                    text-align: center;
                }}
                .header h1 {{
                    margin: 0;
                    font-size: 28px;
                    font-weight: 600;
                }}
                .header .subtitle {{
                    margin: 10px 0 0 0;
                    font-size: 16px;
                    opacity: 0.9;
                }}
                .content {{
                    padding: 40px 30px;
                }}
                .content p {{
                    margin: 16px 0;
                    font-size: 16px;
                }}
                .content h2 {{
                    color: #2c3e50;
                    font-size: 20px;
                    margin: 30px 0 15px 0;
                }}
                .button {{
                    display: inline-block;
                    background: linear-gradient(135deg, {header_color} 0%, #764ba2 100%);
                    color: white;
                    padding: 16px 32px;
                    text-decoration: none;
                    border-radius: 8px;
                    margin: 20px 0;
                    font-weight: 600;
                    font-size: 16px;
                    transition: transform 0.2s;
                }}
                .button:hover {{
                    transform: translateY(-2px);
                }}
                .alert {{
                    padding: 20px;
                    margin: 25px 0;
                    border-radius: 8px;
                    border-left: 5px solid;
                }}
                .alert-success {{
                    background: #d4edda;
                    border-left-color: #28a745;
                    color: #155724;
                }}
                .alert-warning {{
                    background: #fff3cd;
                    border-left-color: #ffc107;
                    color: #856404;
                }}
                .alert-info {{
                    background: #d1ecf1;
                    border-left-color: #17a2b8;
                    color: #0c5460;
                }}
                .alert-danger {{
                    background: #f8d7da;
                    border-left-color: #dc3545;
                    color: #721c24;
                }}
                .code-block {{
                    background: #f8f9fa;
                    border: 1px solid #e9ecef;
                    border-radius: 6px;
                    padding: 15px;
                    font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
                    font-size: 14px;
                    word-break: break-all;
                    margin: 15px 0;
                }}
                .backup-codes {{
                    background: #f8f9fa;
                    border: 2px solid #e9ecef;
                    border-radius: 8px;
                    padding: 20px;
                    margin: 20px 0;
                }}
                .backup-codes h3 {{
                    color: #dc3545;
                    margin-top: 0;
                    font-size: 18px;
                }}
                .backup-codes-grid {{
                    display: grid;
                    grid-template-columns: repeat(2, 1fr);
                    gap: 10px;
                    margin: 15px 0;
                }}
                .backup-code {{
                    background: white;
                    border: 1px solid #dee2e6;
                    border-radius: 4px;
                    padding: 8px 12px;
                    font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
                    font-size: 14px;
                    text-align: center;
                    font-weight: bold;
                }}
                .tips-list {{
                    background: #e3f2fd;
                    border-radius: 8px;
                    padding: 20px;
                    margin: 20px 0;
                }}
                .tips-list h3 {{
                    color: #1976d2;
                    margin-top: 0;
                }}
                .tips-list ul {{
                    margin: 10px 0;
                    padding-left: 20px;
                }}
                .tips-list li {{
                    margin: 8px 0;
                }}
                .footer {{
                    background: #f8f9fa;
                    padding: 30px;
                    text-align: center;
                    color: #6c757d;
                    font-size: 14px;
                    border-top: 1px solid #e9ecef;
                }}
                .footer-links {{
                    margin: 15px 0;
                }}
                .footer-links a {{
                    color: {header_color};
                    text-decoration: none;
                    margin: 0 15px;
                }}
                .security-notice {{
                    background: #fff3e0;
                    border: 1px solid #ffb74d;
                    border-radius: 8px;
                    padding: 20px;
                    margin: 25px 0;
                }}
                .security-notice h3 {{
                    color: #f57c00;
                    margin-top: 0;
                }}
                @media (max-width: 600px) {{
                    .container {{ padding: 10px; }}
                    .header {{ padding: 30px 20px; }}
                    .content {{ padding: 30px 20px; }}
                    .header h1 {{ font-size: 24px; }}
                    .backup-codes-grid {{ grid-template-columns: 1fr; }}
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="email-wrapper">
                    <div class="header">
                        <h1>{{HEADER_TITLE}}</h1>
                        <div class="subtitle">{{HEADER_SUBTITLE}}</div>
                    </div>
                    <div class="content">
                        {{CONTENT}}
                    </div>
                    <div class="footer">
                        <div>
                            <strong>Infra Mind</strong><br>
                            AI-Powered Infrastructure Intelligence Platform
                        </div>
                        <div class="footer-links">
                            <a href="{{FRONTEND_URL}}/dashboard">Dashboard</a>
                            <a href="{{FRONTEND_URL}}/settings">Settings</a>
                            <a href="{{FRONTEND_URL}}/support">Support</a>
                        </div>
                        <div style="margin-top: 20px;">
                            <small>This email was sent from a no-reply address. Please don't reply to this email.</small><br>
                            <small>If you have questions, visit our support center or contact us through the dashboard.</small>
                        </div>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """

    async def send_mfa_setup_email(self, to_email: str, user_name: str, backup_codes: list = None) -> bool:
        """
        Send MFA setup confirmation email with backup codes.
        
        Args:
            to_email: User's email address
            user_name: User's name
            backup_codes: List of backup codes to include in email
            
        Returns:
            bool: True if email sent successfully
        """
        subject = "🔒 Multi-Factor Authentication Successfully Enabled"
        
        # Generate backup codes display if provided
        backup_codes_html = ""
        if backup_codes:
            codes_grid = ""
            for code in backup_codes:
                codes_grid += f'<div class="backup-code">{code}</div>'
            
            backup_codes_html = f"""
            <div class="backup-codes">
                <h3>⚠️ Important: Save Your Backup Codes</h3>
                <p><strong>Store these codes in a safe place!</strong> You can use these one-time codes to access your account if you lose your authenticator device.</p>
                <div class="backup-codes-grid">
                    {codes_grid}
                </div>
                <p><small><strong>Security Note:</strong> Each code can only be used once. After using a backup code, it will be permanently disabled.</small></p>
            </div>
            """
        
        content = f"""
        <p>Hello <strong>{user_name}</strong>,</p>
        
        <div class="alert alert-success">
            <strong>🎉 Excellent!</strong> Multi-Factor Authentication (MFA) has been successfully enabled for your Infra Mind account.
        </div>
        
        <h2>🛡️ What This Means</h2>
        <p>Your account now has an additional layer of security. When signing in, you'll need to provide:</p>
        <ul>
            <li><strong>Your password</strong> (something you know)</li>
            <li><strong>A 6-digit code</strong> from your authenticator app (something you have)</li>
        </ul>
        
        {backup_codes_html}
        
        <div class="tips-list">
            <h3>🔐 Security Best Practices</h3>
            <ul>
                <li><strong>Keep your authenticator app secure</strong> - Use a device lock (PIN, fingerprint, face ID)</li>
                <li><strong>Don't share your codes</strong> - Never give your 6-digit codes to anyone</li>
                <li><strong>Store backup codes safely</strong> - Keep them in a password manager or secure location</li>
                <li><strong>Use multiple devices</strong> - Consider setting up the same account on multiple authenticator apps</li>
                <li><strong>Regular backups</strong> - Some authenticator apps support cloud backup</li>
            </ul>
        </div>
        
        <div class="security-notice">
            <h3>🚨 Important Security Alert</h3>
            <p>If you did <strong>NOT</strong> enable MFA yourself, please:</p>
            <ul>
                <li>Change your password immediately</li>
                <li>Review your account activity</li>
                <li>Contact our support team</li>
            </ul>
        </div>
        
        <h2>📱 Next Steps</h2>
        <p>Your MFA setup is now complete! The next time you sign in, you'll be prompted to enter a 6-digit code from your authenticator app.</p>
        
        <div style="text-align: center; margin: 30px 0;">
            <a href="{{FRONTEND_URL}}/auth/login" class="button">Sign In to Test MFA</a>
        </div>
        
        <p>If you need help or have questions about MFA, please visit our security documentation or contact support.</p>
        
        <p>Stay secure,<br>
        <strong>The Infra Mind Security Team</strong></p>
        """
        
        html_content = self._get_base_email_template("MFA Enabled", "#28a745")
        html_content = html_content.replace("{{HEADER_TITLE}}", "🔒 MFA Enabled Successfully")
        html_content = html_content.replace("{{HEADER_SUBTITLE}}", "Your account is now more secure")
        html_content = html_content.replace("{{CONTENT}}", content)
        html_content = html_content.replace("{{FRONTEND_URL}}", os.getenv('FRONTEND_URL', 'http://localhost:3000'))
        
        text_content = f"""
        MFA Successfully Enabled
        
        Hello {user_name},
        
        Multi-Factor Authentication (MFA) has been successfully enabled for your Infra Mind account.
        
        Your account now requires both your password and a 6-digit code from your authenticator app when signing in.
        
        IMPORTANT: Save your backup codes in a safe place:
        {', '.join(backup_codes) if backup_codes else 'Backup codes were provided during setup'}
        
        Security Best Practices:
        - Keep your authenticator app secure
        - Don't share your 6-digit codes with anyone
        - Store backup codes in a password manager
        - Use multiple devices for redundancy
        
        If you didn't enable MFA, please change your password immediately and contact support.
        
        Stay secure,
        The Infra Mind Security Team
        
        Sign in to test: {os.getenv('FRONTEND_URL', 'http://localhost:3000')}/auth/login
        """
        
        return await self.send_email(to_email, subject, html_content, text_content)

    async def send_mfa_login_alert(self, to_email: str, user_name: str, login_info: dict = None) -> bool:
        """
        Send security alert when MFA login occurs.
        
        Args:
            to_email: User's email address
            user_name: User's name
            login_info: Dictionary with login details (IP, location, device, etc.)
            
        Returns:
            bool: True if email sent successfully
        """
        subject = "🔐 Secure Login to Your Infra Mind Account"
        
        # Format login information
        login_details = ""
        if login_info:
            login_time = login_info.get('timestamp', 'Unknown time')
            ip_address = login_info.get('ip_address', 'Unknown IP')
            user_agent = login_info.get('user_agent', 'Unknown device')
            location = login_info.get('location', 'Unknown location')
            
            login_details = f"""
            <div class="alert alert-info">
                <h3>📋 Login Details</h3>
                <ul style="margin: 10px 0; list-style: none; padding: 0;">
                    <li><strong>Time:</strong> {login_time}</li>
                    <li><strong>IP Address:</strong> {ip_address}</li>
                    <li><strong>Location:</strong> {location}</li>
                    <li><strong>Device:</strong> {user_agent}</li>
                </ul>
            </div>
            """
        
        content = f"""
        <p>Hello <strong>{user_name}</strong>,</p>
        
        <div class="alert alert-success">
            <strong>✅ Secure Login Successful</strong><br>
            Someone just signed in to your Infra Mind account using Multi-Factor Authentication.
        </div>
        
        {login_details}
        
        <h2>🔒 Why You're Receiving This</h2>
        <p>We send this notification whenever someone successfully logs into your account using MFA. This helps you monitor your account security and detect any unauthorized access.</p>
        
        <div class="security-notice">
            <h3>🚨 Wasn't You?</h3>
            <p>If you didn't just sign in to your account, please take immediate action:</p>
            <ul>
                <li><strong>Change your password</strong> right away</li>
                <li><strong>Review your account activity</strong> for suspicious actions</li>
                <li><strong>Check your authenticator app</strong> for any unauthorized setup</li>
                <li><strong>Contact our support team</strong> immediately</li>
            </ul>
            
            <div style="text-align: center; margin: 20px 0;">
                <a href="{{FRONTEND_URL}}/auth/change-password" class="button" style="background: #dc3545;">Secure My Account</a>
            </div>
        </div>
        
        <div class="tips-list">
            <h3>🛡️ Account Security Tips</h3>
            <ul>
                <li>Never share your MFA codes with anyone</li>
                <li>Use a strong, unique password</li>
                <li>Keep your backup codes in a secure location</li>
                <li>Sign out from shared or public computers</li>
                <li>Monitor your account activity regularly</li>
            </ul>
        </div>
        
        <p>Thank you for keeping your account secure with Multi-Factor Authentication!</p>
        
        <p>Best regards,<br>
        <strong>The Infra Mind Security Team</strong></p>
        """
        
        html_content = self._get_base_email_template("Secure Login Alert", "#17a2b8")
        html_content = html_content.replace("{{HEADER_TITLE}}", "🔐 Secure Login Detected")
        html_content = html_content.replace("{{HEADER_SUBTITLE}}", "MFA login to your account")
        html_content = html_content.replace("{{CONTENT}}", content)
        html_content = html_content.replace("{{FRONTEND_URL}}", os.getenv('FRONTEND_URL', 'http://localhost:3000'))
        
        text_content = f"""
        Secure Login to Your Infra Mind Account
        
        Hello {user_name},
        
        Someone just signed in to your Infra Mind account using Multi-Factor Authentication.
        
        Login Details:
        {f"Time: {login_info.get('timestamp')}" if login_info else ""}
        {f"IP: {login_info.get('ip_address')}" if login_info else ""}
        {f"Location: {login_info.get('location')}" if login_info else ""}
        
        If this wasn't you:
        1. Change your password immediately
        2. Review your account activity
        3. Contact our support team
        
        Thank you for using MFA to keep your account secure!
        
        The Infra Mind Security Team
        """
        
        return await self.send_email(to_email, subject, html_content, text_content)

    async def send_mfa_disabled_email(self, to_email: str, user_name: str) -> bool:
        """
        Send notification when MFA is disabled.
        
        Args:
            to_email: User's email address
            user_name: User's name
            
        Returns:
            bool: True if email sent successfully
        """
        subject = "⚠️ Multi-Factor Authentication Disabled"
        
        content = f"""
        <p>Hello <strong>{user_name}</strong>,</p>
        
        <div class="alert alert-warning">
            <strong>⚠️ Security Notice</strong><br>
            Multi-Factor Authentication (MFA) has been disabled for your Infra Mind account.
        </div>
        
        <h2>🔓 What This Means</h2>
        <p>Your account now only requires your password to sign in. This reduces your account security compared to having MFA enabled.</p>
        
        <div class="security-notice">
            <h3>🚨 Didn't Disable MFA?</h3>
            <p>If you did <strong>NOT</strong> disable MFA yourself, your account may be compromised. Please:</p>
            <ul>
                <li><strong>Change your password</strong> immediately</li>
                <li><strong>Re-enable MFA</strong> right away</li>
                <li><strong>Review your account activity</strong></li>
                <li><strong>Contact our support team</strong></li>
            </ul>
            
            <div style="text-align: center; margin: 20px 0;">
                <a href="{{FRONTEND_URL}}/auth/mfa-setup" class="button">Re-enable MFA</a>
            </div>
        </div>
        
        <h2>🛡️ Why We Recommend MFA</h2>
        <p>Multi-Factor Authentication provides an additional layer of security by requiring:</p>
        <ul>
            <li>Something you know (your password)</li>
            <li>Something you have (your phone/authenticator app)</li>
        </ul>
        
        <p>This makes it much harder for attackers to access your account, even if they somehow obtain your password.</p>
        
        <div style="text-align: center; margin: 30px 0;">
            <a href="{{FRONTEND_URL}}/auth/mfa-setup" class="button">Set Up MFA Again</a>
        </div>
        
        <p>We strongly recommend re-enabling MFA to keep your account secure.</p>
        
        <p>Stay safe,<br>
        <strong>The Infra Mind Security Team</strong></p>
        """
        
        html_content = self._get_base_email_template("MFA Disabled", "#ffc107")
        html_content = html_content.replace("{{HEADER_TITLE}}", "⚠️ MFA Disabled")
        html_content = html_content.replace("{{HEADER_SUBTITLE}}", "Your account security has been reduced")
        html_content = html_content.replace("{{CONTENT}}", content)
        html_content = html_content.replace("{{FRONTEND_URL}}", os.getenv('FRONTEND_URL', 'http://localhost:3000'))
        
        text_content = f"""
        Multi-Factor Authentication Disabled
        
        Hello {user_name},
        
        MFA has been disabled for your Infra Mind account.
        
        Your account now only requires your password to sign in.
        
        If you didn't disable MFA:
        1. Change your password immediately
        2. Re-enable MFA at: {os.getenv('FRONTEND_URL', 'http://localhost:3000')}/auth/mfa-setup
        3. Contact our support team
        
        We strongly recommend using MFA for better account security.
        
        The Infra Mind Security Team
        """
        
        return await self.send_email(to_email, subject, html_content, text_content)


# Global email service instance
email_service = EmailService()