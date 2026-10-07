"""Shared helpers for replication #1 (Atlas-Grokcelot, 1F916 replication desk).
Spectrogram correlation with a switch between the band guard on DAS4Whales main
(606452f) and the one in Wilmund's PR #38 (e34db1f). All signal-processing helpers
are the library's own (das4whales.detect)."""
import io, contextlib
import numpy as np
from das4whales import detect as d

def guard_band(flims, k, guard):
    fmin, fmax = flims; f0, f1, bw = k["f0"], k["f1"], k["bdwidth"]
    if guard == "main":            # detect.py @ 606452f
        if fmax - f1 < 2*bw: fmax = f1 + 3*bw
        if f0 - fmin < 2*bw: fmin = f0 - 3*bw
    else:                          # PR #38 @ e34db1f
        hi, lo = max(f0, f1), min(f0, f1)
        if fmax - hi < 2*bw: fmax = hi + 3*bw
        if lo - fmin < 2*bw: fmin = lo - 3*bw
    return fmin, fmax

def correlogram(data, fs, flims, k, guard, win=0.8, ovl=0.95):
    """= detect.compute_cross_correlogram_spectrocorr with selectable guard (2-D data)."""
    data = np.atleast_2d(data)
    nperseg = int(win*fs); nhop = int(np.floor(nperseg*(1-ovl)))
    fmin, fmax = guard_band(flims, k, guard)
    with contextlib.redirect_stdout(io.StringIO()):
        S, ff, tt = d.get_sliced_nspectrogram(data[0], fs, fmin, fmax, nperseg, nhop)
        _, _, K = d.buildkernel(k["f0"], k["f1"], k["bdwidth"], k["dur"], ff, tt, fs, fmin, fmax)
        out = np.empty((data.shape[0], len(tt)))
        for i in range(data.shape[0]):
            S, _, _ = d.get_sliced_nspectrogram(data[i], fs, fmin, fmax, nperseg, nhop)
            out[i] = d.xcorr2d(S, K)
    return out, tt

KERNELS = {"HF": {"f0": 27., "f1": 17., "dur": 0.8, "bdwidth": 4.},   # scripts/main_spectrodetect.py
           "LF": {"f0": 20., "f1": 14., "dur": 1.2, "bdwidth": 4.}}
FLIMS = (14., 30.)
