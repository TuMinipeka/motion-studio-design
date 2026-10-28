#!/usr/bin/env bash
# Instala la skill motion-studio para agentes de IA.
#   ./install.sh                 -> copia a ~/.agents/skills/motion-studio
#   ./install.sh RUTA            -> usa el directorio de skills que reconozca tu agente
set -euo pipefail
aqui="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
destino="${1:-$HOME/.agents/skills}"
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
echo "Recarga las skills o abre una sesion nueva de tu agente. Si no detecta esta ruta, pasa su directorio como argumento."
