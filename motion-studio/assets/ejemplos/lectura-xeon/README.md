# Ejemplo: medición de lectura del proyecto XEON

Copia de `lectura.mjs`, `lectura.py` y `holds.json` tal como se usaron en XEON v05. **Referencia, no plantilla.**

Están ligadas a ese proyecto: `lectura.mjs` instrumenta el escenario 3D de XEON (`STAGE.devs.phone` / `imac`) y
`lectura.py` clasifica textos concretos de ese video (conjuntos N1 y N2). Para usar la idea en otro video hay que adaptarlas.

Idea que implementan: un texto es legible si está completo, opaco, nítido, sin taparse y casi quieto, y leerlo pide
0,4 s + 1 s por cada 16 letras. Los mensajes clave deben cumplirlo en su escena.

No forman parte del flujo por defecto de Motion Studio.
