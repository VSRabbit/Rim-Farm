import RPi.GPIO as GPIO
from datetime import datetime
import logging
import os
from pathlib import Path

WATER_PIN = 20
AIR_PIN = 21

# Logging configuration
log_dir = Path("logs")
log_dir.mkdir(parents=True, exist_ok=True)

log_file = log_dir / f"motor_{datetime.now().strftime('%Y-%m-%d')}.log"

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),  # Output to screen
        logging.FileHandler(log_file, encoding="utf-8")  # Output to file
    ]
)

class MotorController:
    
    def __init__(self, config):
        GPIO.setmode(GPIO.BCM)
        self.working_hours = config['working_hours']
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(WATER_PIN, GPIO.OUT) # Water pump
        GPIO.setup(AIR_PIN, GPIO.OUT)   # Air pump
        self.current_state = False
        logging.info("MotorController initialized. Working hours: %s", self.working_hours)
        
    def is_working_time(self, time_str):
        now = datetime.strptime(time_str, "%H:%M").time()
        logging.debug(f"Checking time: {now}")
        for period in self.working_hours:
            start = datetime.strptime(period["start"], "%H:%M").time()
            end = datetime.strptime(period["end"], "%H:%M").time()
            # logging.debug(f"Period: {start} - {end}")
            if start <= now <= end:
                logging.info(f"{time_str} is within working period {start}-{end}")
                return True
        logging.info(f"{time_str} is not within any working period")
        return False
    
    def control_motor(self, activate):
        GPIO.output(WATER_PIN, GPIO.HIGH if activate else GPIO.LOW)
        GPIO.output(AIR_PIN, GPIO.HIGH if activate else GPIO.LOW)
        self.current_state = activate
        logging.info(f"Motor {'activated' if activate else 'deactivated'}")
    
    def check_and_control(self, time_str):
        should_activate = self.is_working_time(time_str)
        if should_activate != self.current_state:
            self.control_motor(should_activate)
            logging.debug(f"Motor state changed to {should_activate}")
        else:
            logging.debug(f"Motor state remains {self.current_state}")
    
    def cleanup(self):
        GPIO.cleanup()
        logging.info("GPIO cleaned up")
