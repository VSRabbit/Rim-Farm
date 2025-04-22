import os
import time
from datetime import datetime
import subprocess
from pathlib import Path
import json
import logging

class CameraModule:
    def __init__(self, config):
        # Configure logging

        log_dir = Path("logs")
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / f"camera_{datetime.now().strftime('%Y-%m-%d')}.log"

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]

        )
        self.logger = logging.getLogger(__name__)
        
        try:
            # Load configuration
            self.capture_times = config.get("capture_times", ["12:00","18:00"])
            self.save_path = Path(config.get("save_path", "cam"))
            self.rotation = config.get("rotation", 0)
            self.quality = config.get("quality", 90)
            self.resolution = config.get("resolution", "640x480")
            self.width, self.height = map(int, self.resolution.split('x'))
            #advanced settings
            self.awb = config.get("awb", "auto")
            self.metering = config.get("metering","centre")
            self.exposure = config.get("exposure", "normal")
            self.denoise = config.get("denoise", "auto")
            # Ensure save path exists and has write permissions
            self.save_path.mkdir(parents=True, exist_ok=True)
            
            # Verify if libcamera-jpeg is available
            self._check_camera()
            
        except Exception as e:
            self.logger.error(f"Failed to initialize camera module: {str(e)}")
            raise

    def _check_camera(self):
        """Check if camera is available"""
        try:
            result = subprocess.run(
                ["libcamera-jpeg", "--help"],
                capture_output=True,
                timeout=5
            )
            if result.returncode != 0:
                raise RuntimeError("libcamera-jpeg is not available")
        except Exception as e:
            self.logger.error(f"Camera check failed: {str(e)}")
            raise RuntimeError("Camera system is not available") from e

    def take_photo(self):
        timestamp = datetime.now().strftime("%Y-%m-%d-%H%M")
        filename = f"{timestamp}.jpg"
        filepath = self.save_path / filename
        
        self.logger.info(f"Starting photo capture, saving to: {filepath}")
        
        command = [
            "libcamera-jpeg",
            "-o", str(filepath),
            "--quality", str(self.quality),
            "--rotation", str(self.rotation),
            "--width", str(self.width),
            "--height", str(self.height),
            "--nopreview",  # No preview mode

            "--awb",str(self.awb) ,
            "--metering", str(self.metering),
            "--exposure", str(self.exposure),
            "--denoise", str(self.denoise)
        ]
        
        try:
            result = subprocess.run(
                command, 
                check=True, 
                capture_output=True,
                timeout=30  # Add timeout
            )
            
            return True
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Photo capture failed: {e.stderr.decode('utf-8')}")
            return False
        except subprocess.TimeoutExpired:
            self.logger.error("Photo capture timed out")
            return False
        except Exception as e:
            self.logger.error(f"Unknown error during photo capture: {str(e)}")
            return False

    def should_capture(self, current_time):
        try:
            return current_time in self.capture_times
        except Exception as e:
            self.logger.error(f"Error checking capture time: {str(e)}")
            return False

    def check_and_capture(self, current_time_str):
        try:
            if self.should_capture(current_time_str):
                self.logger.info(f"[{current_time_str}] Starting capture")
                if self.take_photo():
                    self.logger.info(f"[{current_time_str}] Capture successful")
                else:
                    self.logger.error(f"[{current_time_str}] Capture failed")
                
        except Exception as e:
            self.logger.error(f"Error during capture process: {str(e)}")

if __name__ == "__main__":
    from time import sleep
    from datetime import datetime

    test_config = {
        "capture_times": [datetime.now().strftime("%H:%M")],  # use current time for testing
        "save_path": "test_cam",
        "rotation": 0,
        "quality": 100,
        "resolution": "2592x1944",
        # advanced settings
        "awb":"auto",
        "metering": "centre",
        "exposure": "normal",
        "denoise": "auto"

    }
    
    camera = CameraModule(test_config)
    current_time = datetime.now().strftime("%H:%M")
    camera.check_and_capture(current_time)
