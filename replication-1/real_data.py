"""Bug 2 on real data: OOI RCA North cable, 2021-11-04T02:00:02Z (the repo's example file,
fs=200 Hz), processed exactly like scripts/main_spectrodetect.py (bp_filt 14-30 Hz +
hybrid_ninf_filter_design f-k filter), then spectrogram correlation with the main vs PR #38
band guard. No ground-truth call list exists, so we report label-free statistics per channel:
  baseline = median correlation (most time bins are noise)
  contrast_p95 = max / p95 ; contrast_med = max / median
Usage: python real_data.py <file.h5>   (sha256 of the file is printed and pinned)"""
import sys, json, hashlib
import numpy as np
import das4whales as dw
from common import correlogram, KERNELS, FLIMS

path = sys.argv[1]
h = hashlib.sha256(open(path, "rb").read()).hexdigest()
md = dw.data_handle.get_acquisition_parameters(path, interrogator="optasense")
fs, dx = md["fs"], md["dx"]
sel_m = [20000, 65000, 10]                      # script uses 5 m; 10 m keeps RAM < 4 GB
sel = [int(v // dx) for v in sel_m]
tr, time, dist, t0 = dw.data_handle.load_das_data(path, sel, md)
fk = dw.dsp.hybrid_ninf_filter_design((tr.shape[0], tr.shape[1]), sel, dx, fs,
        cs_min=1350, cp_min=1450, cp_max=3300, cs_max=3450, fmin=14, fmax=30)
tr = dw.dsp.bp_filt(tr, fs, 14, 30)
trf = dw.dsp.fk_filter_sparsefilt(tr, fk, tapering=False)
del tr
# the library normalises each channel by its max before the spectrogram (detect.py)
trf = (trf - trf.mean(1, keepdims=True)) / np.abs(trf).max(1, keepdims=True)
rows = trf[::4]                                  # every 4th channel (40 m), ~560 channels
res = {"file": path.split("/")[-1], "sha256": h, "fs": float(fs), "dx": float(dx),
       "channels_used": int(rows.shape[0]), "kernels": {}}
for kn, k in KERNELS.items():
    st = {}
    for g in ("main", "pr38"):
        c, _ = correlogram(rows, fs, FLIMS, k, g)
        med = np.median(c, 1); p95 = np.percentile(c, 95, 1); mx = c.max(1)
        st[g] = dict(baseline=med, cp95=mx/p95, cmed=mx/med, mx=mx,
                     frac14=float((c > 14).mean()))   # pick_times(threshold=14) in main_spectrodetect.py
    r95 = st["pr38"]["cp95"] / st["main"]["cp95"]
    # channels with a clear detection under the fixed guard (top decile of contrast)
    top = st["pr38"]["cp95"] >= np.percentile(st["pr38"]["cp95"], 90)
    res["kernels"][kn] = {
        "baseline_median_main": float(np.median(st["main"]["baseline"])),
        "baseline_median_pr38": float(np.median(st["pr38"]["baseline"])),
        "peak_median_main": float(np.median(st["main"]["mx"])),
        "peak_median_pr38": float(np.median(st["pr38"]["mx"])),
        "frac_bins_above_14_main": st["main"]["frac14"],
        "frac_bins_above_14_pr38": st["pr38"]["frac14"],
        "contrast_p95_median_main": float(np.median(st["main"]["cp95"])),
        "contrast_p95_median_pr38": float(np.median(st["pr38"]["cp95"])),
        "ratio_p95_median_all": float(np.median(r95)),
        "ratio_p95_median_top10pct": float(np.median(r95[top])),
        "ratio_p95_iqr_all": [float(np.percentile(r95, 25)), float(np.percentile(r95, 75))],
    }
print(json.dumps(res, indent=1))
