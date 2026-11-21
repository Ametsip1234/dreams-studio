# Banda sonora original del tráiler de Liminal 8 (síntesis, 90 BPM, re menor).
import numpy as np, subprocess, sys
from scipy.signal import butter, sosfilt, fftconvolve

SR = 48000
DUR = 63.1
N = int(SR * DUR)
rng = np.random.default_rng(8)
L = np.zeros(N); R = np.zeros(N)          # bus seco
RL = np.zeros(N); RR = np.zeros(N)        # envío a reverb
BEAT = 60 / 90

def hz(n):  # nota MIDI -> Hz
    return 440 * 2 ** ((n - 69) / 12)

def lp(x, f, o=2): return sosfilt(butter(o, f, 'low', fs=SR, output='sos'), x)
def hp(x, f, o=2): return sosfilt(butter(o, f, 'high', fs=SR, output='sos'), x)
def bp(x, a, b, o=2): return sosfilt(butter(o, [a, b], 'band', fs=SR, output='sos'), x)

def add(sig, t, gain=1.0, pan=0.0, send=0.0):
    i = int(t * SR)
    if i >= N: return
    sig = sig[:N - i]
    gl, gr = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
    L[i:i + len(sig)] += sig * gain * gl * 1.414; R[i:i + len(sig)] += sig * gain * gr * 1.414
    if send:
        RL[i:i + len(sig)] += sig * gain * send * gl * 1.414; RR[i:i + len(sig)] += sig * gain * send * gr * 1.414

def env(n, a, r, sustain=True):
    e = np.ones(n); na = max(1, int(a * SR)); nr = max(1, int(r * SR))
    e[:na] = np.linspace(0, 1, na) ** 2
    e[-nr:] *= np.linspace(1, 0, nr) ** 2
    return e

def tt(d): return np.arange(int(d * SR)) / SR

# ---------- instrumentos ----------
def pad(notes, t0, t1, gain=.06, cut=1400, a=2.0, r=2.5, pan_spread=.5):
    d = t1 - t0 + r; t = tt(d)
    for j, n in enumerate(notes):
        f = hz(n); s = np.zeros_like(t)
        for det in (-0.07, 0.0, 0.065):                 # tres voces desafinadas
            ff = f * 2 ** (det / 12)
            ph = rng.uniform(0, 6.28)
            for k in range(1, 14):                      # sierra limitada en banda
                if ff * k > cut * 3: break
                s += np.sin(2 * np.pi * ff * k * t + ph * k) / k
        s = lp(s, cut, 2)
        s *= 1 + .12 * np.sin(2 * np.pi * .23 * t + j)  # movimiento lento
        s *= env(len(t), a, r)
        add(s, t0, gain / len(notes) ** .5, pan=(j / max(1, len(notes) - 1) - .5) * pan_spread, send=.5)

def bell(n, t0, gain=.12, pan=0., dec=2.8):
    f = hz(n); t = tt(dec * 1.6)
    s = (np.sin(2 * np.pi * f * t) * np.exp(-t / dec)
         + .35 * np.sin(2 * np.pi * f * 2.0 * t) * np.exp(-t / (dec * .45))
         + .12 * np.sin(2 * np.pi * f * 3.01 * t) * np.exp(-t / (dec * .22))
         + .05 * np.sin(2 * np.pi * f * 4.17 * t) * np.exp(-t / (dec * .12)))
    s *= np.minimum(1, t / .004)
    add(s, t0, gain, pan, send=.65)

def kick(t0, gain=.42, f0=95, f1=44, dec=.38):
    t = tt(.9)
    f = f1 + (f0 - f1) * np.exp(-t / .045)
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / dec)
    s = lp(s, 900)
    s *= np.minimum(1, t / .003)
    add(s, t0, gain, 0, send=.08)

def heart(t0, gain=.5):
    kick(t0, gain, 70, 38, .22); kick(t0 + .24, gain * .7, 62, 36, .26)

def hat(t0, gain=.025, pan=.25, dec=.035):
    t = tt(.25); s = hp(rng.standard_normal(len(t)), 7000) * np.exp(-t / dec)
    add(s, t0, gain, pan, send=.15)

def shaker(t0, gain=.02, pan=-.3):
    t = tt(.18); s = bp(rng.standard_normal(len(t)), 3500, 9000) * np.exp(-t / .05) * np.minimum(1, t / .015)
    add(s, t0, gain, pan, send=.1)

def bass(n, t0, d, gain=.16):
    f = hz(n); t = tt(d + .1)
    s = np.sin(2 * np.pi * f * t) + .35 * np.sin(2 * np.pi * 2 * f * t) + .12 * np.sin(2 * np.pi * 3 * f * t)
    s = lp(s, 380) * env(len(t), .008, .08) * np.exp(-t / (d * 1.4))
    add(s, t0, gain, 0, send=.05)

