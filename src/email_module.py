import os
import json
import smtplib
import imaplib
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from datetime import datetime, timedelta

class EmailNotifier:
    def __init__(self, config):
        self.sender_email = config['sender_email']
        self.sender_password = config['sender_password']
        self.whitelist = config['whitelist']
        self.server = None
        self.sent_requests = {}  # track sent requests
        
    def connect_smtp(self):
        try:
            self.server = smtplib.SMTP('smtp-mail.outlook.com', 587)
            self.server.starttls()
            self.server.login(self.sender_email, self.sender_password)
            return True
        except Exception as e:
            print(f"SMTP server connect fail: {e}")
            return False
    
    def connect_imap(self):
        try:
            imap = imaplib.IMAP4_SSL('imap-mail.outlook.com')
            imap.login(self.sender_email, self.sender_password)
            return imap
        except Exception as e:
            print(f"IMAP server connect fail: {e}")
            return None
    
    def get_recent_images(self, count=18):
        images = []
        if os.path.exists('cam'):
            files = sorted(os.listdir('cam'), reverse=True)
            for f in files[:count]:
                if f.endswith('.jpg'):
                    images.append(os.path.join('cam', f))
        return images
    
    def send_images(self, recipient, images):
        if not self.server and not self.connect_smtp():
            return False
        
        msg = MIMEMultipart()
        msg['From'] = self.sender_email
        msg['To'] = recipient
        msg['Subject'] = "Recent Monitoring Images"
        
        text = MIMEText("Here are some recent recorded images:", 'plain')
        msg.attach(text)
        
        for img_path in images:
            with open(img_path, 'rb') as f:
                img_data = f.read()
            image = MIMEImage(img_data, name=os.path.basename(img_path))
            msg.attach(image)
        
        try:
            self.server.sendmail(self.sender_email, recipient, msg.as_string())
            print(f"Images sent to {recipient}")
            return True
        except Exception as e:
            print(f"Fail to send to {recipient}: {e}")
            return False
    
    def check_emails(self):
        imap = self.connect_imap()
        if not imap:
            return False
        
        try:
            imap.select('inbox')
            
            since_date = (datetime.now() - timedelta(days=1)).strftime('%d-%b-%Y')
            status, messages = imap.search(None, f'(SINCE "{since_date}" SUBJECT "check")')
            
            if status != 'OK':
                print("Failed to search emails")
                return False
            
            email_ids = messages[0].split()
            
            for email_id in email_ids:
                # get the email
                status, msg_data = imap.fetch(email_id, '(RFC822)')
                if status != 'OK':
                    continue
                
                raw_email = msg_data[0][1]
                email_message = email.message_from_bytes(raw_email)
                
                # check if the sender is in the whitelist
                sender = email.utils.parseaddr(email_message['From'])[1]
                if sender not in self.whitelist:
                    continue
                
                # check if the subscriber's subject contains "check"
                subject = email_message['Subject']
                if subject.lower() != 'check':
                    continue
                
                # check if the request is already done
                if email_id in self.sent_requests:
                    continue
                
                # record the request
                self.sent_requests[email_id] = datetime.now().isoformat()
                
                # send images to the sender
                images = self.get_recent_images()
                if images:
                    self.send_images(sender, images)
            
            # cleanup old requests
            week_ago = datetime.now() - timedelta(days=31)
            self.sent_requests = {k: v for k, v in self.sent_requests.items() 
                                if datetime.fromisoformat(v) > week_ago}
            
            return True
            
        except Exception as e:
            print(f"Error checking emails: {e}")
            return False
        finally:
            imap.close()
            imap.logout()
    
    def close(self):
        if self.server:
            self.server.quit()
