"""Etapa 2 del modo edición: el corte en papel. Decide qué se queda a partir del análisis y escribe:

    python planificar.py [--rehacer] [--pausa 0.5] [--zoom-salto 1.12]

  GUION-MONTAJE.md   la transcripción con lo que se quita tachado y el motivo; es lo que aprueba el usuario
  analisis/guion.json   palabras conservadas y frases quitadas (qc.py comprueba que el video final las respeta)
  montaje.json -> clips   un clip por tramo conservado de la voz

Qué quita: las tomas repetidas que no ganaron (analisis/frases.json -> tomas), las frases que solo son muletillas
("eh", "em"…), las palabras sin voz debajo (alucinaciones de Whisper) y los silencios: dos frases conservadas
separadas por más de --pausa segundos pasan a ser dos clips (un jump cut). En cada jump cut alterna el zoom entre 1 y
--zoom-salto para que el salto no se note. Los límites de cada clip se ajustan con la energía del audio, porque
Whisper suele dar finales de palabra adelantados: se alarga hasta que la voz cae y se añade un margen.
No pisa un montaje ya editado salvo con --rehacer.
"""
import argparse
import json
import os
import re
import sys

import numpy as np

import analizar
import montaje as mt

ROOT = os.path.dirname(os.path.abspath(__file__))
MULETILLAS = {"e", "eh", "ehh", "ehm", "em", "emm", "mm", "mmm", "hm", "ah", "aa", "eeh", "este…", "eh…"}
MARGEN_INI, MARGEN_FIN = 0.06, 0.12      # aire antes del primer sonido y después del último


def limpio(t):
    return re.sub(r"[^\wáéíóúüñ…]", "", t.lower())


