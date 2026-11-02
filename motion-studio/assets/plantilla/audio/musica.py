"""Audio de Motion Studio: música, efectos y voz -> audio/final.wav a -14 LUFS, con la cuadrícula de pulsos en beats.json.

    python audio/musica.py                      sintetiza música y efectos desde BPM y GOLPES (abajo)
    python audio/musica.py --pista tema.mp3     usa una pista del usuario: MIDE sus pulsos y los escribe en beats.json
                           [--bpm 120]           (tempo aproximado si la medición automática se equivoca)
    python audio/musica.py --voz voz.wav        añade una narración y baja la música mientras se habla (ducking)

Al terminar comprueba con detección de golpes que la cuadrícula de beats.json cae sobre el audio real y lo informa.
Necesita numpy y ffmpeg. Todo es determinista: el ruido sale de un generador con semilla.
PLANTILLA: ajusta BPM, ACORDES y GOLPES al storyboard; index.html debe anclar sus cambios a los mismos pulsos.
"""
import argparse
import json
import os
import re
import subprocess
import wave

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CFG = json.load(open(os.path.join(ROOT, "motion.config.json"), encoding="utf-8"))
SR, DUR = 48000, float(CFG["video"]["duracion"])
N = int(SR * DUR)
SALIDA = os.path.join(ROOT, "audio", "final.wav")

BPM, POR_COMPAS = 90, 4
ACORDES = [[57, 60, 64], [53, 57, 60], [48, 52, 55], [55, 59, 62]]   # notas MIDI por compás, en bucle
GOLPES = {"impacto": [0, 8], "tic": [4, 5, 6, 7]}                    # efecto -> pulsos en los que suena

rng = np.random.default_rng(1234)
hz = lambda m: 440 * 2 ** ((m - 69) / 12)


def env(n, a=0.005, d=1.0):
    t = np.arange(n) / SR
    return np.minimum(1, t / a) * np.exp(-t / d)


def piano(m, dur=2.5):
    n = int(SR * dur); t = np.arange(n) / SR
    s = sum(np.sin(2 * np.pi * hz(m) * k * t) / k ** 1.6 for k in range(1, 7))
    return s * env(n, 0.004, 0.8)


def impacto(dur=2.0, f0=130, f1=32):
    n = int(SR * dur); t = np.arange(n) / SR
    f = f1 + (f0 - f1) * np.exp(-t * 9)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * env(n, 0.002, 0.6) + 0.2 * rng.standard_normal(n) * env(n, 0.001, 0.03)


def tic(f=2200, dur=0.08):
    n = int(SR * dur); t = np.arange(n) / SR
    return np.sin(2 * np.pi * f * t) * env(n, 0.001, 0.015)


EFECTOS = {"impacto": (impacto, 0.8), "tic": (tic, 0.3)}


def poner(mix, sig, t, gain=1.0):
    i = int(round(t * SR))
    if 0 <= i < N:
        sig = sig[: N - i] * gain
        mix[:, i:i + len(sig)] += sig


def leer(ruta):
    """Cualquier formato que lea ffmpeg -> estéreo float a 48 kHz."""
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", ruta, "-f", "f32le", "-ac", "2", "-ar", str(SR), "-"], capture_output=True, check=True)
    return np.frombuffer(r.stdout, dtype="<f4").reshape(-1, 2).T.astype(float)


def flujo(mono, hop):
    """Envolvente de ataques: aumento de energía logarítmica por ventana de `hop` muestras."""
    e = np.array([np.sum(mono[i:i + hop] ** 2) for i in range(0, len(mono) - hop, hop)])
    return np.maximum(0, np.diff(np.log(e + 1e-9), prepend=0))


def medir_pulsos(mono, bpm_aprox=None):
    """Tempo aproximado por autocorrelación de la envolvente; después, periodo y fase finos (0,2 ms y 5 ms) que maximizan
    la energía de ataque sobre toda la pista, para que la rejilla no se desvíe a lo largo del video."""
    H = 0.005; f = flujo(mono, int(SR * H)); g = f - f.mean()
    ac = np.correlate(g, g, "full")[len(g) - 1:]
    lags = np.arange(len(ac)); validos = (lags >= int(60 / 180 / H)) & (lags <= int(60 / 60 / H))
    aprox = 60 / bpm_aprox if bpm_aprox else lags[validos][np.argmax(ac[validos])] * H
    picos = f + 0.5 * (np.roll(f, 1) + np.roll(f, -1))     # tolera ±1 ventana, pero premia el centro
    def puntaje(paso, fase):
        idx = np.round((fase + paso * np.arange(int((DUR - fase) / paso) + 1)) / H).astype(int)
        return picos[idx[idx < len(picos)]].mean()
    paso, fase = max(((p, fz) for p in np.arange(aprox * 0.96, aprox * 1.04, 0.0002) for fz in np.arange(0, p, H)),
                     key=lambda c: puntaje(*c))
    return 60 / paso, [round(fase + k * paso, 4) for k in range(int((DUR - fase) / paso) + 1) if fase + k * paso < DUR]


