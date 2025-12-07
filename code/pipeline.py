import numpy as np
from numba import njit

@njit(cache=True, fastmath=True)
def _highpass(x, state, a):
    """
    y[n] = a * (y[n-1] + x[n] - x[n-1])
    """
    y_prev = state[0]
    x_prev = state[1]
    y = a * (y_prev + x - x_prev)
    state[0] = y
    state[1] = x
    return y

@njit(cache=True, fastmath=True)
def _mvavg(x, buf, state):
    """
    S[n] = S[n-1] + x[n] - x[n-L], y[n] = S[n]/L
    y[n] = y[n-1] + (x[n] - x[n-L]) / L
    """
    idx, s = int(state[0]), state[1]
    L = len(buf)
    s += x - buf[idx] # x[n] - x[n-L]
    y = s / L
    buf[idx] = x
    idx = (idx + 1) % L
    state[0], state[1] = idx, s
    return y

@njit(cache=True, fastmath=True)
def _deriv(x, buf, state, sample_idx):
    """
    d[n] = 2x[n] + x[n-1] + 0 x[n-2] - x[n-3] - 2x[n-4]
    """
    if sample_idx < 5:
        return 0.0
    idx = int(state[0])
    n = len(buf)
    buf[idx] = x
    
    x0 = buf[idx]                  # x[n]
    x1 = buf[(idx - 1 + n) % n]    # x[n-1]
    x3 = buf[(idx - 3 + n) % n]    # x[n-3]
    x4 = buf[(idx - 4 + n) % n]    # x[n-4]
    
    d = (2 * x0 + x1 - x3 - 2 * x4)
    
    state[0] = (idx + 1) % n
    return d

@njit(cache=True, fastmath=True)
def _mwi(x, buf, state):
    """
    S[n] = S[n-1] + x[n] - x[n-L]
    """
    idx, s = int(state[0]), state[1]
    L = len(buf)
    s += x - buf[idx]
    buf[idx] = x
    s = max(0.0, s)
    y = int(s / L)
    idx = (idx + 1) % L
    state[0], state[1] = idx, s
    return y

@njit(cache=True, fastmath=True)
def _peak(mwi, state, sample_idx, fs, interval, decay, min_th):
    prev_mwi = state[0]
    prev_slope = state[1]
    th = int(state[2])
    last = int(state[3])
    
    # Calculate current slope
    slope = mwi - prev_mwi
    
    # Peak Detect
    samples = int(interval * fs / 1000.0)
    peak = 0.0
    
    if (sample_idx - last) > samples:
        if prev_slope > 0 and slope <= 0 and prev_mwi > th:
            peak = 1.0
            last = sample_idx - 1
            th = int(prev_mwi * 0.4)

    # Threshold decay
    th = int(th * decay)
    th = max(th, min_th) # Minimum Threshold
    
    # Update state
    state[0] = mwi
    state[1] = slope
    state[2] = th
    state[3] = last
    return peak

@njit(cache=True, fastmath=True)
def _pipeline(x_array, buffers, states, params):
    n = len(x_array)
    
    # Pre allocate output array
    sig_out = np.empty(n, dtype=np.float64)
    mwi_out = np.empty(n, dtype=np.float64)
    peak_out = np.empty(n, dtype=np.float64)
    th_out = np.empty(n, dtype=np.float64)
    
    # Unzip params
    ma_buf, d_buf, mwi_buf = buffers
    hp_state, ma_state, d_state, mwi_state, pk_state, idx = states
    hp_alpha, fs, interval, decay, min_th = params
    
    cur = int(idx[0])
    
    # Loop Vectorize (if batch size = 10, means do 10 loops)
    for i in range(n):
        raw = x_array[i]
        
        # Filtering
        # 0. Highpass (Baseline wander)
        hp = _highpass(raw, hp_state, hp_alpha)

        # 1. Moving Average Lowpass (60Hz Powerline)
        lp = _mvavg(hp, ma_buf, ma_state)
        
        # 2. Derivative
        d = _deriv(lp, d_buf, d_state, cur)
        
        # 3. Squaring
        sq = d * d
        
        # 4. Moving Window Intergration
        mwi = _mwi(sq, mwi_buf, mwi_state)
        
        # 5. Peak Detection
        peak = _peak(mwi, pk_state, cur, fs, interval, decay, min_th)
        
        # Submit output
        sig_out[i] = lp
        mwi_out[i] = mwi
        peak_out[i] = peak
        th_out[i] = pk_state[2]
        
        cur += 1
        
    # Update Index
    idx[0] = cur
    
    return sig_out, mwi_out, peak_out, th_out