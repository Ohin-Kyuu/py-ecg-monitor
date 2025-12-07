"""
Threading module for Serial & ECG worker.
"""
import os
import queue
import threading
import time
import serial
import psutil
import numpy as np
from datetime import datetime
from config import Config
from ecg import ECG
from utils import SHARED_STATS

class Serial(threading.Thread):
    __slots__ = ('cfg', 'output', 'stop_event')
    
    def __init__(self, cfg: Config, output: queue.Queue):
        super().__init__(daemon=True)
        self.cfg = cfg
        self.output = output
        self.stop_event = threading.Event()
    
    def run(self):
        try:
            ser = serial.Serial(self.cfg.port, self.cfg.baud_rate, timeout=0.1)
            time.sleep(2)
            ser.reset_input_buffer()
            print(f"[Serial] Listening on {self.cfg.port}...")
        except Exception as e:
            print(f"[Serial] Failed to open {self.cfg.port}: {e}")
            return
        
        batch = []
        while not self.stop_event.is_set():
            val = None
            if ser and ser.in_waiting:
                try:
                    raw = ser.read_until(b"\n")
                    if raw:
                        val = int(raw.decode("utf-8").strip())
                except: pass
            else:
                time.sleep(0.001)

            if val is not None:
                batch.append(val)
                if len(batch) >= self.cfg.batch_size:
                    data = np.array(batch, dtype=np.float64)
                    self.output.put(data)
                    batch = [] # Clear
        if ser: ser.close()
    
    def stop(self):
        self.stop_event.set()


class Worker(threading.Thread):
    __slots__ = ('input', 'output', 'process', 'stop_event')
    
    def __init__(self, cfg: Config, input: queue.Queue, output: queue.Queue):
        super().__init__(daemon=True)
        self.input = input
        self.output = output
        self.process = ECG(cfg)
        self.stop_event = threading.Event()
    
    def run(self):
        while not self.stop_event.is_set():
            try:
                batch = self.input.get(timeout=0.1)
                results = self.process.process(batch)
                self.output.put(results)
            except queue.Empty:
                continue
    
    def stop(self):
        self.stop_event.set()

class Monitor(threading.Thread):
    __slots__ = ('stop_event', 'interval', 'process')
    
    def __init__(self, interval=1.0):
        super().__init__(daemon=True)
        self.stop_event = threading.Event()
        self.interval = interval
        self.process = psutil.Process(os.getpid())
    
    def run(self):
        print(f"[Monitor] Dashboard active (PID: {os.getpid()})")
        
        # Proccess Time
        headers = f"{'Time':<10} | {'CPU %':<8} | {'RAM MB':<8} | {'Proc Time (100pts)':<20}"
        print(headers)
        print("-" * len(headers))
        
        self.process.cpu_percent(interval=None)
        
        while not self.stop_event.is_set():
            try:
                now = datetime.now().strftime("%H:%M:%S")
                cpu = self.process.cpu_percent(interval=None)
                mem = self.process.memory_info().rss / 1024 / 1024
                proc_time_s = SHARED_STATS["proc_time"]
                
                if proc_time_s > 0:
                    proc_str = f"{proc_time_s * 1000:.3f} ms"
                else:
                    proc_str = "Waiting..."

                msg = f"{now:<10} | {cpu:<8.1f} | {mem:<8.1f} | {proc_str:<20}"
                print(msg)
                
                time.sleep(self.interval)
                
            except Exception as e:
                print(f"[Monitor] Error: {e}")
                break
    
    def stop(self):
        self.stop_event.set()