voz_real = analizar.voz_real


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--rehacer", action="store_true", help="sustituir los clips aunque ya se hayan editado")
    ap.add_argument("--pausa", type=float, default=0.5, help="pausa máxima que se conserva entre frases (s)")
    ap.add_argument("--zoom-salto", type=float, default=1.12, help="zoom alterno en los jump cuts (1 = sin zoom)")
    a = ap.parse_args()
    m = mt.cargar()
    if m.get("clips") and not a.rehacer:
        sys.exit("montaje.json ya tiene clips. Para empezar de nuevo desde el análisis: python planificar.py --rehacer")
    fr = json.load(open(os.path.join(ROOT, "analisis", "frases.json"), encoding="utf-8"))
    voz = fr["fuente"]
    palabras = mt.palabras(m, voz)
    x = analizar.leer_wav(m["fuentes"][voz]["wav"])
    db, umbral, dur = analizar.energia(x), fr["umbralDb"], len(x) / analizar.SR

    quitar = {}
    for g in fr["tomas"]:
        for i in g["frases"]:
            if i != g["elegida"]:
                quitar[i] = f"toma repetida (se queda la {g['elegida']})"
    conservar = {}                       # frase -> (primera, última) palabra conservada
    for f in fr["frases"]:
        if f["i"] in quitar:
            continue
        if f["palabras"] is None:        # nivel núcleo: la frase entera
            conservar[f["i"]] = None
            continue
        idx = [k for k in range(f["palabras"][0], f["palabras"][1] + 1)
               if not palabras[k].get("sinVoz") and limpio(palabras[k]["t"]) not in MULETILLAS]
        # las muletillas del principio y del final se recortan; las de en medio no se pueden quitar sin un corte
        if not idx:
            todas = range(f["palabras"][0], f["palabras"][1] + 1)
            quitar[f["i"]] = "muletilla" if any(limpio(palabras[k]["t"]) in MULETILLAS for k in todas) else "sin voz (alucinación de Whisper)"
            continue
        conservar[f["i"]] = (idx[0], idx[-1])

    # tramos conservados en segundos de la voz, ajustados a la energía y sin invadir lo que se quita
    tramos = []
    orden = [f for f in fr["frases"] if f["i"] in conservar]
    # la voz real de cada frase (también de las que se quitan: marcan hasta dónde puede llegar el margen del vecino)
    reales = []
    for f in fr["frases"]:
        c = conservar.get(f["i"])
        de, a_ = (palabras[c[0]]["de"], palabras[c[1]]["a"]) if c else (f["de"], f["a"])
        # una frase sin voz debajo (alucinación) no ocupa sitio: no debe recortar el margen de sus vecinas
        sin_voz = f["palabras"] is not None and all(palabras[k].get("sinVoz") for k in range(f["palabras"][0], f["palabras"][1] + 1))
        reales.append(None if sin_voz else voz_real(de, a_, db, umbral))
    for n, f in enumerate(fr["frases"]):
        if f["i"] not in conservar:
            continue
        ini, fin = reales[n]
        antes = next((r for r in reversed(reales[:n]) if r), None)
        despues = next((r for r in reales[n + 1:] if r), None)
        minimo = antes[1] + 0.02 if antes else 0.0
        maximo = despues[0] - 0.03 if despues else dur
        tramos.append([f["i"], max(minimo, ini - MARGEN_INI), min(maximo, fin + MARGEN_FIN), ini, fin])

    # frases seguidas con una pausa natural forman un solo clip; si se quitó algo entre ellas o la pausa es larga, corte
    clips = []
    fin_voz = None
    for i, de, a_, ini_v, fin_v in tramos:
        anterior = clips[-1] if clips else None
        seguidas = anterior and all(k in conservar for k in range(anterior["_frases"][-1] + 1, i))
        # la pausa se mide entre voces, no entre clips con margen: si no, una pausa larga parecería corta
        if anterior and seguidas and ini_v - fin_voz <= a.pausa:
            anterior["a"], anterior["_frases"] = a_, anterior["_frases"] + [i]
        else:
            clips.append({"id": len(clips) + 1, "fuente": voz, "de": round(de, 3), "a": round(a_, 3), "layout": "completo",
                          "zoom": 1.0, "foco": [0.5, 0.4], "transicion": "corte", "_frases": [i]})
        fin_voz = fin_v
    zoom = 1.0
    for c in clips[1:]:
        zoom = a.zoom_salto if zoom == 1.0 else 1.0
        c["zoom"] = zoom
    for c in clips:
        c["a"] = round(c["a"], 3)
        c["frases"] = c.pop("_frases")

    m["clips"] = clips
    m.setdefault("registro", []).append({"op": "planificar", "pausa": a.pausa, "zoomSalto": a.zoom_salto})
    errores = mt.validar(m)
    if errores:
        for e in errores:
            print("ERROR:", e)
        return 1
    mt.guardar(m, "planificar")

    conservadas = [k for f in orden if conservar[f["i"]] for k in range(conservar[f["i"]][0], conservar[f["i"]][1] + 1)
                   if not palabras[k].get("sinVoz") and limpio(palabras[k]["t"]) not in MULETILLAS]
    with open(os.path.join(ROOT, "analisis", "guion.json"), "w", encoding="utf-8") as fh:
        json.dump({"fuente": voz, "conservadas": conservadas, "quitadas": [{"frase": k, "motivo": v} for k, v in sorted(quitar.items())]},
                  fh, ensure_ascii=False, indent=1)

    # el corte en papel, para leer en dos minutos
    mmss = lambda t: f"{int(t // 60)}:{t % 60:04.1f}"
    total = mt.duracion(m)
    lineas = [f"# Guion de montaje · {os.path.basename(ROOT)}", "",
              f"Grabado: {mmss(dur)} · montado: {mmss(total)} · {len(clips)} clips · {len(clips) - 1} cortes · "
              f"{sum('toma' in v for v in quitar.values())} tomas descartadas · {sum('muletilla' in v for v in quitar.values())} muletillas · "
              f"{len(fr['silencios'])} silencios largos recortados", "",
              "| # | Grabación | Texto | Decisión |", "|---|---|---|---|"]
    for f in fr["frases"]:
        txt = f["texto"] or "(sin transcripción)"
        if f["i"] in quitar:
            lineas.append(f"| {f['i']} | {mmss(f['de'])}–{mmss(f['a'])} | ~~{txt}~~ | ✗ {quitar[f['i']]} |")
        else:
            lineas.append(f"| {f['i']} | {mmss(f['de'])}–{mmss(f['a'])} | {txt} | ✔ |")
    dudas = [f"- {mmss(p['de'])} «{p['t']}» (confianza {p['p']:.2f})" for k, p in enumerate(palabras)
             if k in set(conservadas) and p["p"] < 0.6]
    sueltos = [f"- {mmss(s['de'])}–{mmss(s['a'])}" for s in fr.get("sinPalabra", []) if s.get("tipo") == "muletilla probable"]
    if dudas or sueltos:
        lineas += ["", "## Para revisar"]
        if dudas:
            lineas += ["Palabras conservadas con baja confianza (¿se entiende? ¿está bien transcrita?):", *dudas]
        if sueltos:
            lineas += ["Sonidos sin palabra entre frases (muletillas o arranques probables; ya quedan fuera si caen en una pausa):", *sueltos]
    with open(os.path.join(ROOT, "GUION-MONTAJE.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lineas) + "\n")
    print(f"{len(clips)} clips · {mmss(dur)} -> {mmss(total)} · quitadas {len(quitar)} frases · GUION-MONTAJE.md listo para revisar")
    return 0


if __name__ == "__main__":
    sys.exit(main())
