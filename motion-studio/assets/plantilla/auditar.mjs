// Motion Studio · auditor estático del contrato de renderizado (sin navegador, sin dependencias).
//   node auditar.mjs            revisa el código del proyecto
//   node auditar.mjs ruta       revisa otra carpeta
// Sale con código 1 si hay ERRORES. Los AVISOS señalan fuentes de no determinismo que conviene revisar.
//
// Reglas (ERROR): sin transiciones CSS, sin setTimeout/setInterval, sin requestAnimationFrame y sin aleatorios sin semilla
// (Math.random, crypto.getRandomValues). Reglas (AVISO): relojes reales (Date.now, new Date, performance.now) y animaciones
// por tiempo (CSS animation/@keyframes, element.animate), que también hacen que un fotograma dependa de algo más que de t.
// También avisa de texto dibujado con fillText/strokeText fuera de lib.js (la caché de glifos de Chrome lo vuelve no
// determinista bajo escala o rotación: usa crearTexto) y de un contexto 2D que no se reinicia con ctx.reset().
// Se ignoran comentarios y cadenas de texto. No se revisan node_modules, review, exportaciones, audio, assets, *.min.js
// ni los scripts auxiliares cuyo nombre empieza por _ (diagnósticos que no forman parte del video).
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const raiz = path.resolve(process.argv[2] || path.dirname(fileURLToPath(import.meta.url)));
const OMITIR_DIRS = new Set(['node_modules', 'review', 'exportaciones', 'audio', 'assets', '.git']);
const OMITIR_ARCHIVOS = new Set(['render.mjs', 'auditar.mjs', 'lectura.mjs']);

