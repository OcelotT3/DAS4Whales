"""Replication #1 (Atlas-Grokcelot, 1F916 replication desk): Wilmund's DAS4Whales PR #38.
Bug 1: dsp.bp_filt (b,a) instability. Bug 2: spectrocorr band guard ("nearly doubled" contrast).
Plus issue #39 item 1: hybrid_ninf_filter_design, before/after our follow-up fix.
Each dsp.py version is loaded straight from git so the comparison is exact:
  main = 606452f, pr38 = e34db1f, followup = <REV argument, default HEAD>.
Usage: python replicate.py <path-to-DAS4Whales-clone> [REV]  -> writes results.md, results.json
Seeds are fixed (bug 1: 20261007; bug 2: 1000..1019, fresh vs. our first pass which used 0..9)."""
import sys, json, subprocess, tempfile, importlib.util, warnings, platform
import numpy as np, scipy, scipy.signal as sp
from common import correlogram, KERNELS, FLIMS
from das4whales import detect as d

warnings.simplefilter("ignore")
REPO = sys.argv[1]; REV = sys.argv[2] if len(sys.argv) > 2 else "HEAD"
REVS = {"main": "606452f", "pr38": "e34db1f", "followup": REV}

def load_dsp(rev):
    src = subprocess.check_output(["git", "-C", REPO, "show", f"{rev}:src/das4whales/dsp.py"])
    f = tempfile.NamedTemporaryFile("wb", suffix=".py", delete=False); f.write(src); f.close()
    spec = importlib.util.spec_from_file_location(f"dsp_{rev}", f.name)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m

dsp = {k: load_dsp(v) for k, v in REVS.items()}
sha = {k: subprocess.check_output(["git", "-C", REPO, "rev-parse", v]).decode().strip() for k, v in REVS.items()}
out = {"env": {"python": platform.python_version(), "numpy": np.__version__, "scipy": scipy.__version__},
       "revs": sha}
md = [f"# Replication #1 results\n\nEnv: Python {platform.python_version()}, numpy {np.__version__}, "
      f"scipy {scipy.__version__}. Revs: " + ", ".join(f"{k}={v[:7]}" for k, v in sha.items()) + "\n"]

# ---------------- Bug 1: bp_filt ----------------
md.append("## Bug 1: `dsp.bp_filt` (order-8 Butterworth bandpass)\n")
md.append("| band (Hz) | fs (Hz) | max pole radius, (b,a) | max abs(out), main | max abs(out), PR #38 | 20 Hz/centre tone gain, PR #38 |")
md.append("|---|---|---|---|---|---|")
b1 = []
for lo, hi in [(14, 30), (15, 25), (10, 30), (32, 48)]:
    for fs in [200, 500, 1000, 2000]:
        rng = np.random.default_rng(20261007)
        x = rng.standard_normal((2, 8*fs))
        b, a = sp.butter(8, [lo/(fs/2), hi/(fs/2)], "bp")
        r = float(np.abs(np.roots(a)).max())
        y0 = dsp["main"].bp_filt(x, fs, lo, hi); y1 = dsp["pr38"].bp_filt(x, fs, lo, hi)
        m0 = float(np.nanmax(np.abs(y0))) if np.isfinite(y0).any() else float("nan")
        if not np.isfinite(y0).all(): m0 = float("nan") if not np.isfinite(y0).any() else m0
        t = np.arange(8*fs)/fs; tone = np.sin(2*np.pi*0.5*(lo+hi)*t)[None]
        g = float(np.abs(dsp["pr38"].bp_filt(tone, fs, lo, hi)[:, 2*fs:-2*fs]).max())
        nan0 = not np.isfinite(y0).all()
        b1.append(dict(band=[lo, hi], fs=fs, pole=r, main=m0, main_nonfinite=nan0,
                       pr38=float(np.abs(y1).max()), tone_gain_pr38=g))
        mtxt = "NaN/inf" if nan0 else f"{m0:.3g}"
        flag = " **unstable**" if r >= 1 else ""
        md.append(f"| {lo}-{hi} | {fs} | {r:.4f}{flag} | {mtxt} | {np.abs(y1).max():.3g} | {g:.3f} |")
out["bug1"] = b1
md.append("\nInput: unit white noise, 2x8 s. Stable filter output stays below about 5. Larger values mean the output blew up.\n")

# ---------------- Bug 2: spectrocorr band guard, synthetic ----------------
def noise(kind, n, fs, rng):
    w = rng.standard_normal(n)
    if kind == "white": return w
    if kind == "pink":
        f = np.fft.rfftfreq(n, 1/fs); f[0] = f[1]
        x = np.fft.irfft(np.fft.rfft(w)/np.sqrt(f), n); return x/x.std()
    if kind == "white->bp14-30":   # documented pipeline: bp_filt(14,30) before spectrocorr
        x = sp.sosfiltfilt(sp.butter(8, [14/100, 30/100], "bp", output="sos"), w); return x/x.std()