def strings(notes, t0, t1, gain=.035, trem=5.5):
    d = t1 - t0 + 1.5; t = tt(d)
    for j, n in enumerate(notes):
        f = hz(n); s = np.zeros_like(t)
        for det in (-.05, .05):
            ff = f * 2 ** (det / 12)
            for k in range(1, 10): s += np.sin(2 * np.pi * ff * k * t + k) / k
        s = lp(s, 2200) * (1 - .35 * (.5 + .5 * np.sin(2 * np.pi * trem * t)))
        s *= env(len(t), 2.5, 1.5)
        add(s, t0, gain, (j - .5) * .8, send=.7)

def swell(t0, d, gain=.07, lo=300, hi=5000):
    # ruido que sube de brillo y volumen hasta t0+d
    t = tt(d); n = rng.standard_normal(len(t))
    parts = [bp(n, lo * (hi / lo) ** (k / 5), lo * (hi / lo) ** (k / 5) * 2.2) for k in range(6)]
    pos = np.linspace(0, 5, len(t)); s = np.zeros_like(t)
    for k in range(6): s += parts[k] * np.clip(1 - abs(pos - k), 0, 1)
    s *= (t / d) ** 2.2
    tone = np.sin(2 * np.pi * np.cumsum(180 * 2 ** (2 * t / d)) / SR) * .25 * (t / d) ** 3
    add(s + tone, t0, gain, 0, send=.6)

def boom(t0, gain=.55):
    t = tt(4)
    s = np.sin(2 * np.pi * np.cumsum(38 + 30 * np.exp(-t / .2)) / SR) * np.exp(-t / 1.3)
    s += .3 * lp(rng.standard_normal(len(t)), 250) * np.exp(-t / .5)
    s *= np.minimum(1, t / .01)
    add(s, t0, gain, 0, send=.45)

def whoosh_down(t0, d=3.2, gain=.08):
    t = tt(d); f = 900 * 2 ** (-5 * t / d)
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * .3 + lp(rng.standard_normal(len(t)), 1200) * .6
    s *= np.exp(-t / (d * .4)) * np.minimum(1, t / .05)
    add(s, t0, gain, 0, send=.6)

b = lambda k: 10 + k * BEAT          # pulso 0 = 10 s ("THE RULES ARE SIMPLE")
D2, F2, G2, A2, Bb2, C3 = 38, 41, 43, 45, 46, 48

# ---------- A · 0–10 s: el pasillo ----------
pad([50, 53, 57, 62], 0.2, 10.2, gain=.075, a=4.5, cut=1100)          # Re menor
for t0, n in [(2.0, 69), (4.6, 65), (7.2, 64), (8.6, 62)]: bell(n, t0, .09, pan=-.2)
for k in range(4): heart(6.0 + k * 1.333, .30 + k * .04)

# ---------- B · 10–20 s: las reglas ----------
boom(10.0, .2)
pad([46, 50, 53, 58], 10.0, 14.0, gain=.07, a=.8, cut=1500)           # Si b
pad([50, 53, 57, 60], 14.0, 16.0, gain=.07, a=.3, cut=1700)           # "TURN BACK": Re m7
pad([43, 50, 55, 58], 16.0, 18.0, gain=.055, a=.3, cut=1000)          # "IF NOT": Sol m
pad([41, 48, 53, 57, 60], 18.0, 20.2, gain=.07, a=.3, cut=1900)       # "KEEP GOING": Fa
for k in range(15):                                                    # 10–20 s
    t = b(k)
    if t >= 16 and t < 18:                                             # silencio de ritmo en "IF NOT"
        continue
    kick(t, .34 if k % 2 == 0 else .26)
    hat(t + BEAT / 2, .022)
    shaker(t + BEAT / 4, .012); shaker(t + 3 * BEAT / 4, .01)
    root = Bb2 if t < 14 else (D2 if t < 16 else F2)
    bass(root, t, BEAT * .45); bass(root + 12 if k % 4 == 3 else root, t + BEAT / 2, BEAT * .4, .12)
swell(12.6, 1.4, .05); swell(16.8, 1.2, .045)
for t0, n in [(18.0, 72), (18.67, 69), (19.33, 67)]: bell(n, t0, .08, pan=.25, dec=2)

# ---------- C · 20–30 s: agua negra y el maniquí ----------
pad([50, 53, 57], 20.0, 30.0, gain=.06, a=1.2, cut=800)
strings([69, 70], 21.0, 29.6, .028)                                    # La contra Si b: tensión
for k in range(15):
    t = 20 + k * BEAT
    bass(D2, t, BEAT * .5, .13)
    if k % 2 == 0: heart(t, .26)
bell(74, 23.0, .06, .3, 3.5); bell(73, 26.3, .055, -.3, 3.5)          # re / do# : inquietud
swell(28.2, 1.8, .06)

