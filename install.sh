#!/usr/bin/env bash
# Instala la skill motion-studio para Claude Code (global, para tu usuario).
#   ./install.sh                 -> copia a ~/.claude/skills/motion-studio
#   ./install.sh RUTA            -> copia a otra carpeta de skills
set -euo pipefail
aqui="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
destino="${1:-$HOME/.claude/skills}"
[ -f "$aqui/motion-studio/SKILL.md" ] || { echo "No encuentro motion-studio/SKILL.md junto a este script." >&2; exit 1; }
mkdir -p "$destino"
# Se reemplaza la versión instalada. No se deja copia de seguridad aquí: dentro de la carpeta de skills
# Claude Code la leería como una segunda skill con el mismo nombre. Este repositorio es la fuente.
if [ -e "$destino/motion-studio" ]; then rm -rf "$destino/motion-studio"; echo "Se reemplazó la versión instalada."; fi
cp -r "$aqui/motion-studio" "$destino/motion-studio"
echo "Instalada en $destino/motion-studio"
echo "Reinicia Claude Code (o abre una sesión nueva) para que la detecte."
