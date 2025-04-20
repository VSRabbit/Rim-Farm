import os
import time
from datetime import datetime
import subprocess
from pathlib import Path
import json

class CameraModule:
    def __init__(self, config):
        
        self.capture_times = config.get("capture_times", ["12:00","18:00"])
        self.save_path = Path(config.get("save_path", "cam"))
        self.rotation = config.get("rotation", 0)
        self.quality = config.get("quality", 90)

        self.resolution = config.get("resolution", "640x480")
        self.width, self.height = map(int, self.resolution.split('x'))

        self.save_path.mkdir(parents=True, exist_ok=True)

    def take_photo(self):

        timestamp = datetime.now().strftime("%Y-%m-%d-%H%M")
        filename = f"{timestamp}.jpg"
        filepath = self.save_path / filename
        
        command = [
            "libcamera-jpeg",
            "-o", str(filepath),
            "--quality", str(self.quality),
            "--rotation", str(self.rotation),
            "--width", str(self.width),
            "--height", str(self.height),
        ]
        
        try:
            subprocess.run(command, check=True, capture_output=True)
            return True
        except subprocess.CalledProcessError as e:
            print(f"Failed to cap: {e.stderr.decode('utf-8')}")
            return False

    def should_capture(self, current_time):
        return current_time in self.capture_times

    def check_and_capture(self, current_time_str):
        if self.should_capture(current_time_str):
            print(f"[{current_time_str}] cap")
            if self.take_photo():
                print(f"[{current_time_str}] capture success")
            else:
                print(f"[{current_time_str}] capture failed")

if __name__ == "__main__":

    from time import sleep
    from datetime import datetime
    

    test_config = {
        "capture_times": [datetime.now().strftime("%H:%M")],  # use current time for testing
        "save_path": "test_cam",
        "rotation": 0,
        "quality": 85,
        "resolution": "2592x1944"
    }
    
    camera = CameraModule(test_config)
    current_time = datetime.now().strftime("%H:%M")
    camera.check_and_capture(current_time)