# ---------- D · 30–38 s: montaje ----------
prog = [(D2, [50, 53, 57]), (Bb2, [46, 50, 53]), (G2, [43, 50, 55, 58]), (A2, [45, 49, 52, 57])]
for i, (root, ch) in enumerate(prog):
    t0 = 30 + i * 2 * BEAT * 1.5
    pad(ch, t0, t0 + 2 * BEAT * 1.5, gain=.06, a=.15, r=.8, cut=1600)
for k in range(12):
    t = 30 + k * BEAT
    kick(t, .36); kick(t + BEAT * .75, .16) if k % 2 == 1 else None
    hat(t + BEAT / 2, .03); hat(t + BEAT / 4, .012, -.3); hat(t + 3 * BEAT / 4, .012, .4)
    root = prog[min(3, int((t - 30) / (2 * BEAT * 1.5)))][0]
    for e in range(2): bass(root, t + e * BEAT / 2, BEAT * .38, .14)
swell(34.0, 4.0, .085, 400, 7000)

# ---------- E · 38–42 s: la caída ----------
boom(38.0, .24); whoosh_down(38.05, 3.6, .09)
pad([38, 45, 50], 38.0, 41.5, gain=.05, a=.05, r=2.5, cut=500)

# ---------- F · 43–54 s: el logo y el multijugador ----------
boom(43.0, .26)
pad([50, 57, 62, 65, 69], 43.0, 49.0, gain=.08, a=1.0, cut=1800)     # Re m9 abierto
for t0, n in [(43.3, 74), (44.0, 77), (44.67, 81), (45.33, 79), (46.0, 77), (46.67, 76), (47.33, 74)]:
    bell(n, t0, .075, pan=-.15 + (n - 74) * .04, dec=2.4)
pad([41, 48, 53, 57, 64], 49.0, 51.7, gain=.07, a=.2, cut=1900)       # Fa maj7
pad([46, 50, 53, 57, 62], 51.7, 54.2, gain=.07, a=.2, cut=1700)       # Si b maj7
for k in range(8):
    t = 49 + k * BEAT
    kick(t, .3 if k % 2 == 0 else .22); hat(t + BEAT / 2, .02)
    shaker(t + BEAT / 4, .01)
    bass(F2 if t < 51.7 else Bb2, t, BEAT * .45, .13)
bell(81, 49.0, .06, .3); bell(77, 50.33, .055, -.3); bell(79, 51.67, .055, .2); bell(74, 53.0, .06, -.2)

# ---------- G · 54–60 s: final ----------
pad([38, 50, 57, 62, 66], 54.3, 59.5, gain=.075, a=.6, r=3.0, cut=1500)   # Re mayor: resolución inquieta
bell(74, 54.4, .08, 0, 4); bell(78, 55.7, .06, .2, 4); bell(81, 57.0, .055, -.2, 4.5)

# ---------- H · 60–63 s: "DON'T LOOK BACK" ----------
heart(60.6, .38); heart(61.93, .3)
strings([70, 69], 60.2, 62.4, .022, trem=7)

# ---------- zumbido real de los fluorescentes del juego ----------
try:
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', sys.argv[2], '-f', 'f32le', '-ac', '1', '-ar', str(SR), '-'],
                         capture_output=True, check=True).stdout
    hum = np.frombuffer(raw, np.float32).astype(float)
    hum = np.tile(hum, int(N / len(hum)) + 2)[:N]
    he = np.zeros(N); t = np.arange(N) / SR
    he += np.clip(t / 3, 0, 1) * np.clip((10.5 - t) / .6, 0, 1) * .22            # intro
    he += np.clip((t - 20) / 1, 0, 1) * np.clip((30 - t) / .3, 0, 1) * .12        # maniquí
    he += np.clip((t - 59.8) / .4, 0, 1) * .18                                    # final
    L += hum * he * .9; R += hum * he
except Exception as e:
    print('sin zumbido', e)

# ---------- reverb (sala grande, oscura) ----------
def ir(seed, d=3.6):
    g = np.random.default_rng(seed); t = tt(d)
    x = g.standard_normal(len(t)) * np.exp(-t / .9)
    return lp(x, 4200) * np.minimum(1, t / .02)
wl = fftconvolve(RL, ir(1))[:N] * .22; wr = fftconvolve(RR, ir(2))[:N] * .22
L += wl; R += wr

st = np.stack([L, R], 1)
st = hp(st.T, 28).T
st /= np.percentile(np.abs(st), 99.95) / .75
st = np.tanh(st * 1.15) / np.tanh(1.15)
fade = np.ones(N); nf = int(.8 * SR); fade[-nf:] = np.linspace(1, 0, nf)
st *= fade[:, None]
import wave
pcm = (np.clip(st, -1, 1) * 32767).astype('<i2')
with wave.open(sys.argv[1], 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
print('ok', sys.argv[1])
