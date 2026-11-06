// La reanudación solo reutiliza segmentos de las mismas fuentes y configuración.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';

export function huellaProyecto(root, { salida = 'exportaciones', extra = {} } = {}) {
  const h = crypto.createHash('sha256');
  const fuera = path.resolve(root, salida);
  const omitir = new Set(['.git', 'node_modules', '__pycache__', 'review', 'exportaciones']);
  const buffer = Buffer.alloc(1024 * 1024);
  function recorrer(dir) {
    for (const entry of fs.readdirSync(dir, { withFileTypes: true }).sort((a, b) => a.name.localeCompare(b.name))) {
      const file = path.join(dir, entry.name);
      if (file === fuera || omitir.has(entry.name) || entry.isSymbolicLink()) continue;
      if (entry.isDirectory()) { recorrer(file); continue; }
      // La mezcla se vuelve a unir en cada exportación; cambiar solo el audio no rehace la imagen.
      if (!entry.isFile() || /\.(md|log|pyc|wav|mp3|m4a|aac|flac|ogg|opus)$/i.test(entry.name)) continue;
      h.update(path.relative(root, file).split(path.sep).join('/') + '\0');
      const fd = fs.openSync(file, 'r');
      try {
        let n;
        while ((n = fs.readSync(fd, buffer, 0, buffer.length, null)) > 0) h.update(buffer.subarray(0, n));
      } finally { fs.closeSync(fd); }
      h.update('\0');
    }
  }
  recorrer(root);
  h.update(JSON.stringify(extra));
  return h.digest('hex').slice(0, 20);
}
