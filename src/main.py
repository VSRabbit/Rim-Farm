import threading
import time
import json
from motor_control import MotorController
from camera_module import CameraModule
from email_module import EmailNotifier
from logger_utils import setup_logger

logger = setup_logger("main", "main")

def load_config():
    with open('config/config.json') as f:
        return json.load(f)

def run_motor_controller(motor):
    while True:
        now = time.strftime("%H:%M")
        motor.check_and_control(now)
        time.sleep(30) 

def run_camera_module(camera):
    while True:
        now = time.strftime("%H:%M")
        camera.check_and_capture(now)
        time.sleep(30) 

def run_email_module(email):
    while True:
        email.check_emails()
        time.sleep(60) 

def main():
    try:
        config = load_config()
        logger.info("Configuration loaded successfully")
        
        # initialize modules
        motor = MotorController(config['motor'])
        camera = CameraModule(config['camera'])
        email = EmailNotifier(config['email'])
        logger.info("All modules initialized")
        
        # launch threads
        motor_thread = threading.Thread(target=run_motor_controller, args=(motor,), daemon=True)
        camera_thread = threading.Thread(target=run_camera_module, args=(camera,), daemon=True)
        email_thread = threading.Thread(target=run_email_module, args=(email,), daemon=True)
        
        motor_thread.start()
        camera_thread.start()
        email_thread.start()
        logger.info("All threads started")
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Stopping application...")
            motor.cleanup()
            email.close()
            logger.info("Application stopped")
            
    except Exception as e:
        logger.error(f"Application error: {str(e)}")
        raise

if __name__ == "__main__":
    main()
