# Replication #1 results

Env: Python 3.12.15, numpy 2.5.3, scipy 1.18.1. Revs: main=606452f, pr38=e34db1f, followup=a3b78af

## Bug 1: `dsp.bp_filt` (order-8 Butterworth bandpass)

| band (Hz) | fs (Hz) | max pole radius, (b,a) | max abs(out), main | max abs(out), PR #38 | 20 Hz/centre tone gain, PR #38 |
|---|---|---|---|---|---|
| 14-30 | 200 | 0.9678 | 1.62 | 1.62 | 1.000 |
| 14-30 | 500 | 0.9921 | 1.09 | 0.875 | 1.000 |
| 14-30 | 1000 | 1.1508 **unstable** | NaN/inf | 0.662 | 1.000 |
| 14-30 | 2000 | 1.1995 **unstable** | NaN/inf | 0.451 | 1.000 |
| 15-25 | 200 | 0.9766 | 1.17 | 1.17 | 0.951 |
| 15-25 | 500 | 1.0398 **unstable** | 3.55e+59 | 0.652 | 0.998 |
| 15-25 | 1000 | 1.1722 **unstable** | NaN/inf | 0.524 | 0.998 |
| 15-25 | 2000 | 1.2022 **unstable** | NaN/inf | 0.332 | 1.000 |
| 10-30 | 200 | 0.9685 | 1.68 | 1.68 | 0.951 |
| 10-30 | 500 | 1.0114 **unstable** | 1.02 | 1.08 | 0.998 |
| 10-30 | 1000 | 1.1436 **unstable** | NaN/inf | 0.721 | 0.998 |
| 10-30 | 2000 | 1.1793 **unstable** | NaN/inf | 0.663 | 1.000 |
| 32-48 | 200 | 0.9577 | 1.44 | 1.44 | 0.951 |
| 32-48 | 500 | 0.9840 | 1 | 1 | 0.998 |
| 32-48 | 1000 | 1.0467 **unstable** | 2.17e+155 | 0.698 | 0.998 |
| 32-48 | 2000 | 1.1226 **unstable** | NaN/inf | 0.437 | 0.998 |

Input: unit white noise, 2x8 s. Stable filter output stays below about 5. Larger values mean the output blew up.

## Bug 2: spectrocorr band guard, synthetic (20 fresh seeds)

Metric: peak correlation within ±0.6 s of the injected call, divided by the noise-floor p95 (|t-tc|>3 s). Median over seeds. Call amplitude is relative to the in-band (14-30 Hz) noise RMS. The baseline is the mean correlation off the call.

| kernel | noise | call amp | contrast main | contrast PR #38 | ratio | baseline main | baseline PR #38 |
|---|---|---|---|---|---|---|---|
| HF | white | 0.5 | 1.05 | 1.10 | **x1.04** | 0.917 | 0.199 |
| HF | white | 1.0 | 1.89 | 2.87 | **x1.52** | 0.916 | 0.198 |
| HF | white | 2.0 | 4.25 | 7.67 | **x1.81** | 0.915 | 0.198 |
| HF | white | 4.0 | 9.19 | 17.32 | **x1.89** | 0.913 | 0.198 |
| HF | pink | 0.5 | 1.06 | 1.23 | **x1.16** | 0.999 | 0.143 |
| HF | pink | 1.0 | 1.88 | 3.23 | **x1.72** | 0.998 | 0.143 |
| HF | pink | 2.0 | 4.17 | 8.83 | **x2.12** | 0.996 | 0.143 |
| HF | pink | 4.0 | 8.97 | 20.46 | **x2.28** | 0.995 | 0.143 |
| HF | white->bp14-30 | 0.5 | 1.05 | 1.08 | **x1.03** | 1.100 | 3.964 |
| HF | white->bp14-30 | 1.0 | 1.79 | 1.84 | **x1.02** | 1.099 | 3.962 |
| HF | white->bp14-30 | 2.0 | 3.95 | 4.16 | **x1.05** | 1.097 | 3.958 |
| HF | white->bp14-30 | 4.0 | 8.54 | 9.14 | **x1.07** | 1.096 | 3.956 |
| LF | white | 0.5 | 1.10 | 1.15 | **x1.05** | 0.439 | 0.196 |
| LF | white | 1.0 | 2.90 | 3.64 | **x1.25** | 0.439 | 0.196 |
| LF | white | 2.0 | 6.67 | 8.81 | **x1.32** | 0.438 | 0.196 |
| LF | white | 4.0 | 14.35 | 19.70 | **x1.37** | 0.438 | 0.196 |
| LF | pink | 0.5 | 0.99 | 1.06 | **x1.06** | 0.473 | 0.095 |
| LF | pink | 1.0 | 2.38 | 3.69 | **x1.55** | 0.473 | 0.095 |
| LF | pink | 2.0 | 5.75 | 9.94 | **x1.73** | 0.472 | 0.095 |
| LF | pink | 4.0 | 12.32 | 23.20 | **x1.88** | 0.472 | 0.095 |
| LF | white->bp14-30 | 0.5 | 1.14 | 1.14 | **x1.00** | 1.141 | 1.736 |
| LF | white->bp14-30 | 1.0 | 2.37 | 2.38 | **x1.00** | 1.140 | 1.734 |
| LF | white->bp14-30 | 2.0 | 5.20 | 5.20 | **x1.00** | 1.138 | 1.731 |
| LF | white->bp14-30 | 4.0 | 10.94 | 10.94 | **x1.00** | 1.136 | 1.726 |

## Issue #39 item 1: `hybrid_ninf_filter_design` (f-k mask, 128 ch x 4 s, dx=2 m)

Envelope = max over k of the mask. Core passband = central half of the band. Max abs diff = followup minus main over the whole mask.

| band | fs | main: core min/max | main: mask max | followup: core min/max | followup: mask max | max abs diff vs main |
|---|---|---|---|---|---|---|
| 14-30 | 200 | 1/1 | 1 | 1/1 | 1 | 1.1e-07 |
| 14-30 | 500 | 0.87/1.12 | 22 | 1/1 | 1 | 22 |
| 14-30 | 1000 | 1.09e-08/2.14e-05 | 0.00139 | 1/1 | 1 | 1 |
| 14-30 | 2000 | 5.75e-18/1.02e-13 | 3.34e-07 | 1/1 | 1 | 1 |
| 15-25 | 200 | 1/1 | 1 | 1/1 | 1 | 1.2e-05 |
| 15-25 | 500 | 0.0456/3.31 | 3.31 | 1/1 | 1 | 2.3 |
| 15-25 | 1000 | 1.62e-11/1.44e-09 | 3.67e-07 | 1/1 | 1 | 1 |
| 15-25 | 2000 | 9.28e-22/1.09e-19 | 7.72e-13 | 1/1 | 1 | 1 |
| 10-30 | 200 | 0.999/1 | 1 | 0.999/1 | 1 | 2.6e-07 |
| 10-30 | 500 | 0.978/1.07 | 1.3 | 0.999/1 | 1 | 0.45 |
| 10-30 | 1000 | 2.45e-07/0.00969 | 0.12 | 0.999/1 | 1 | 1 |
| 10-30 | 2000 | 1.17e-17/8.58e-12 | 0.000629 | 0.999/1 | 1 | 1 |
