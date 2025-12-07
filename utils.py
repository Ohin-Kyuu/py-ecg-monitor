import time
import functools
import numpy as np

SHARED_STATS = {
    "proc_time": 0.0, 
    "updated": False
}

def _tictoc(func):
    stats = {"count": 0, "elps": 0.0}

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        ecg_self = args[0]
        batch_size = ecg_self.cfg.batch_size
        samples = max(1, int(100 / batch_size)) # 1 sample for 100 loops 

        t_start = time.perf_counter()
        result = func(*args, **kwargs)
        t_end = time.perf_counter()

        stats["elps"] += (t_end - t_start)
        stats["count"] += 1
        
        if stats["count"] >= samples:
            SHARED_STATS["proc_time"] = stats["elps"]
            SHARED_STATS["updated"] = True
            # Reset
            stats["count"] = 0
            stats["elps"] = 0.0
        
        return result
    return wrapper

def _bpm(func):
    state = {
        "dist": 0, # last peak
        "history": [],
        "bpm": 0
    }
    
    @functools.wraps(func)
    def wrapper(self, batch):
        hpf, mwi, peaks, ths = func(self, batch)
        
        fs = self.cfg.fs
        peak_indices = np.flatnonzero(peaks)
        
        batch_len = len(batch)
        cur = 0
        
        if len(peak_indices) == 0:
            state["dist"] += batch_len
        else:
            for idx in peak_indices:
                dist = state["dist"] + (idx - cur) + 1
                state["dist"] = 0 
                cur = idx + 1
                if dist > int(0.2 * fs):
                    instant_bpm = (60 * fs) / dist
                    # Filter outlier values
                    if 40 < instant_bpm < 220:
                        state["history"].append(instant_bpm)
                        if len(state["history"]) > 5: state["history"].pop(0)
                        state["bpm"] = int(sum(state["history"]) / len(state["history"]))
            state["dist"] += (batch_len - cur)
        return hpf, mwi, peaks, ths, state["bpm"]
    return wrapper