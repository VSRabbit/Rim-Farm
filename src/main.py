import threading
import time
import json
from motor_control import MotorController
from camera_module import CameraModule
# from email_module import EmailNotifier

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
    config = load_config()
    
    # initialize modules
    motor = MotorController(config['motor'])
    camera = CameraModule(config['camera'])
    # email = EmailNotifier(config['email'])
    
    # launch threads
    motor_thread = threading.Thread(target=run_motor_controller, args=(motor,), daemon=True)
    camera_thread = threading.Thread(target=run_camera_module, args=(camera,), daemon=True)
    # email_thread = threading.Thread(target=run_email_module, args=(email,), daemon=True)
    
    motor_thread.start()
    camera_thread.start()
    # email_thread.start()
    
    try:
        # keep-alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nstopping...")
        motor.cleanup()
        # email.close()

if __name__ == "__main__":
    main()
