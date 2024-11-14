
import time
import random
import threading
from dataclasses import dataclass
import numpy as np
import logging
from typing import List, Dict, Tuple
from enum import Enum

# set up basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("safety_system")

# sensor types - might add more later
class SensorTypes(Enum):
    ACCEL = "accelerometer"     # for crash detection
    GYRO = "gyroscope"         # for rollover
    IMPACT = "impact"          # direct collision 
    PROX = "proximity"         # distance sensing
    MAG = "magnetic"           # for cover alignment

# thresholds for my sensors - tested these values
SENSOR_SETTINGS = {
    "accel_threshold": 2.5,    # g-force
    "gyro_threshold": 45.0,    # deg/sec
    "impact_threshold": 4.0,   # kN
    "prox_threshold": 0.15,    # meters
    "mag_threshold": 0.5       # tesla
}

class SafetyComponent:
    def __init__(self, name, has_magnets=False):
        self.name = name
        self.deployed = False
        self.magnets_active = False
        self.has_magnets = has_magnets
        self._last_check = time.time()
        
    def deploy(self):
        # quick safety check before deployment
        if not self.deployed:
            try:
                # simulate actuator movement
                time.sleep(0.1)  
                self.deployed = True
                logger.info(f"{self.name} deployed")
                return True
            except Exception as e:
                logger.error(f"Failed to deploy {self.name}: {e}")
                return False
        return True
    
    def retract(self):
        if self.deployed:
            try:
                if self.has_magnets:
                    self.deactivate_magnets()
                time.sleep(0.1)
                self.deployed = False
                logger.info(f"{self.name} retracted")
                return True
            except Exception as e:
                logger.error(f"Couldn't retract {self.name}: {e}")
                return False
        return True
    
    # magnet control functions
    def activate_magnets(self):
        if self.has_magnets:
            self.magnets_active = True
            logger.info(f"Magnets activated for {self.name}")
    
    def deactivate_magnets(self):
        if self.has_magnets:
            self.magnets_active = False

class SensorReader:
    def __init__(self):
        # initialize sensor communication
        self.running = True
        self._last_readings = {}
        
    def read_accelerometer(self) -> List[float]:
        # returns [x, y, z] acceleration
        return [random.gauss(0, 0.1) for _ in range(3)]
    
    def read_gyroscope(self) -> List[float]:
        # returns [roll, pitch, yaw]
        return [random.gauss(0, 0.5) for _ in range(3)]
    
    def read_impact(self) -> float:
        # simulated impact force
        return abs(random.gauss(0, 0.2))
    
    def read_proximity(self) -> float:
        # distance in meters
        return abs(random.gauss(1.0, 0.05))
    
    def read_magnetic(self) -> float:
        # magnetic field strength
        return abs(random.gauss(0.1, 0.01))
    
    def check_emergency(self) -> Tuple[bool, str]:
        # check all sensors for emergency conditions
        emergency = False
        reason = ""
        
        # check accelerometer
        accel = self.read_accelerometer()
        if max(abs(x) for x in accel) > SENSOR_SETTINGS["accel_threshold"]:
            emergency = True
            reason = "High acceleration detected"
        
        # check gyroscope
        gyro = self.read_gyroscope()
        if max(abs(x) for x in gyro) > SENSOR_SETTINGS["gyro_threshold"]:
            emergency = True
            reason = "Possible rollover detected"
        
        # check impact
        impact = self.read_impact()
        if impact > SENSOR_SETTINGS["impact_threshold"]:
            emergency = True
            reason = "Impact detected"
        
        # store readings for later
        self._last_readings = {
            "accel": accel,
            "gyro": gyro,
            "impact": impact,
            "prox": self.read_proximity(),
            "mag": self.read_magnetic()
        }
        
        return emergency, reason

class SafetySystem:
    def __init__(self):
        # create my components
        self.front = SafetyComponent("front_cover", has_magnets=True)
        self.left = SafetyComponent("left_cover", has_magnets=True)
        self.right = SafetyComponent("right_cover", has_magnets=True)
        self.back = SafetyComponent("back_cover")
        self.body = SafetyComponent("body_cover")
        
        self.sensor_reader = SensorReader()
        self.monitoring = False
        self.monitor_thread = None
        
        # for tracking system state
        self.emergency_active = False
        self.last_deployment = None
        
        logger.info("Safety system initialized")
    
    def start_monitoring(self):
        """Start watching for emergencies"""
        if not self.monitoring:
            self.monitoring = True
            self.monitor_thread = threading.Thread(target=self._monitor_loop)
            self.monitor_thread.start()
            logger.info("Started monitoring")
    
    def stop_monitoring(self):
        """Stop the monitoring loop"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join()
            logger.info("Stopped monitoring")
    
    def _monitor_loop(self):
        while self.monitoring:
            try:
                emergency, reason = self.sensor_reader.check_emergency()
                
                if emergency and not self.emergency_active:
                    logger.warning(f"Emergency detected: {reason}")
                    self.deploy_protection()
                
                # don't need to check too often
                time.sleep(0.02)  # 50Hz is enough
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                self.monitoring = False
    
    def deploy_protection(self):
        """Deploy everything in the right order"""
        if self.emergency_active:
            return
        
        try:
            # 1. deploy sides first
            self.left.deploy()
            self.right.deploy()
            
            # 2. activate magnets
            self.left.activate_magnets()
            self.right.activate_magnets()
            
            # 3. front cover
            self.front.deploy()
            self.front.activate_magnets()
            
            # 4. body and back protection
            self.body.deploy()
            self.back.deploy()
            
            self.emergency_active = True
            self.last_deployment = time.time()
            
            logger.info("All protection deployed")
            
        except Exception as e:
            logger.error(f"Failed to deploy protection: {e}")
    
    def retract_protection(self):
        """Put everything back - reverse order"""
        if not self.emergency_active:
            return
        
        try:
            # go backwards
            self.back.retract()
            self.body.retract()
            
            self.front.deactivate_magnets()
            self.front.retract()
            
            self.right.deactivate_magnets()
            self.left.deactivate_magnets()
            
            self.right.retract()
            self.left.retract()
            
            self.emergency_active = False
            logger.info("Protection retracted")
            
        except Exception as e:
            logger.error(f"Error retracting protection: {e}")
    
    def test_system(self):
        """Quick test of all components"""
        logger.info("Testing system...")
        
        # test sensors
        emergency, _ = self.sensor_reader.check_emergency()
        logger.info(f"Sensor check: {'OK' if not emergency else 'WARNING'}")
        
        # test components
        components = [self.front, self.left, self.right, self.back, self.body]
        all_ok = True
        
        for comp in components:
            if not comp.deploy():
                all_ok = False
            time.sleep(0.2)  # wait a bit between tests
            if not comp.retract():
                all_ok = False
        
        return all_ok

# quick test
if __name__ == "__main__":
    print("Starting safety system test...")
    
    safety = SafetySystem()
    
    if safety.test_system():
        print("System test passed!")
        safety.start_monitoring()
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nShutting down...")
            safety.stop_monitoring()
    else:
        print("System test failed - check logs")