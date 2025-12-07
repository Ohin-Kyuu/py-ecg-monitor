"""
PyQtGraph-based real-time visualization for ECG Monitor.
"""
import queue
import numpy as np
import pyqtgraph as pg
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QMainWindow, QVBoxLayout, QWidget
from PySide6.QtGui import QFont
from config import Config
from ring_buffer import RingBuf

class Plot(QMainWindow):
    def __init__(self, cfg: Config, input: queue.Queue):
        super().__init__()
        self.cfg = cfg
        self.queue = input
        
        self.setWindowTitle("Real-time ECG Monitor")
        self.resize(1000, 700)
        
        # Main Widget
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        
        # Graphics
        self.glw = pg.GraphicsLayoutWidget()
        layout.addWidget(self.glw)
        
        self.x_max = cfg.buf_size / cfg.fs
        
        ### Plot 1: ECG signal with Peak Markers
        self.p1 = self.glw.addPlot(row=0, col=0, title="ECG signal")
        self.p1.showGrid(x=True, y=True, alpha=0.3)
        self.p1.setLabel('bottom', 'Time', units='s')
        
        self.p1.setXRange(0, self.x_max, padding=0)
        self.p1.enableAutoRange(axis='x', enable=False)
        
        self.p1.setYRange(-200, 300, padding=0)
        self.p1.enableAutoRange(axis='y', enable=False)
        
        self.ecg = self.p1.plot(pen=pg.mkPen("#00FFFF", width=1.5), name="ECG")
        
        self.peak = pg.ScatterPlotItem(
            size=10,
            pen=pg.mkPen(None),
            brush=pg.mkBrush(255, 0, 0, 255),  # Red
        )
        self.p1.addItem(self.peak)

        # BPM Text
        self.bpm_text = pg.TextItem(
            text="--", 
            color="#00FFFF", 
            anchor=(1, 1),
            fill=pg.mkBrush(0, 0, 0, 150)
        )
        font = QFont()
        font.setPixelSize(24)
        font.setBold(True)
        self.bpm_text.setFont(font)
        self.bpm_text.setZValue(100)
        self.p1.addItem(self.bpm_text)
        
        #### Plot 2: MWI & Threshold
        self.p2 = self.glw.addPlot(row=1, col=0, title="MWI & Threshold")
        self.p2.showGrid(x=True, y=True, alpha=0.3)
        self.p2.setXLink(self.p1)
        self.p2.setLabel('bottom', 'Time', units='s')
        
        self.p2.setYRange(0, 10000, padding=0)
        self.p2.enableAutoRange(axis='y', enable=False)
        
        self.mwi = self.p2.plot(pen=pg.mkPen("#00FF00", width=1.5), name="MWI")
        self.th = self.p2.plot(
            pen=pg.mkPen("#FFFF00", style=pg.QtCore.Qt.DashLine), name="Th"
        )
        
        # Ring buffers
        self.buf_ecg = RingBuf(cfg.buf_size)
        self.buf_mwi = RingBuf(cfg.buf_size)
        self.buf_th = RingBuf(cfg.buf_size)
        self.buf_peak = RingBuf(cfg.buf_size, dtype=np.float32)
        
        # Timer (30fps)
        self.timer = QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(33)
    
    def update(self):
        processed = 0
        while not self.queue.empty():
            try:
                # (sig_arr, mwi_arr, peak_arr, th_arr, bpm_val)
                data = self.queue.get_nowait()
                if not data: continue
                
                sig, mwi, peak, th, bpm = data
                self.buf_ecg.extend(sig)
                self.buf_mwi.extend(mwi)
                self.buf_peak.extend(peak)
                self.buf_th.extend(th)
                
                # BPM Update
                if bpm > 0: self.bpm_text.setText(f"{bpm} BPM")
                else: self.bpm_text.setText("- -")

                processed += len(sig)
                if processed > 2000: break
                
            except queue.Empty:
                break
                
        if processed > 0:
            y_ecg = self.buf_ecg.get_view()
            y_mwi = self.buf_mwi.get_view()
            y_th = self.buf_th.get_view()
            y_peak = self.buf_peak.get_view()
            
            x_axis = np.arange(len(y_ecg)) / self.cfg.fs
            
            self.ecg.setData(x_axis, y_ecg)
            self.mwi.setData(x_axis, y_mwi)
            self.th.setData(x_axis, y_th)
            
            # Peak Markers
            raw_peak = np.flatnonzero(y_peak)
            true_idx = []            
            win = 40 
            
            for idx in raw_peak:
                start = max(0, idx - win)
                end = idx + 5
                if end > start:
                    local_max = np.argmax(y_ecg[start : end])
                    real_peak = start + local_max
                    true_idx.append(real_peak)
                else:
                    true_idx.append(idx)

            if len(true_idx) > 0:
                true_idx = np.array(true_idx, dtype=int)
                pk_time = x_axis[true_idx]
                pk_val = y_ecg[true_idx]
                
                self.peak.setData(pk_time, pk_val)
            else:
                self.peak.clear()

            view = self.p1.viewRange()
            x_min, x_max = view[0]
            y_min, y_max = view[1]
            x_margin = (x_max - x_min) * 0.02
            y_margin = (y_max - y_min) * 0.05
            self.bpm_text.setPos(x_max - x_margin, y_min + y_margin)