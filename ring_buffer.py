"""
Ring Buffer for real-time data streaming.
"""
import numpy as np

class RingBuf:
    __slots__ = ('data', 'ptr', 'size', 'full')
    
    def __init__(self, size, dtype=np.float32):
        self.data = np.zeros(size, dtype=dtype)
        self.ptr = 0
        self.size = size
        self.full = False
    
    def append(self, val):
        self.data[self.ptr] = val
        self.ptr = (self.ptr + 1) % self.size
        if self.ptr == 0:
            self.full = True
    
    def extend(self, vals):
        n = len(vals)
        if n == 0: return
        
        if n >= self.size:
            self.data[:] = vals[-self.size:]
            self.ptr = 0
            self.full = True
            return

        end = self.ptr + n
        
        if end <= self.size:
            self.data[self.ptr : end] = vals
            if end == self.size:
                self.full = True
        else:
            split = self.size - self.ptr
            self.data[self.ptr :] = vals[:split]
            self.data[: end - self.size] = vals[split:]
            self.full = True
            
        self.ptr = (self.ptr + n) % self.size

    def get_view(self):
        if not self.full and self.ptr == 0:
            return np.array([])
        
        if self.full:
            # Concatenate tail and head to restore chronological order
            return np.concatenate((self.data[self.ptr:], self.data[:self.ptr]))
        else:
            # Buffer not full yet, return up to current position
            return self.data[:self.ptr]