param(
  [switch]$RecreateVenv,
  [switch]$ReinstallDeps
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# start-backend.ps1
# 用途：为本地开发启动后端（不应提交到 git）
# 主要步骤：进入 backend，按需创建 .venv，校验 Python 3.12，按需安装依赖并运行 flask

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Resolve-Path (Join-Path $ScriptDir "..")
$BackendDir = Join-Path $RepoRoot "backend"
$VenvDir = Join-Path $BackendDir ".venv"
$RequirementsFile = Join-Path $BackendDir "requirements.txt"
$RequirementsHashFile = Join-Path $VenvDir ".requirements.sha256"
$RequiredPythonMinor = "3.12"
$PythonBin = "python3.12"
$PythonExeCmd = $null
$PythonExeArgs = @()

Write-Host "切换到后端目录: $BackendDir"
Set-Location $BackendDir

# 选择可用的 Python 命令：优先 Windows Launcher (py -3.12) -> python3.12 -> python
if (Get-Command "py" -ErrorAction SilentlyContinue) {
  $PythonExeCmd = "py"
  $PythonExeArgs = @("-3.12")
} elseif (Get-Command $PythonBin -ErrorAction SilentlyContinue) {
  $PythonExeCmd = $PythonBin
} elseif (Get-Command "python" -ErrorAction SilentlyContinue) {
  $PythonExeCmd = "python"
} else {
  Write-Error "错误: 未找到 py/python3.12/python。请先安装 Python 3.12 或调整 PYTHON_BIN 变量。"
  exit 1
}

function Get-VenvPythonPath {
  param([string]$Dir)
  $candidates = @(
    (Join-Path $Dir "Scripts\\python.exe"),
    (Join-Path $Dir "Scripts\\python"),
    (Join-Path $Dir "bin\\python"),
    (Join-Path $Dir "bin\\python3.12")
  )
  foreach ($candidate in $candidates) {
    if (Test-Path $candidate) {
      return $candidate
    }
  }
  return $null
}

function New-Venv {
  param([string]$Dir)
  if (Test-Path $Dir) {
    Write-Host "移除已有虚拟环境: $Dir"
    Remove-Item -Recurse -Force $Dir
  }
  Write-Host "使用 $PythonExeCmd $($PythonExeArgs -join ' ') 创建虚拟环境..."
  & $PythonExeCmd @PythonExeArgs -m venv $Dir
  if ($LASTEXITCODE -ne 0) {
    Write-Error "错误: 创建虚拟环境失败 (exit code $LASTEXITCODE)。"
    exit $LASTEXITCODE
  }
  if (-not (Test-Path $Dir)) {
    Write-Error "错误: 虚拟环境目录未创建: $Dir"
    exit 1
  }
}

$NeedCreateVenv = $RecreateVenv -or -not (Test-Path $VenvDir)
if (-not $NeedCreateVenv) {
  $existingVenvPython = Get-VenvPythonPath -Dir $VenvDir
  if (-not $existingVenvPython) {
    Write-Host "现有虚拟环境不完整，重新创建: $VenvDir"
    $NeedCreateVenv = $true
  } else {
    $existingVersion = & $existingVenvPython -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
    if ($existingVersion -ne $RequiredPythonMinor) {
      Write-Host "现有虚拟环境 Python 版本为 $existingVersion，要求 $RequiredPythonMinor，重新创建。"
      $NeedCreateVenv = $true
    }
  }
}

if ($NeedCreateVenv) {
  New-Venv -Dir $VenvDir
} else {
  Write-Host "复用已有虚拟环境: $VenvDir"
}

# 直接使用 venv 的 python 路径，避免依赖激活脚本
$PythonExe = Get-VenvPythonPath -Dir $VenvDir
if (-not $PythonExe) {
  $ActivateDir = Join-Path $VenvDir "Scripts"
  Write-Error "错误: 未找到虚拟环境的 python，可执行文件不存在。请确认 venv 是否创建成功。"
  Write-Host "诊断: $VenvDir 内容如下："
  Get-ChildItem -Force -Path $VenvDir | Format-Table -AutoSize
  if (Test-Path $ActivateDir) {
    Write-Host "诊断: $ActivateDir 内容如下："
    Get-ChildItem -Force -Path $ActivateDir | Format-Table -AutoSize
  }
  $BinDir = Join-Path $VenvDir "bin"
  if (Test-Path $BinDir) {
    Write-Host "诊断: $BinDir 内容如下："
    Get-ChildItem -Force -Path $BinDir | Format-Table -AutoSize
  }
  exit 1
}

$PythonPath = & $PythonExe -c "import sys;print(sys.executable)"
Write-Host "使用的 Python: $PythonPath"
& $PythonExe --version
& $PythonExe -c "import sys,site,platform;print(sys.executable);print(site.getsitepackages());print(platform.python_version())"

# 按需安装依赖：首次创建、requirements 变化或显式要求
if (Test-Path $RequirementsFile) {
  $currentReqHash = (Get-FileHash -Algorithm SHA256 -Path $RequirementsFile).Hash
  $previousReqHash = $null
  if (Test-Path $RequirementsHashFile) {
    $previousReqHash = (Get-Content $RequirementsHashFile -Raw).Trim()
  }

  $needInstallDeps = $ReinstallDeps -or $NeedCreateVenv -or ($currentReqHash -ne $previousReqHash)

  if ($needInstallDeps) {
    Write-Host "安装/更新后端依赖..."
    & $PythonExe -m pip install -U pip setuptools wheel
    & $PythonExe -m pip install -r $RequirementsFile
    Set-Content -Path $RequirementsHashFile -Value $currentReqHash -Encoding ascii -NoNewline
  } else {
    Write-Host "requirements.txt 未变化，跳过依赖安装。需要强制重装可加参数 -ReinstallDeps。"
  }
} else {
  Write-Host "警告: 在 $BackendDir 中未找到 requirements.txt，跳过依赖安装。"
}

# 确保 FLASK_APP 被设置，如果不存在，尝试设置为 run.py
if (-not $env:FLASK_APP) {
  $RunPy = Join-Path $BackendDir "run.py"
  if (Test-Path $RunPy) {
    $env:FLASK_APP = "run.py"
    Write-Host "设置 FLASK_APP=run.py"
  } else {
    Write-Host "注意: 未设置 FLASK_APP 环境变量，且未找到 run.py。请手动设置 FLASK_APP。"
  }
}

# 显示 flask 版本并运行
Write-Host "Flask 版本："
& $PythonExe -m flask --version

Write-Host "启动 Flask 开发服务器... (按 Ctrl+C 停止)"
& $PythonExe -m flask run
