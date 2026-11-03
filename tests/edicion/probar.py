"""Prueba de principio a fin del modo edición con material sintético de respuestas conocidas, más la regresión del
modo animación. Es una prueba de desarrollo del repositorio.

    python tests/edicion/probar.py [--carpeta DIR] [--sin-animacion]

Edición: crea un proyecto con `nuevo.py --edicion`, genera el material (sintetico.py), y comprueba que
  - analizar.py mide el desfase de la pantalla con error ≤ 1 fotograma y agrupa las tomas repetidas esperadas;
  - planificar.py conserva la voz completa de cada frase esperada y quita las tomas descartadas y la muletilla;
  - editar.py --final + qc.py --retranscribir --determinismo pasan;
  - qc.py falla cuando se provoca un corte dentro de una palabra y cuando se pierde una palabra del guion;
  - el detector de clics encuentra un salto provocado en una señal.
Animación: auditar.mjs, --determinismo, --final y verificar.py sobre la plantilla, como antes del modo edición.
Código 1 si algo falla.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile

import numpy as np

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SKILL = os.path.join(REPO, "motion-studio")
resultados = []


def correr(cmd, cwd, debe=0):
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if (debe is not None) and r.returncode != debe:
        print(r.stdout[-2000:], r.stderr[-2000:])
    return r


def comprobar(nombre, cond, detalle=""):
    resultados.append((nombre, bool(cond)))
    print(f"  {'OK   ' if cond else 'FALLA'} {nombre}" + (f" · {detalle}" if detalle else ""), flush=True)


def edicion(base):
    p = os.path.join(base, "edicion")
    py = sys.executable
    correr([py, os.path.join(SKILL, "scripts", "nuevo.py"), p, "--edicion", "--nombre", "prueba"], base)
    correr([py, os.path.join(REPO, "tests", "edicion", "sintetico.py"), p], base)
    esp = json.load(open(os.path.join(p, "esperado.json"), encoding="utf-8"))

    r = correr([py, "analizar.py"], p)
    comprobar("analizar.py termina", r.returncode == 0)
    m = json.load(open(os.path.join(p, "montaje.json"), encoding="utf-8"))
    fps = m["salida"]["fps"]
    d = m["fuentes"].get("pant1", {}).get("desfase")
    comprobar("desfase de la pantalla ≤ 1 fotograma", d is not None and abs(d - esp["desfasePantalla"]) <= 1 / fps, f"{d} frente a {esp['desfasePantalla']}")
    fr = json.load(open(os.path.join(p, "analisis", "frases.json"), encoding="utf-8"))
    nivel = fr["nivel"]
    if nivel == "completo":
        grupos = sorted(sorted(g["frases"]) for g in fr["tomas"])
        comprobar("tomas repetidas agrupadas como se espera", len(grupos) == 2 and all(len(g) == 2 for g in grupos), str(grupos))

    r = correr([py, "planificar.py"], p)
    comprobar("planificar.py termina", r.returncode == 0)
    m = json.load(open(os.path.join(p, "montaje.json"), encoding="utf-8"))
    dentro = lambda de, a: any(c["de"] <= de + 0.02 and a - 0.02 <= c["a"] for c in m["clips"])
    medio = lambda f: any(c["de"] < (f["de"] + f["a"]) / 2 < c["a"] for c in m["clips"])
    for f in esp["frases"]:
        if f["conservar"]:
            comprobar(f"frase {f['i']} entera en el montaje", dentro(f["de"], f["a"]), f"{f['de']}–{f['a']} s")
        elif nivel == "completo":
            comprobar(f"frase {f['i']} quitada ({f['motivo']})", not medio(f))

    r = correr([py, "editar.py", "--final"], p)
    comprobar("editar.py --final termina", r.returncode == 0, r.stdout.strip().splitlines()[-1] if r.stdout.strip() else "")
    r = correr([py, "qc.py", "--retranscribir", "--determinismo"], p, debe=None)
    comprobar("qc.py pasa en el montaje planificado", r.returncode == 0, "; ".join(l.strip() for l in r.stdout.splitlines() if "FALLA" in l))

    # fallos provocados: el control de calidad debe detectarlos
    pal = json.load(open(os.path.join(p, "analisis", "palabras.json"), encoding="utf-8"))[m["voz"]]["palabras"]
    g = json.load(open(os.path.join(p, "analisis", "guion.json"), encoding="utf-8"))
    k = g["conservadas"][len(g["conservadas"]) // 2]
    w = pal[k]
    pos = {c["id"]: (i, f) for c, i, f in [(c, *_pos(m, c)) for c in m["clips"]]}
    clip = next(c for c in m["clips"] if c["de"] <= w["de"] and w["a"] <= c["a"])
    t_salida = pos[clip["id"]][0] + (w["de"] + w["a"]) / 2 - clip["de"]
    correr([py, "montaje.py", "quitar", "--desde", f"{t_salida:.3f}", "--hasta", f"{t_salida + 0.4:.3f}", "--exacto"], p)
    r = correr([py, "qc.py"], p, debe=None)
    comprobar("qc.py detecta un corte dentro de una palabra", r.returncode == 1 and "dentro de palabras" in r.stdout)
    correr([py, "montaje.py", "deshacer"], p)
    correr([py, "montaje.py", "cortar", "--en", f"{t_salida:.3f}", "--exacto"], p)
    r = correr([py, "qc.py"], p, debe=None)
    comprobar("un cambio de plano sin corte de audio no cuenta como corte", "dentro de palabras" not in r.stdout and "perdidas" not in r.stdout)
    correr([py, "montaje.py", "deshacer"], p)
    correr([py, "montaje.py", "quitar", "--palabras", f"{k}-{k}"], p)
    r = correr([py, "qc.py"], p, debe=None)
    comprobar("qc.py detecta una palabra del guion perdida", r.returncode == 1 and "perdidas" in r.stdout)
    correr([py, "montaje.py", "deshacer"], p, debe=None)

    sys.path.insert(0, p)
    import qc
    y = np.sin(np.linspace(0, 2000, 48000)).astype(np.float32) * 0.2
    y[24000:] += 0.3                 # escalón brusco a mitad: un clic
    comprobar("el detector de clics encuentra un salto provocado", qc.clics(y, [0.5]) == [0.5] and qc.clics(y, [0.25]) == [])


def _pos(m, c):
    t = 0
    for x in m["clips"]:
        n = round((x["a"] - x["de"]) * m["salida"]["fps"])
        if x is c:
            return t / m["salida"]["fps"], (t + n) / m["salida"]["fps"]
        t += n


def animacion(base):
    p = os.path.join(base, "animacion")
    correr([sys.executable, os.path.join(SKILL, "scripts", "nuevo.py"), p, "--sin-preparar", "--duracion", "3", "--fps", "24"], base)
    comprobar("animación: auditar.mjs", correr(["node", "auditar.mjs"], p).returncode == 0)
    comprobar("animación: --determinismo", correr(["node", "render.mjs", "--determinismo"], p).returncode == 0)
    comprobar("animación: --final", correr(["node", "render.mjs", "--final"], p).returncode == 0)
    comprobar("animación: verificar.py", correr([sys.executable, "verificar.py"], p).returncode == 0)


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--carpeta", help="dónde crear los proyectos (por defecto, una carpeta temporal que se borra)")
    ap.add_argument("--sin-animacion", action="store_true")
    a = ap.parse_args()
    base = a.carpeta or tempfile.mkdtemp(prefix="motion-pruebas-")
    os.makedirs(base, exist_ok=True)
    try:
        print("Modo edición"); edicion(base)
        if not a.sin_animacion:
            print("Modo animación (regresión)"); animacion(base)
    finally:
        if not a.carpeta:
            shutil.rmtree(base, ignore_errors=True)
    fallos = [n for n, ok in resultados if not ok]
    print(f"\n{len(resultados) - len(fallos)}/{len(resultados)} comprobaciones correctas" + (f" · fallan: {', '.join(fallos)}" if fallos else ""))
    return 1 if fallos else 0


if __name__ == "__main__":
    sys.exit(main())