_SOS = sp.butter(8, [14/100, 30/100], "bp", output="sos")
def inband_norm(x, rng):
    ref = sp.sosfiltfilt(_SOS, rng.standard_normal(len(x))).std()
    return x*ref/sp.sosfiltfilt(_SOS, x).std()

fs, T, tc = 200, 60.0, 30.0
md.append("## Bug 2: spectrocorr band guard, synthetic (20 fresh seeds)\n")
md.append("Metric: peak correlation within ±0.6 s of the injected call, divided by the noise-floor p95 (|t-tc|>3 s). Median over seeds. "
          "Call amplitude is relative to the in-band (14-30 Hz) noise RMS. The baseline is the mean correlation off the call.\n")
md.append("| kernel | noise | call amp | contrast main | contrast PR #38 | ratio | baseline main | baseline PR #38 |")
md.append("|---|---|---|---|---|---|---|---|")
b2 = []
for kn, k in KERNELS.items():
    call = d.gen_hyperbolic_chirp(k["f1"], k["f0"], k["dur"], fs)*np.hanning(int(k["dur"]*fs))
    for nk in ["white", "pink", "white->bp14-30"]:
        for amp in [0.5, 1.0, 2.0, 4.0]:
            R = {"main": [], "pr38": []}; B = {"main": [], "pr38": []}
            for seed in range(1000, 1020):
                rng = np.random.default_rng(seed)
                x = inband_norm(noise(nk, int(T*fs), fs, rng), rng)
                i0 = int((tc - k["dur"]/2)*fs); x[i0:i0+len(call)] += amp*call
                x = (x - x.mean())/np.abs(x).max()      # library's per-channel normalisation
                for g in R:
                    c, tt = correlogram(x, fs, FLIMS, k, g); c = c[0]
                    near = np.abs(tt-tc) <= 0.6; far = np.abs(tt-tc) > 3
                    R[g].append(c[near].max()/np.percentile(c[far], 95)); B[g].append(c[far].mean())
            mo, mn = float(np.median(R["main"])), float(np.median(R["pr38"]))
            row = dict(kernel=kn, noise=nk, amp=amp, main=mo, pr38=mn, ratio=mn/mo,
                       base_main=float(np.mean(B["main"])), base_pr38=float(np.mean(B["pr38"])))
            b2.append(row)
            md.append(f"| {kn} | {nk} | {amp} | {mo:.2f} | {mn:.2f} | **x{mn/mo:.2f}** | {row['base_main']:.3f} | {row['base_pr38']:.3f} |")
out["bug2_synthetic"] = b2

# ---------------- issue #39 item 1: hybrid_ninf_filter_design ----------------
md.append("\n## Issue #39 item 1: `hybrid_ninf_filter_design` (f-k mask, 128 ch x 4 s, dx=2 m)\n")
md.append("Envelope = max over k of the mask. Core passband = central half of the band. "
          "Max abs diff = followup minus main over the whole mask.\n")
md.append("| band | fs | main: core min/max | main: mask max | followup: core min/max | followup: mask max | max abs diff vs main |")
md.append("|---|---|---|---|---|---|---|")
b3 = []
for lo, hi in [(14., 30.), (15., 25.), (10., 30.)]:
    for fs in [200, 500, 1000, 2000]:
        nns = 4*fs; freq = np.fft.fftshift(np.fft.fftfreq(nns, 1/fs))
        q = 0.25*(hi-lo); core = (freq >= lo+q) & (freq <= hi-q)
        M = {}
        for v in ("main", "followup"):
            M[v] = dsp[v].hybrid_ninf_filter_design((128, nns), [0, 128, 1], 2.0, fs, fmin=lo, fmax=hi).todense()
        e0, e1 = M["main"].max(0), M["followup"].max(0)
        diff = float(np.abs(M["followup"]-M["main"]).max())
        b3.append(dict(band=[lo, hi], fs=fs, main_core=[float(e0[core].min()), float(e0[core].max())],
                       main_max=float(M["main"].max()), fix_core=[float(e1[core].min()), float(e1[core].max())],
                       fix_max=float(M["followup"].max()), maxabsdiff=diff))
        md.append(f"| {lo:g}-{hi:g} | {fs} | {e0[core].min():.3g}/{e0[core].max():.3g} | {M['main'].max():.3g} | "
                  f"{e1[core].min():.3g}/{e1[core].max():.3g} | {M['followup'].max():.3g} | {diff:.2g} |")
out["ninf"] = b3
open("results.json", "w").write(json.dumps(out, indent=1, default=float) + "\n")
open("results.md", "w").write("\n".join(md) + "\n")
print("\n".join(md))
