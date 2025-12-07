import math
import numpy as np
from pipeline import _pipeline
from config import Config
from utils import _tictoc, _bpm

class ECG:
    __slots__ = ('cfg', 'buffers', 'states', 'params')
    
    def __init__(self, cfg: Config):
        self.cfg = cfg

        # Highpass (Baseline Wander) config
        dt = 1.0 / cfg.fs
        if cfg.hp_fc > 0:
            hp_tau = 1.0 / (2 * math.pi * cfg.hp_fc)
            hp_alpha = hp_tau / (hp_tau + dt)
        else:
            hp_alpha = 1.0 

        # Pack all buffers into a tuple
        self.buffers = (
            np.zeros(cfg.ma_len, dtype=np.float32),     # ma_buf
            np.zeros(cfg.deriv_len, dtype=np.float32),  # d_buf
            np.zeros(cfg.mwi_len, dtype=np.float32),    # mwi_buf
        )
        
        # Pack all states into arrays
        self.states = (
            np.array([0.0, 0.0], dtype=np.float64),               # hp: [y_prev, x_prev]
            np.array([0.0, 0.0], dtype=np.float64),               # ma: [idx, sum]
            np.array([0.0], dtype=np.float64),                    # deriv: [idx]
            np.array([0.0, 0.0], dtype=np.float64),               # mwi: [idx, sum]
            np.array([0.0, 0.0, 2000.0, 0.0], dtype=np.float64),  # peak: [prev_mwi, prev_slope, th, last]
            np.array([0.0], dtype=np.float64),                    # sample_idx
        )
        
        # Threshold Decay
        decay = math.exp(-1.0 / (cfg.fs * cfg.tau))
        
        # Pack constant params
        self.params = (hp_alpha, cfg.fs, cfg.interval, decay, cfg.min_th)

        print("[Processor] Compiling Numba functions...")
        dummy_batch = np.zeros(cfg.batch_size, dtype=np.float64)
        self.process(dummy_batch)
        print("[Processor] JIT Compiled.")
    
    @_bpm
    @_tictoc
    def process(self, batch):
        sig, mwi, peak, th = _pipeline(batch, self.buffers, self.states, self.params)
        return sig, mwi, peak, th