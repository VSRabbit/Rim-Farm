import os
import json
import time
import logging
from datetime import datetime
from pathlib import Path
import imaplib
import smtplib
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.header import decode_header
import email
import threading
from logger_utils import setup_logger

# Configure logging
log_dir = Path("logs")
log_dir.mkdir(parents=True, exist_ok=True)
email_log_file = log_dir / f"email_{datetime.now().strftime('%Y-%m-%d')}.log"

email_logger = logging.getLogger("email")
email_logger.setLevel(logging.INFO)
if not email_logger.handlers:
    fh = logging.FileHandler(email_log_file, encoding="utf-8")
    sh = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    fh.setFormatter(formatter)
    sh.setFormatter(formatter)
    email_logger.addHandler(fh)
    email_logger.addHandler(sh)

class EmailNotifier:
    def __init__(self, config):
        self.logger = setup_logger("email", "email")
        self.email = config['sender_email']
        self.password = config['sender_password']
        self.subscribers = config['subscribers']
        self.cam_path = Path("cam")
        self.last_imap_check = 0
        self.last_smtp_check = 0
        self.check_interval = 300  # 5 minutes
        self.imap = None
        self.smtp = None

    def ensure_imap_connection(self):
        """Ensure IMAP connection is active"""
        try:
            if self.imap:
                try:
                    self.imap.noop()
                    return True
                except:
                    self.logger.debug("IMAP connection lost")
                    
            # Create new IMAP connection
            self.imap = imaplib.IMAP4_SSL("imap.qq.com", 993)
            self.imap.login(self.email, self.password)
            self.logger.info("IMAP connection established")
            return True
            
        except Exception as e:
            self.logger.error(f"IMAP connection failed: {str(e)}")
            self.imap = None
            return False

    def ensure_smtp_connection(self):
        """Ensure SMTP connection is active"""
        try:
            if self.smtp:
                try:
                    self.smtp.noop()
                    return True
                except:
                    self.logger.debug("SMTP connection lost")
                    
            # Create new SMTP connection
            self.smtp = smtplib.SMTP_SSL("smtp.qq.com", 465, timeout=30)
            self.smtp.login(self.email, self.password)
            self.logger.info("SMTP connection established")
            return True
            
        except Exception as e:
            self.logger.error(f"SMTP connection failed: {str(e)}")
            self.smtp = None
            return False

    def get_latest_images(self, num=6):
        """Get latest 10 images"""
        try:
            if not self.cam_path.exists():
                self.logger.warning(f"Camera path not found: {self.cam_path}")
                return []
                
            self.logger.debug(f"Scanning for images in: {self.cam_path}")
            images = sorted(
                [f for f in self.cam_path.glob("*.jpg")],
                key=lambda x: x.stat().st_mtime,
                reverse=True
            )
            
            selected_images = images[:num]
            self.logger.info(f"Found {len(selected_images)} images")
            return selected_images
            
        except Exception as e:
            self.logger.error(f"Error getting latest images: {str(e)}")
            return []
            
    def send_with_retry(self, msg, to_addr, max_retries=3):
        """Send email with retry mechanism"""
        for attempt in range(max_retries):
            try:
                # Create new connection for each attempt
                if hasattr(self, 'smtp'):
                    try:
                        self.smtp.quit()
                    except:
                        pass
                
                # Establish connection and send immediately
                self.smtp = smtplib.SMTP_SSL("smtp.qq.com", 465, timeout=30)
                self.smtp.login(self.email, self.password)
                self.logger.info("SMTP connection established")
                time.sleep(10)   # wait for stable connection
                # Send email
                self.smtp.sendmail(self.email, to_addr, msg.as_string())
                self.logger.info("SMTP send successful")
                
                # Close connection after sending
                try:
                    self.smtp.quit()
                except:
                    pass
                
                return True
                
            except Exception as e:
                self.logger.error(f"Send attempt {attempt + 1} failed: {str(e)}")
                if attempt < max_retries - 1:
                    self.logger.info(f"Waiting 15 seconds before retry {attempt + 2}")
                    time.sleep(15)
                    continue
                
        self.smtp = None
        return False

    def send_response(self, to_addr, images):
        """Send response email with images"""
        try:
            msg = MIMEMultipart()
            msg['Subject'] = 'Plant Photos Response'
            msg['From'] = self.email
            msg['To'] = to_addr
            
            # Add text content
            text = MIMEText(f"Here are the latest {len(images)} photos.", 'plain')
            msg.attach(text)
            
            # Add images with progress logging and size limit check
            total_size = 0
            processed_images = []
            
            for i, img_path in enumerate(images, 1):
                self.logger.debug(f"Processing image {i}/{len(images)}: {img_path.name}")
                try:
                    with open(img_path, 'rb') as f:
                        img_data = f.read()
                        img_size = len(img_data)
                        
                        # Check individual image size (5MB limit)
                        if img_size > 5 * 1024 * 1024:
                            self.logger.warning(f"Skipping {img_path.name}: size {img_size/1024/1024:.1f}MB exceeds 5MB limit")
                            continue
                            
                        # Check accumulated size
                        if total_size + img_size > 20 * 1024 * 1024:
                            self.logger.warning("Total size would exceed 20MB limit, stopping here")
                            break
                            
                        img = MIMEImage(img_data)
                        img.add_header('Content-Disposition', 'attachment', filename=img_path.name)
                        msg.attach(img)
                        total_size += img_size
                        processed_images.append(img_path.name)
                        
                except Exception as e:
                    self.logger.error(f"Failed to process image {img_path}: {str(e)}")
                    continue
            
            if not processed_images:
                self.logger.error("No images were successfully processed")
                return False
                
            self.logger.info(f"Attempting to send email with {len(processed_images)} images ({total_size/1024/1024:.1f}MB)")
            
            # Send email with retry mechanism
            try:
                if self.send_with_retry(msg, to_addr):
                    self.logger.info(f"Successfully sent response to {to_addr}")
                    return True
                else:
                    self.logger.error("All send attempts failed")
                    return False
                    
            except Exception as e:
                self.logger.error(f"Failed to send response: {str(e)}")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to send response: {str(e)}")
            return False

    def process_email(self, num):
        """Process a single email and send response if needed
        
        Args:
            num: Email message number/ID
            
        Returns:
            bool: True if processed successfully and should be marked as read
        """
        # Get email content
        _, msg = self.imap.fetch(num, '(RFC822)')
        email_body = msg[0][1]
        email_message = email.message_from_bytes(email_body)
        
        # Get sender and subject
        subject = decode_header(email_message["Subject"])[0][0]
        if isinstance(subject, bytes):
            subject = subject.decode()
        
        from_addr = email.utils.parseaddr(email_message["From"])[1]
        
        # Check if this is a valid request
        if from_addr in self.subscribers and "check" in subject.lower():
            self.logger.info(f"Processing check request from {from_addr}")
            images = self.get_latest_images()
            
            if images:
                if self.send_response(from_addr, images):
                    return True
                else:
                    self.logger.error(f"Failed to send response to {from_addr}")
                    return False
            else:
                self.logger.warning("No images available to send")
                return False
        else:
            self.logger.debug(f"Skipping email from {from_addr}, subject: {subject}")
            return False

    def check_emails(self):
        """Check new emails"""
        if not self.ensure_imap_connection():
            return

        try:
            self.imap.select('INBOX')
            _, messages = self.imap.search(None, 'UNSEEN')
            
            if not messages[0]:
                return
                
            for num in messages[0].split():
                try:
                    # Process email and send response
                    if self.process_email(num):
                        # Ensure connection before marking as read
                        if self.ensure_imap_connection():
                            try:
                                self.imap.store(num, '+FLAGS', '\\Seen')
                                self.logger.info(f"Message {num} marked as read")
                            except Exception as e:
                                self.logger.error(f"Failed to mark message {num} as read: {str(e)}")
                        else:
                            self.logger.error("Lost IMAP connection while trying to mark message as read")
                    
                except Exception as e:
                    self.logger.error(f"Error processing email {num}: {str(e)}")
                    continue
                    
        except Exception as e:
            self.logger.error(f"Error checking emails: {str(e)}")
            self.imap = None  # Force reconnection next time

    def close(self):
        """Close all connections"""
        if self.imap:
            try:
                self.imap.logout()
            except:
                pass
                
        if self.smtp:
            try:
                self.smtp.quit()
            except:
                pass
                
        self.logger.info("All connections closed")

def start_email_service(config_path="config/config.json"):
    """Start email service"""
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        email_notifier = EmailNotifier(config['email'])
        
        while True:
            email_notifier.check_emails()
            time.sleep(300)  # Check every 5 minutes
            
    except Exception as e:
        email_logger.error(f"Failed to start email service: {str(e)}")

if __name__ == "__main__":
    start_email_service()
