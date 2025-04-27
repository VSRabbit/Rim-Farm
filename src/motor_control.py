import RPi.GPIO as GPIO
from datetime import datetime
import os
from pathlib import Path
from logger_utils import setup_logger

WATER_PIN = 20
AIR_PIN = 21

class MotorController:
    
    def __init__(self, config):
        GPIO.setmode(GPIO.BCM)
        self.logger = setup_logger("motor", "motor")
        self.working_hours = config['working_hours']
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(WATER_PIN, GPIO.OUT) # Water pump
        GPIO.setup(AIR_PIN, GPIO.OUT)   # Air pump
        self.current_state = False
        
    def is_working_time(self, time_str):
        now = datetime.strptime(time_str, "%H:%M").time()
        for period in self.working_hours:
            start = datetime.strptime(period["start"], "%H:%M").time()
            end = datetime.strptime(period["end"], "%H:%M").time()
            if start <= now <= end:
                return True
        return False
    
    def control_motor(self, activate):
        GPIO.output(WATER_PIN, GPIO.HIGH if activate else GPIO.LOW)
        GPIO.output(AIR_PIN, GPIO.HIGH if activate else GPIO.LOW)
        self.current_state = activate
        self.logger.info(f"Motor {'activated' if activate else 'deactivated'}")
    
    def check_and_control(self, time_str):
        should_activate = self.is_working_time(time_str)
        if should_activate != self.current_state:
            self.control_motor(should_activate)
        else:
            # force synchronize the state with the current time
            GPIO.output(WATER_PIN, GPIO.HIGH if should_activate else GPIO.LOW)
            GPIO.output(AIR_PIN, GPIO.HIGH if should_activate else GPIO.LOW)
            self.current_state = should_activate
    
    def cleanup(self):
        GPIO.cleanup()
        self.logger.info("GPIO cleaned up")
