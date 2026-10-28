"""Medición de lectura (7.º criterio de revisión), a partir de review/lectura_raw.json.

Un texto es legible en un fotograma si está completo (entrada terminada), opaco, nítido, sin taparse,
dentro del cuadro, casi quieto (< 300 px/s, zoom < 35 %/s) y con letra de al menos 15 px.
Leerlo pide 0,4 s para encontrarlo + 1 s por cada 16 letras.

Jerarquía: N1 = mensajes (la línea de la historia), N2 = pruebas clave; el resto es ambiente y no se exige.
Pasa si (a) en alguna aparición está legible el tiempo que pide y (b) un lector que lee un texto
N1/N2 a la vez, en orden de aparición, alcanza a terminarlo.

  python lectura.py  -> review/lectura.txt
"""
import json
import os
import re
from collections import defaultdict

import numpy as np

ROOT = os.path.dirname(os.path.abspath(__file__))
RAW = json.load(open(os.path.join(ROOT, "review", "lectura_raw.json"), encoding="utf-8"))
HOLDS = json.load(open(os.path.join(ROOT, "holds.json"), encoding="utf-8"))["holds"]
BEATS = json.load(open(os.path.join(ROOT, "beats.json"), encoding="utf-8"))
CUES = json.load(open(os.path.join(ROOT, "cues.json"), encoding="utf-8"))
FPS, DUR = RAW["fps"], RAW["dur"]
DT = 1 / FPS

N1 = {"Una consulta.", "Ocho preguntas.", "Cada cotización interrumpe la atención.",
      "Asistente comercial por WhatsApp", "para ferreterías.", "Conversar", "Verificar", "Calcular", "Revisar",
      "Pregunta antes", "de asumir.", "Faltan 3: sede, existencias y precio.",
      "Lo que no se sabe", "no se muestra como agotado.",
      "La IA conversa.", "Entiende «mejor que sean 12».", "El sistema calcula.", "12 × $32.500 = $390.000",
      "No es reserva.", "No es factura.", "Falta una persona.", "Una persona responsable al final.",
      "Tu equipo atiende el mostrador.", "XEON prepara la cotización.",
      "Del chat a la cotización aprobada.", "Agenda una demostración"}
N2 = {"necesito cemento y una pala", "Chats sin responder",
      "Te ayudo. ¿Qué cemento buscas?", "Gris uso general · 50 kg", "¿Cuántos bultos?",
      "¿Y la pala: cuadrada o redonda?", "Redonda · mango largo", "¿Cuántas?", "Pedido en curso",
      "Existencias por sede", "Consulto existencias por sede.", "Verificado", "Dato vencido", "Por confirmar", "AGOTADO",
      "Centro: disponible. Norte y Sur: stock pendiente de confirmación con un asesor.", "Recojo en Centro.",
      "Carrito · Recoge en Sede Centro", "Calculado por el sistema", "Mejor que sean 12 bultos.",
      "Listo: 12 bultos. Total actualizado.", "$438.900", "Borrador de cotización · BC-0142", "8 de 8 preguntas resueltas",
      "Gracias. Un asesor revisará tu cotización.", "Pendiente de revisión humana", "Aprobar para facturación",
      "Aprobada para facturación", "Aprobada por: Asesor · Sede Centro"}


def Bt(bar, beat=1.0):
    """Mismo reloj que lib.js: posición de partitura del v04 -> tiempo del v05."""
    i = (bar - 1) * 4 + (beat - 1)
    i += sum(4 * n for b, p, n in HOLDS if i >= (b - 1) * 4 + (p - 1) - 1e-9)
    return BEATS["offset"] + i * 60 / BEATS["bpm"]


CHB = [17, 29, 37, 49]
SECT = [(0, Bt(5), "Gancho"), (Bt(5), Bt(13), "Problema"), (Bt(13), Bt(17), "Revelación")]
for k, (a, b, nme) in enumerate([(17, 29, "① Conversar"), (29, 37, "② Verificar"), (37, 49, "③ Calcular"), (49, 61, "④ Revisar")]):
    SECT += [(Bt(a), Bt(a) + 2, f"Tarjeta 0{k + 1}"), (Bt(a) + 2, Bt(b), nme)]
