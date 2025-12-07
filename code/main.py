"""
Main entrypoint for ECG.
"""
import sys
import queue
from PySide6.QtWidgets import QApplication
from config import Config
from threads import Serial, Worker, Monitor
from plot import Plot


if __name__ == "__main__":
    cfg = Config()
    
    # Communication Queues
    raw = queue.Queue()  # Serial to Worker
    out = queue.Queue()  # Worker to GUI
    
    # Threads
    serial = Serial(cfg, raw)
    worker = Worker(cfg, raw, out)
    monitor = Monitor(interval=1.0)
    serial.start()
    worker.start()
    monitor.start()
    
    # Plot
    app = QApplication(sys.argv)
    plot = Plot(cfg, out)
    plot.show()
    
    try:
        sys.exit(app.exec())
    finally:
        serial.stop()
        worker.stop()
        serial.join()
        worker.join()