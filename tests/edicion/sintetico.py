"""Material de prueba con respuestas conocidas para el modo edición de Motion Studio.

    python tests/edicion/sintetico.py <carpeta-del-proyecto>

Escribe en <proyecto>/fuentes/:
- camara/movil.mp4   (testsrc2) vertical 1080×1920, ~30 fps con marcas de tiempo irregulares (VFR, como un móvil), voz sintética
- pantalla/obs.mp4   (testsrc, con contador) 1920×1080 a 30 fps constantes; su audio es la misma voz, más baja, con ruido y empezando antes
y en <proyecto>/esperado.json lo que el pipeline debe encontrar: desfase de la pantalla, frases, tomas repetidas,
muletillas y silencios largos.

La voz se sintetiza con la voz española de Windows (System.Speech); en otros sistemas usa `espeak-ng` si existe.
Es una prueba de desarrollo del repositorio, no parte de la skill instalada.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import wave

import numpy as np

SR = 48000
DESFASE_PANTALLA = 1.37        # OBS empezó a grabar 1,37 s antes que el móvil
# (texto, conservar, motivo, silencio después en s)
GUION = [
    ("Hola, hoy vamos a comparar tres modelos de inteligencia artificial.", True, "", 0.6),
    ("El primer modelo es muy rápido pero", False, "toma repetida", 0.9),
    ("El primer modelo es muy rápido, pero comete errores en los detalles.", True, "", 2.6),
    ("Eh", False, "muletilla", 0.5),
    ("Ahora veamos la pantalla con los resultados.", True, "", 0.5),
    ("El segundo modelo tarda más, aunque el resultado es más limpio.", True, "", 0.7),
    ("El segundo modelo tarda más, aunque el resultado es mucho más limpio y ordenado.", True, "", 0.6),
    ("Al final, el tercero gana por su equilibrio entre velocidad y calidad.", True, "", 1.0),
]
# la frase 5 es una toma repetida de la 4: se conserva la última, más completa
GUION[5] = (GUION[5][0], False, "toma repetida", GUION[5][3])


def decir(texto, ruta):
    if sys.platform == "win32":
        ps = ("Add-Type -AssemblyName System.Speech; $s = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
              "$v = $s.GetInstalledVoices() | ? { $_.VoiceInfo.Culture.Name -like 'es-*' } | select -First 1; "
              "if ($v) { $s.SelectVoice($v.VoiceInfo.Name) }; "
              "$s.SetOutputToWaveFile($env:RUTA_WAV); $s.Speak($env:TEXTO); $s.Dispose()")
        subprocess.run(["powershell", "-NoProfile", "-Command", ps], check=True, env={**os.environ, "RUTA_WAV": ruta, "TEXTO": texto})
    elif shutil.which("espeak-ng"):
        subprocess.run(["espeak-ng", "-v", "es", "-w", ruta, texto], check=True)
    else:
        sys.exit("No hay sintetizador de voz (Windows System.Speech o espeak-ng).")
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", ruta, "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"], capture_output=True, check=True)
    x = np.frombuffer(r.stdout, "<f4")
    # recorta el silencio que añade el sintetizador para que los tiempos esperados sean los de la voz
    voz = np.nonzero(np.abs(x) > 0.01)[0]
    return x[voz[0]: voz[-1] + 1] if len(voz) else x


def escribir_wav(ruta, x):
    with wave.open(ruta, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(x, -1, 1) * 32767).astype("<i2").tobytes())


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    proyecto = os.path.abspath(sys.argv[1])
    os.makedirs(os.path.join(proyecto, "fuentes", "camara"), exist_ok=True)
    os.makedirs(os.path.join(proyecto, "fuentes", "pantalla"), exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        partes, frases, t = [np.zeros(int(0.8 * SR), np.float32)], [], 0.8
        for k, (texto, conservar, motivo, pausa) in enumerate(GUION):
            x = decir(texto, os.path.join(tmp, f"f{k}.wav")) * 0.5
            frases.append({"i": k, "texto": texto, "de": round(t, 3), "a": round(t + len(x) / SR, 3), "conservar": conservar, "motivo": motivo})
            partes += [x, np.zeros(int(pausa * SR), np.float32)]
            t += len(x) / SR + pausa
        voz = np.concatenate(partes)
        dur = len(voz) / SR
        escribir_wav(os.path.join(tmp, "voz.wav"), voz)
        rng = np.random.default_rng(7)
        pant = np.concatenate([np.zeros(int(DESFASE_PANTALLA * SR), np.float32), voz * 0.4]) + rng.normal(0, 0.003, int(DESFASE_PANTALLA * SR) + len(voz)).astype(np.float32)
        escribir_wav(os.path.join(tmp, "pantalla.wav"), pant)

        # móvil: vertical, marcas de tiempo irregulares (hasta 20 ms) como un teléfono que graba en VFR
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", f"testsrc2=size=1080x1920:rate=30:duration={dur:.3f}",
                        "-i", os.path.join(tmp, "voz.wav"),
                        "-vf", "setpts=PTS+0.02*mod(N\\,3)/TB",
                        "-fps_mode", "passthrough", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
                        "-c:a", "aac", "-b:a", "192k", "-shortest", os.path.join(proyecto, "fuentes", "camara", "movil.mp4")], check=True)
        dp = DESFASE_PANTALLA + dur
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", f"testsrc=size=1920x1080:rate=30:duration={dp:.3f}",
                        "-i", os.path.join(tmp, "pantalla.wav"),
                        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k",
                        "-shortest", os.path.join(proyecto, "fuentes", "pantalla", "obs.mp4")], check=True)

    esperado = {"duracionVoz": round(dur, 3), "desfasePantalla": DESFASE_PANTALLA, "frases": frases,
                "silenciosLargos": [[f["a"], round(f["a"] + GUION[f["i"]][3], 3)] for f in frases if GUION[f["i"]][3] >= 1.0]}
    with open(os.path.join(proyecto, "esperado.json"), "w", encoding="utf-8") as f:
        json.dump(esperado, f, ensure_ascii=False, indent=1)
    print(f"Material de prueba en {proyecto}/fuentes · voz {dur:.1f} s · desfase de la pantalla {DESFASE_PANTALLA} s")


if __name__ == "__main__":
    main()