SECT += [(Bt(61), Bt(67), "Escala"), (Bt(67), DUR + 1, "Final")]
NEXT = {SECT[i][2]: SECT[i + 1][2] for i in range(len(SECT) - 1)}


def sect(t):
    for a, b, nme in SECT:
        if a - 1e-6 <= t < b - 1e-6:
            return nme
    return "Final"


fmt = lambda t: (lambda d: f"{int(d // 600)}:{d % 600 / 10:04.1f}")(round(t * 10))
frames = sorted(RAW["frames"], key=lambda f: f["t"])
tracks = defaultdict(list)
for f in frames:
    seen = defaultdict(int)
    for s, k, X, Y, h, prog, al, blur, occ in f["r"]:
        key = (s.strip("«» "), k, seen[(s, k)])
        seen[(s, k)] += 1
        tracks[key].append((f["t"], X, Y, h, prog, al, blur, occ))

VMAX, ZMAX, HMIN = 300.0, 0.35, 15.0


def speed(tr, i):
    j = i + 1 if i + 1 < len(tr) and abs(tr[i + 1][0] - tr[i][0] - DT) < 1e-3 else i - 1
    if j < 0 or j >= len(tr) or abs(abs(tr[j][0] - tr[i][0]) - DT) > 1e-3:
        return 0.0, 0.0
    return (np.hypot(tr[j][1] - tr[i][1], tr[j][2] - tr[i][2]) / DT, abs(tr[j][3] - tr[i][3]) / max(tr[i][3], 1) / DT)


apps = []
for (s, k, n), tr in tracks.items():
    lvl = 1 if s in N1 else 2 if s in N2 else 3
    cur = None
    for i, (t, X, Y, h, prog, al, blur, occ) in enumerate(tr):
        if not (al > 0.3 and -50 < X < 1970 and -30 < Y < 1110):
            continue
        v, z = speed(tr, i)
        ok = prog >= 0.97 and al >= 0.8 and blur <= 1.5 and not occ and 0 <= X <= 1920 and 0 <= Y <= 1080 and v <= VMAX and z <= ZMAX and h >= HMIN
        if cur is None or t - cur["t1"] > 0.12 or sect(t) != cur["sect"]:
            cur = {"s": s, "k": k, "lvl": lvl, "t0": t, "t1": t, "sect": sect(t), "ok": [], "hok": [], "why": defaultdict(int)}
            apps.append(cur)
        cur["t1"] = t
        if ok:
            cur["ok"].append(t); cur["hok"].append(h)
        else:
            for c, name in ((prog < 0.97, "entrando"), (al < 0.8, "transparente"), (blur > 1.5, "desenfocado"), (occ, "tapado"),
                            (v > VMAX, "en movimiento"), (z > ZMAX, "zoom"), (h < HMIN, "muy pequeño")):
                if c:
                    cur["why"][name] += 1
for a in apps:
    a["need"] = 0.4 + len(a["s"]) / 16
    a["read"] = len(a["ok"]) * DT
    a["rs"] = a["ok"][0] if a["ok"] else None

# lector: un texto N1/N2 a la vez, en orden; lo que no alcanza a terminar lo salta sin gastar tiempo
key = [a for a in apps if a["lvl"] <= 2 and a["rs"] is not None]
done, cursor, got = set(), 0.0, {}
for a in sorted(key, key=lambda a: a["rs"]):
    if a["s"] in done:
        continue
    oks = np.array(a["ok"]); start = max(cursor, a["rs"]); idx = np.where(oks >= start - 1e-6)[0]
    if len(idx) * DT >= a["need"] - 1e-6:
        cursor = oks[idx[int(np.ceil(a["need"] / DT - 1e-6)) - 1]] + DT
        done.add(a["s"]); a["reader"] = True
    got[a["s"]] = max(got.get(a["s"], 0), len(idx) * DT)

