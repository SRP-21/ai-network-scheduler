import random

class StreamingSimulator:
    def __init__(self):
        self.reset()

    def reset(self):
        self.dumb_buffer = 15.0
        self.smart_buffer = 15.0
        self.dumb_stalls = 0
        self.smart_stalls = 0
        self.dumb_dropped = 0
        self.smart_dropped = 0
        self.dumb_quality = 720
        self.smart_quality = 720

    def tick(self, bandwidth_mbps):
        # DUMB logic (Without AI)
        dumb_noise = random.uniform(-0.5, 0.5)
        dumb_effective = bandwidth_mbps * 0.3
        self.dumb_buffer = self.dumb_buffer - 1.5 + dumb_effective + dumb_noise
        
        # Stall detection
        if self.dumb_buffer < 0.5:
            self.dumb_buffer = max(0.0, self.dumb_buffer) + random.uniform(2.0, 4.0)
            self.dumb_stalls += 1
            self.dumb_dropped += random.randint(8, 15)
            self.dumb_quality = 144
        elif self.dumb_buffer < 2.0:
            self.dumb_quality = 240
        elif self.dumb_buffer < 5.0:
            self.dumb_quality = 480
        elif self.dumb_buffer < 15.0:
            self.dumb_quality = 720
        else:
            self.dumb_quality = 1080
            
        self.dumb_buffer = min(30.0, max(0.0, self.dumb_buffer))

        # SMART logic (With AI Scheduler)
        smart_noise = random.uniform(-0.2, 0.5)
        smart_effective = bandwidth_mbps * 0.8
        self.smart_buffer = self.smart_buffer - 1.5 + smart_effective + smart_noise
        
        # Stall detection
        if self.smart_buffer < 0.5:
            self.smart_buffer = max(0.0, self.smart_buffer) + random.uniform(2.0, 4.0)
            self.smart_stalls += 1
            self.smart_dropped += random.randint(1, 3)
            self.smart_quality = 144
        elif self.smart_buffer <= 3.0:
            self.smart_quality = 240
        elif self.smart_buffer <= 8.0:
            self.smart_quality = 480
        elif self.smart_buffer <= 15.0:
            self.smart_quality = 720
        else:
            self.smart_quality = 1080
            
        self.smart_buffer = min(30.0, max(0.0, self.smart_buffer))

        return {
            "dumb": {
                "buffer": self.dumb_buffer,
                "quality": self.dumb_quality,
                "stalls": self.dumb_stalls,
                "dropped": self.dumb_dropped
            },
            "smart": {
                "buffer": self.smart_buffer,
                "quality": self.smart_quality,
                "stalls": self.smart_stalls,
                "dropped": self.smart_dropped
            }
        }