def escribir(x):
    x = np.tanh(x * 1.2) / np.tanh(1.2)       # limitador suave para que el pico no recorte
    pcm = (np.clip(x, -1, 1) * 32767 * 0.97).astype("<i2").T.copy()
    with wave.open(SALIDA, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())


def lufs():
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", SALIDA, "-af", "ebur128", "-f", "null", "-"], capture_output=True, text=True)
    return float(re.findall(r"I:\s+(-?\d+(?:\.\d+)?)\s+LUFS", r.stderr)[-1])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pista", help="música del usuario; sus pulsos se miden y se escriben en beats.json")
    ap.add_argument("--bpm", type=float, help="con --pista: tempo aproximado si la medición automática se equivoca (p. ej. el doble o la mitad)")
    ap.add_argument("--voz", help="narración que se mezcla encima, con la música bajada mientras suena")
    a = ap.parse_args()
    mix = np.zeros((2, N))

    if a.pista:
        p = leer(a.pista)[:, :N]; mix[:, :p.shape[1]] += p
        bpm, beats = medir_pulsos(mix.sum(0), a.bpm)
        print(f"pista: tempo medido {bpm:.1f} BPM, primer pulso en {beats[0]:.3f} s"
              + ("" if a.bpm else "  (compruébalo escuchando; si es el doble, la mitad u otro, repite con --bpm aproximado)"))
    else:
        bpm, paso = BPM, 60 / BPM
        beats = [round(k * paso, 4) for k in range(int(DUR / paso) + 1) if k * paso < DUR]
        for k, t in enumerate(beats):
            ch = ACORDES[(k // POR_COMPAS) % len(ACORDES)]
            poner(mix, piano(ch[k % len(ch)]), t, 0.2)
            if k % POR_COMPAS == 0:
                poner(mix, piano(ch[0] - 24, 4.0), t, 0.25)
        for nombre, pulsos in GOLPES.items():
            fn, g = EFECTOS[nombre]
            for k in pulsos:
                if k < len(beats):
                    poner(mix, fn(), beats[k], g)

    json.dump({"nota": "Cuadrícula de pulsos generada por audio/musica.py " + ("(medida en la pista)" if a.pista else "(la música se sintetiza sobre ella)"),
               "bpm": round(bpm, 2), "beatsPerBar": POR_COMPAS, "bars": len(beats) // POR_COMPAS, "beats": beats},
              open(os.path.join(ROOT, "beats.json"), "w"), indent=1)
    mix /= max(1e-9, np.abs(mix).max()) / 0.5

    if a.voz:
        v = leer(a.voz)[:, :N]; voz = np.zeros((2, N)); voz[:, :v.shape[1]] = v
        nivel = np.convolve(np.abs(voz.sum(0)), np.ones(int(SR * 0.15)) / (SR * 0.15), "same")
        mix *= 1 - 0.7 * np.clip(nivel / (nivel.max() * 0.25 + 1e-9), 0, 1)     # ducking: -10 dB bajo la voz
        mix += voz / max(1e-9, np.abs(voz).max()) * 0.7

    x = mix.copy()
    for _ in range(8):                          # -14 LUFS medidos con ffmpeg (ebur128)
        escribir(x); l = lufs()
        if abs(l + 14) < 0.3:
            break
        x *= 10 ** ((-14 - l) / 20)
    print(f"audio/final.wav  {l:.1f} LUFS")

    # Verificación: ¿cae cada pulso de beats.json sobre un ataque real del audio?
    f = flujo(mix.sum(0), int(SR * 0.005)); err = []
    for bt in beats:
        i = int(bt / 0.005); w = f[max(0, i - 8): i + 9]
        if len(w) and w.max() > 0.5:
            err.append(abs(int(np.argmax(w)) + max(0, i - 8) - i) * 5)
    if err:
        print(f"cuadrícula: {len(err)} pulsos con ataque, desfase medio {np.mean(err):.1f} ms, máximo {max(err)} ms"
              + ("" if np.mean(err) < 25 else "  AVISO: la cuadrícula no coincide con el audio"))
    else:
        print("AVISO: no se detectaron ataques en los pulsos; revisa BPM o la pista")


if __name__ == "__main__":
    main()
