# Instala la skill motion-studio para agentes de IA.
#   .\install.ps1                 -> copia a $HOME\.agents\skills\motion-studio
#   .\install.ps1 -Destino RUTA   -> usa el directorio de skills que reconozca tu agente
param([string]$Destino = (Join-Path $HOME '.agents\skills'))

$origen = Join-Path $PSScriptRoot 'motion-studio'
if (-not (Test-Path (Join-Path $origen 'SKILL.md'))) { throw "No encuentro motion-studio\SKILL.md junto a este script." }

New-Item -ItemType Directory -Force $Destino | Out-Null
$destinoAbsoluto = (Resolve-Path -LiteralPath $Destino -ErrorAction Stop).ProviderPath
$final = [System.IO.Path]::GetFullPath((Join-Path $destinoAbsoluto 'motion-studio'))
$origenAbsoluto = (Resolve-Path -LiteralPath $origen).ProviderPath
if ([System.IO.Path]::GetDirectoryName($final) -ne $destinoAbsoluto.TrimEnd('\', '/')) {
    throw "El destino resuelto no esta dentro del directorio de skills: $final"
}
if ($final -eq $origenAbsoluto -or $origenAbsoluto.StartsWith($final + '\', [StringComparison]::OrdinalIgnoreCase) -or $final.StartsWith($origenAbsoluto + '\', [StringComparison]::OrdinalIgnoreCase)) {
    throw 'El destino no puede coincidir ni solaparse con la skill de origen.'
}
if ((Test-Path -LiteralPath $final) -and ((Get-Item -LiteralPath $final -Force).Attributes -band [IO.FileAttributes]::ReparsePoint)) {
    throw "El destino es un enlace; elige un directorio de copia: $final"
}
# Se reemplaza la versión instalada. No se deja copia de seguridad aquí: dentro de la carpeta de skills
# el agente podría leerla como una segunda skill con el mismo nombre. Este repositorio es la fuente.
if (Test-Path -LiteralPath $final) { Remove-Item -LiteralPath $final -Recurse -Force; Write-Host "Se reemplazó la versión instalada." }
Copy-Item -LiteralPath $origen -Destination $final -Recurse
Write-Host "Instalada en $final"
Write-Host "Recarga las skills o abre una sesion nueva de tu agente. Si no detecta esta ruta, indica su directorio con -Destino."
