#!/usr/bin/env bash
# Instala la skill motion-studio para agentes de IA.
#   ./install.sh                 -> copia a ~/.agents/skills/motion-studio
#   ./install.sh RUTA            -> usa el directorio de skills que reconozca tu agente
#   ./install.sh RUTA --sistema  -> instala también Node.js y FFmpeg (brew/apt) si faltan
#   MOTION_SIN_HERRAMIENTAS=1 ./install.sh -> solo copia la skill
# Después de copiar, ejecuta scripts/preparar.py: Playwright, Chromium, fuentes, numpy y Pillow, y comprueba FFmpeg y GPU.
set -euo pipefail
aqui="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
sistema=""
args=()
for a in "$@"; do if [ "$a" = "--sistema" ]; then sistema="--sistema"; else args+=("$a"); fi; done
destino="${args[0]:-$HOME/.agents/skills}"
[ -f "$aqui/motion-studio/SKILL.md" ] || { echo "No encuentro motion-studio/SKILL.md junto a este script." >&2; exit 1; }
mkdir -p "$destino"
destino="$(cd "$destino" && pwd -P)"
final="$destino/motion-studio"
case "$final/" in
  "$aqui/motion-studio/"*) echo "El destino no puede coincidir ni solaparse con la skill de origen." >&2; exit 1 ;;
esac
case "$aqui/motion-studio/" in
  "$final/"*) echo "El destino no puede contener la skill de origen." >&2; exit 1 ;;
esac
[ ! -L "$final" ] || { echo "El destino es un enlace; elige un directorio de copia: $final" >&2; exit 1; }
# Se reemplaza la versión instalada. No se deja copia de seguridad aquí: dentro de la carpeta de skills
# el agente podría leerla como una segunda skill con el mismo nombre. Este repositorio es la fuente.
if [ -e "$final" ]; then rm -rf -- "$final"; echo "Se reemplazó la versión instalada."; fi
cp -r "$aqui/motion-studio" "$final"
echo "Instalada en $destino/motion-studio"

if [ -z "${MOTION_SIN_HERRAMIENTAS:-}" ]; then
  py="$(command -v python3 || command -v python || true)"
  if [ -z "$py" ]; then
    echo "AVISO: no encuentro Python 3; instálalo y ejecuta: python3 \"$final/scripts/preparar.py\"" >&2
  elif ! "$py" "$final/scripts/preparar.py" $sistema; then
    echo "AVISO: faltan herramientas; sigue las indicaciones de arriba (o repite con --sistema)." >&2
  fi
fi
echo "Recarga las skills o abre una sesion nueva de tu agente. Si no detecta esta ruta, pasa su directorio como argumento."
