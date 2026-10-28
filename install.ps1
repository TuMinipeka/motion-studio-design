# Instala la skill motion-studio para Claude Code (global, para tu usuario).
#   .\install.ps1                 -> copia a $HOME\.claude\skills\motion-studio
#   .\install.ps1 -Destino RUTA   -> copia a otra carpeta de skills (p. ej. .claude\skills de un proyecto)
param([string]$Destino = (Join-Path $HOME '.claude\skills'))

$origen = Join-Path $PSScriptRoot 'motion-studio'
if (-not (Test-Path (Join-Path $origen 'SKILL.md'))) { throw "No encuentro motion-studio\SKILL.md junto a este script." }

$final = Join-Path $Destino 'motion-studio'
New-Item -ItemType Directory -Force $Destino | Out-Null
# Se reemplaza la versión instalada. No se deja copia de seguridad aquí: dentro de la carpeta de skills
# Claude Code la leería como una segunda skill con el mismo nombre. Este repositorio es la fuente.
if (Test-Path $final) { Remove-Item -Recurse -Force $final; Write-Host "Se reemplazó la versión instalada." }
Copy-Item -Recurse $origen $final
Write-Host "Instalada en $final"
Write-Host "Reinicia Claude Code (o abre una sesión nueva) para que la detecte."
