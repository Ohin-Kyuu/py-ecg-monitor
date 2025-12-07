"""
Configuration for ECG.
"""

from dataclasses import dataclass

@dataclass
class Config:
    # Serial
    port: str = "/dev/ttyACM0"
    baud_rate: int = 115200
    batch_size: int = 10  # Set one batch (N samples) for each pipeline
                          # 1 loops can process N samples in same batch
    """ 
    Noted that for the plot frame rate is 30fps, 
    which is 0.33s per frame, if batch size too big, 
    for ex. 100 samples per batch, then for 500Hz fs,
    100/500 = 200ms, you might notice the plt is lagging
    """

    # Signal
    fs: int = 500         # Sampling frequency (Hz)
    
    # Filter
    hp_fc: float = 2.0    # Highpass filter cutoff (Baseline Wander)

    # Window lengths
    ma_len: int = 8       # Moving Average Lowpass filter
    deriv_len: int = 8    # Derivative filter
    mwi_len: int = 40     # Moving window integration
    
    # Peak Detection
    interval: int = 200   # Minimum interval between peaks (ms)
    tau: float = 1.30     # Threshold decay time constant
    min_th: int = 1000     # Minimum Threshold

    # Plot Data buffer
    buf_size: int = 2000