# cada texto se juzga en la escena donde aparece por primera vez (verlo después, de fondo, no cuenta)
res = {}
for a in sorted(apps, key=lambda a: a["t0"]):
    if a["lvl"] > 2:
        continue
    r = res.setdefault(a["s"], {"s": a["s"], "lvl": a["lvl"], "need": a["need"], "best": 0.0, "first": a, "readerOK": False, "app": a})
    # lo que asoma en la tarjeta de capítulo se juzga junto con la escena que la sigue
    f = r["first"]["sect"]
    if a["sect"] != f and not (f.startswith("Tarjeta") and NEXT.get(f) == a["sect"]):
        continue
    if a["read"] > r["best"]:
        r["best"], r["app"] = a["read"], a
    r["readerOK"] |= a.get("reader", False)
missing = sorted((N1 | N2) - set(res))

out = []
w = out.append
nOK = {1: 0, 2: 0}; nT = {1: 0, 2: 0}
fails = []
for r in res.values():
    nT[r["lvl"]] += 1
    alone = r["best"] >= r["need"] - 1e-6
    if alone and r["readerOK"]:
        nOK[r["lvl"]] += 1
    else:
        fails.append(r)
w(f"Lectura v05 · {DUR:.0f} s · N1 (mensajes) {nOK[1]}/{nT[1]} · N2 (pruebas clave) {nOK[2]}/{nT[2]}")
if missing:
    w("no aparecen: " + ", ".join(missing))
w("\nNO PASAN (minuto, nivel, legible solo / pide, motivo)")
for r in sorted(fails, key=lambda r: r["first"]["t0"]):
    a = r["app"]
    why = ", ".join(f"{k} {v * DT:.1f}s" for k, v in sorted(a["why"].items(), key=lambda kv: -kv[1])[:3])
    tag = "solo" if r["best"] < r["need"] - 1e-6 else "en cola"
    w(f"  {fmt(r['first']['t0'])}  N{r['lvl']}  {r['best']:.1f}/{r['need']:.1f} s  [{tag}; {why}]  «{r['s']}»")
w("\nTEXTOS CLAVE EN LOS EQUIPOS CON LETRA < 30 px (mediana mientras es legible)")
for r in sorted(res.values(), key=lambda r: r["app"]["t0"]):
    a = r["app"]
    if a["k"] != "main" and a["hok"] and np.median(a["hok"]) < 30:
        w(f"  {fmt(a['t0'])}  {a['k']}  {np.median(a['hok']):.0f} px  «{r['s']}»")
# algo nuevo cada 2-4 s: golpes de sonido y textos nuevos
ev = sorted(set([round(c["t"], 2) for c in CUES] + [round(a["t0"], 2) for a in apps]))
gaps = [(ev[i], ev[i + 1] - ev[i]) for i in range(len(ev) - 1) if ev[i + 1] - ev[i] > 4.0 and ev[i] < Bt(75)]
w("\nTRAMOS DE MÁS DE 4 s SIN NADA NUEVO" + ("" if gaps else ": ninguno"))
for t, g in gaps:
    w(f"  {fmt(t)}  {g:.1f} s")
w("\nCARGA POR SECCIÓN (lectura N1+N2 de primeras apariciones / duración)")
seen = set(); load = defaultdict(float)
for a in sorted(apps, key=lambda a: a["t0"]):
    if a["lvl"] <= 2 and a["s"] not in seen:
        seen.add(a["s"]); load[a["sect"]] += a["need"]
for a0, b0, nme in SECT:
    d = min(b0, DUR) - a0
    w(f"  {nme:14s} {fmt(a0)}  {d:4.1f} s  lectura {load[nme]:4.1f} s  {100 * load[nme] / d:3.0f}%")
txt = "\n".join(out)
open(os.path.join(ROOT, "review", "lectura.txt"), "w", encoding="utf-8").write(txt + "\n")
print("review/lectura.txt", f"N1 {nOK[1]}/{nT[1]}", f"N2 {nOK[2]}/{nT[2]}")
