$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
$tools = Join-Path $root '.tools'
New-Item -ItemType Directory -Force $tools | Out-Null
if (!(Test-Path "$tools/node/node.exe")) {
    Invoke-WebRequest 'https://nodejs.org/dist/v22.16.0/node-v22.16.0-win-x64.zip' -OutFile "$tools/node.zip" -UseBasicParsing
    Expand-Archive "$tools/node.zip" -DestinationPath $tools -Force
    Move-Item "$tools/node-v22.16.0-win-x64" "$tools/node" -Force
}
if (!(Test-Path "$tools/uv/uv.exe")) {
    Invoke-WebRequest 'https://github.com/astral-sh/uv/releases/latest/download/uv-x86_64-pc-windows-msvc.zip' -OutFile "$tools/uv.zip" -UseBasicParsing
    Expand-Archive "$tools/uv.zip" -DestinationPath "$tools/uv" -Force
}
$env:PATH = "$tools/node;$env:PATH"
& "$tools/node/node.exe" --version
& "$tools/uv/uv.exe" venv --python 3.12 "$root/.venv"
if ($LASTEXITCODE -ne 0) { throw 'Python environment creation failed' }
& "$tools/uv/uv.exe" pip install --python "$root/.venv/Scripts/python.exe" -r "$root/backend/requirements.txt"
if ($LASTEXITCODE -ne 0) { throw 'Python dependency installation failed' }
& "$tools/node/npm.cmd" --prefix "$root/frontend" install --no-audit --no-fund
if ($LASTEXITCODE -ne 0) { throw 'Frontend dependency installation failed' }
Write-Output 'PlantMind dependencies installed successfully.'