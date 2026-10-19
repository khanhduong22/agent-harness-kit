#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate CSS `linear()` easing strings from a damped-spring model.

The skill ships pure CSS: no JS runtimes, no animation libraries (determinism +
the frame-seek video export both require that). `linear()` is how a spring gets
into a stylesheet -- sample the spring's step response, emit the samples as
evenly-spaced control points, and let the browser interpolate between them.

Model: unit step response of a second-order mass-spring-damper, normalised so
x(0) = 0 and x(T) = 1.

  underdamped  (z < 1):  x = 1 - e^(-z*w*t) * (cos(wd*t) + z/sqrt(1-z^2)*sin(wd*t))
  critical     (z = 1):  x = 1 - e^(-w*t) * (1 + w*t)
  overdamped   (z > 1):  two real roots, standard combination

  w  = 2*pi*freq_hz         (undamped natural frequency, rad/s)
  wd = w * sqrt(1 - z^2)    (damped frequency -- sets the overshoot period)

Extrema sit at t = n*pi/wd with magnitude e^(-n*z*pi/sqrt(1-z^2)): z alone fixes
how far each bounce throws, freq*duration fixes how many bounces fit in frame.

  python3 diagram-director/scripts/generate_spring_easing.py --zeta 0.6 --freq 2.0 --duration 560
  python3 diagram-director/scripts/generate_spring_easing.py --presets      # the three shipped tokens
"""

import argparse
import math

PRESETS = {
    #  name             zeta  freq_hz  duration_ms  samples
    "spring-soft":    (1.00,   2.20,        520,       24),
    "spring-snappy":  (0.60,   2.00,        560,       28),
    "spring-bouncy":  (0.35,   2.20,        900,       32),
}


def step_response(t, zeta, omega):
    """Normalised unit-step position of a damped spring at time t (seconds)."""
    if zeta < 1.0:
        wd = omega * math.sqrt(1.0 - zeta * zeta)
        decay = math.exp(-zeta * omega * t)
        return 1.0 - decay * (math.cos(wd * t)
                              + (zeta / math.sqrt(1.0 - zeta * zeta)) * math.sin(wd * t))
    if abs(zeta - 1.0) < 1e-9:
        decay = math.exp(-omega * t)
        return 1.0 - decay * (1.0 + omega * t)
    root = math.sqrt(zeta * zeta - 1.0)
    r1 = -omega * (zeta - root)
    r2 = -omega * (zeta + root)
    return 1.0 - (r1 * math.exp(r2 * t) - r2 * math.exp(r1 * t)) / (r1 - r2)


def fmt(value, places):
    """Compact fixed-point: 0.5000 -> .5, 1.0000 -> 1, -0.0200 -> -.02."""
    text = f"{round(value, places):.{places}f}".rstrip("0").rstrip(".")
    if text in ("", "-", "-0"):
        return "0"
    if text.startswith("0."):
        return text[1:]
    if text.startswith("-0."):
        return "-" + text[2:]
    return text


def samples(zeta, freq_hz, duration_ms, count, places=3):
    """`count` evenly-spaced step-response samples over [0, duration_ms]."""
    omega = 2.0 * math.pi * freq_hz
    total = duration_ms / 1000.0
    values = [step_response(total * i / (count - 1), zeta, omega) for i in range(count)]
    values[0] = 0.0        # linear() must start the property at its from-value
    residual = values[-1] - 1.0
    values[-1] = 1.0       # ...and land exactly on the to-value, no tail snap
    return [round(v, places) for v in values], residual


def describe(name, zeta, freq_hz, duration_ms, count):
    values, residual = samples(zeta, freq_hz, duration_ms, count)
    peaks = sum(1 for i in range(1, len(values) - 1)
                if values[i] > 1.0 and values[i] >= values[i - 1] and values[i] >= values[i + 1])
    over = max(values) - 1.0
    body = ", ".join(fmt(v, 3) for v in values)
    return {
        "name": name, "zeta": zeta, "freq": freq_hz, "duration": duration_ms,
        "samples": count, "css": f"linear({body})", "overshoots": peaks,
        "peak_overshoot_pct": 100.0 * over, "tail_residual_pct": 100.0 * residual,
    }


def emit(info):
    print(f"/* {info['name']}  --  damped spring: zeta={info['zeta']:.2f}, "
          f"f={info['freq']:.2f}Hz, sampled {info['samples']}x over {info['duration']}ms")
    print(f"   overshoots: {info['overshoots']}   peak: +{info['peak_overshoot_pct']:.1f}%   "
          f"tail clamp: {info['tail_residual_pct']:+.2f}%")
    print(f"   diagram-director/scripts/generate_spring_easing.py --zeta {info['zeta']} "
          f"--freq {info['freq']} --duration {info['duration']} --samples {info['samples']} */")
    print(f"--ease-{info['name']}: {info['css']};")
    print()


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--zeta", type=float, default=0.6, help="damping ratio (0<z; 1 = critical)")
    ap.add_argument("--freq", type=float, default=2.0, help="natural frequency in Hz")
    ap.add_argument("--duration", type=float, default=560, help="sampled window, ms")
    ap.add_argument("--samples", type=int, default=28, help="control points (24-32 reads smooth)")
    ap.add_argument("--presets", action="store_true", help="emit the three shipped tokens")
    args = ap.parse_args()
    if args.presets:
        for name, params in PRESETS.items():
            emit(describe(name, *params))
        return 0
    if args.samples < 3 or args.zeta <= 0 or args.freq <= 0 or args.duration <= 0:
        print("error: zeta/freq/duration must be > 0 and samples >= 3")
        return 2
    emit(describe("custom", args.zeta, args.freq, args.duration, args.samples))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