const REGLAS_JS = [
  ['ERROR', /\brequestAnimationFrame\s*\(/, 'requestAnimationFrame depende del reloj real; usa window.seek(t)'],
  ['ERROR', /\bsetTimeout\s*\(/, 'setTimeout depende del reloj real; deriva todo de t'],
  ['ERROR', /\bsetInterval\s*\(/, 'setInterval depende del reloj real; deriva todo de t'],
  ['ERROR', /\bMath\.random\s*\(/, 'Math.random no tiene semilla; usa mulberry32/srand de lib.js'],
  ['ERROR', /\bcrypto\.getRandomValues\s*\(/, 'aleatorio sin semilla; usa mulberry32/srand de lib.js'],
  ['ERROR', /\.style\.transition\b/, 'transición CSS asignada por script'],
  ['AVISO', /\bDate\.now\s*\(/, 'reloj real: un fotograma no debe depender de la hora'],
  ['AVISO', /\bnew\s+Date\s*\(/, 'reloj real: un fotograma no debe depender de la hora'],
  ['AVISO', /\bperformance\.now\s*\(/, 'reloj real: un fotograma no debe depender del tiempo de ejecución'],
  ['AVISO', /\.animate\s*\(/, 'animación por tiempo (Web Animations API)'],
  ['AVISO', /\.style\.animation\b/, 'animación CSS asignada por script'],
  ['AVISO', /\.(fillText|strokeText)\s*\(/, 'fillText/strokeText directo: bajo escala o rotación puede variar entre fotogramas; usa texto()/numero() de crearTexto (lib.js)', 'lib.js'],
];
const REGLAS_CSS = [
  ['ERROR', /\btransition(?:-[a-z]+)?\s*:/, 'transición CSS'],
  ['AVISO', /@keyframes\b/, 'animación CSS por tiempo'],
  ['AVISO', /\banimation(?:-[a-z]+)?\s*:/, 'animación CSS por tiempo'],
];

// Sustituye comentarios y cadenas por espacios conservando los saltos de línea (para mantener los números de línea).
function limpiarJS(s) {
  let o = '', i = 0;
  const blanco = x => x.replace(/[^\n]/g, ' ');
  while (i < s.length) {
    const c = s[i], d = s[i + 1];
    if (c === '/' && d === '/') { const j = s.indexOf('\n', i); const f = j < 0 ? s.length : j; o += blanco(s.slice(i, f)); i = f; }
    else if (c === '/' && d === '*') { const j = s.indexOf('*/', i + 2); const f = j < 0 ? s.length : j + 2; o += blanco(s.slice(i, f)); i = f; }
    else if (c === '"' || c === "'" || c === '`') {
      let j = i + 1;
      while (j < s.length && s[j] !== c && !(c !== '`' && s[j] === '\n')) j += s[j] === '\\' ? 2 : 1;
      o += c + blanco(s.slice(i + 1, j)) + (s[j] === c ? c : ''); i = Math.min(s.length, j + 1);
    } else { o += c; i++; }
  }
  return o;
}
const limpiarCSS = s => s.replace(/\/\*[\s\S]*?\*\//g, m => m.replace(/[^\n]/g, ' '));
const lineaDe = (txt, idx) => txt.slice(0, idx).split('\n').length;

function aplicar(reglas, txt, offsetLinea, archivo, hallazgos) {
  txt.split('\n').forEach((linea, n) => {
    for (const [nivel, re, msg, excepto] of reglas)
      if (re.test(linea) && path.basename(archivo) !== excepto) hallazgos.push({ nivel, archivo, linea: offsetLinea + n, msg });
  });
}

// El estado del contexto 2D (transformación, lineCap, textAlign, font…) persiste entre llamadas a seek(t).
function revisarContexto(codigo, offsetLinea, archivo, hallazgos) {
  const m = codigo.match(/getContext\s*\(\s*['"]2d['"]/);
  if (m && path.basename(archivo) !== 'lib.js' && !/\.reset\s*\(\s*\)/.test(codigo))
    hallazgos.push({ nivel: 'AVISO', archivo, linea: offsetLinea + lineaDe(codigo, m.index) - 1,
      msg: 'contexto 2D sin ctx.reset(): su estado pasa de un fotograma a otro; llámalo al inicio de render(t) (un lienzo auxiliar que se dibuja una sola vez al cargar no lo necesita)' });
}

function revisar(archivo, hallazgos) {
  const src = fs.readFileSync(archivo, 'utf8'), rel = path.relative(raiz, archivo), ext = path.extname(archivo);
  if (ext === '.js' || ext === '.mjs') { aplicar(REGLAS_JS, limpiarJS(src), 1, rel, hallazgos); revisarContexto(src, 1, rel, hallazgos); }
  else if (ext === '.css') aplicar(REGLAS_CSS, limpiarCSS(src), 1, rel, hallazgos);
  else if (ext === '.html') {
    const html = src.replace(/<!--[\s\S]*?-->/g, m => m.replace(/[^\n]/g, ' '));
    for (const m of html.matchAll(/<script\b([^>]*)>([\s\S]*?)<\/script>/gi))
      if (!/\bsrc\s*=/.test(m[1])) {
        const linea = lineaDe(html, m.index + m[0].indexOf('>') + 1);
        aplicar(REGLAS_JS, limpiarJS(m[2]), linea, rel, hallazgos); revisarContexto(m[2], linea, rel, hallazgos);
      }
    for (const m of html.matchAll(/<style\b[^>]*>([\s\S]*?)<\/style>/gi))
      aplicar(REGLAS_CSS, limpiarCSS(m[1]), lineaDe(html, m.index + m[0].indexOf('>') + 1), rel, hallazgos);
    for (const m of html.matchAll(/\bstyle\s*=\s*"([^"]*)"/gi)) aplicar(REGLAS_CSS, m[1], lineaDe(html, m.index), rel, hallazgos);
  }
}

function recorrer(dir, hallazgos, contador) {
  for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
    const p = path.join(dir, e.name);
    if (e.isDirectory()) { if (!OMITIR_DIRS.has(e.name)) recorrer(p, hallazgos, contador); }
    else if (/\.(html|js|mjs|css)$/.test(e.name) && !OMITIR_ARCHIVOS.has(e.name) && !/\.min\./.test(e.name) && !e.name.startsWith('_')) { revisar(p, hallazgos); contador.n++; }
  }
}

const hallazgos = [], contador = { n: 0 };
recorrer(raiz, hallazgos, contador);
const errores = hallazgos.filter(h => h.nivel === 'ERROR').length, avisos = hallazgos.length - errores;
for (const h of hallazgos) console.log(`${h.nivel.padEnd(5)} ${h.archivo}:${h.linea}  ${h.msg}`);
console.log(`${contador.n} archivos revisados · ${errores} errores · ${avisos} avisos`);
process.exitCode = errores ? 1 : 0;
