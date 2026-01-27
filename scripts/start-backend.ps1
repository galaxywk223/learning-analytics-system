Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# start-backend.ps1
# 用途：为本地开发启动后端（不应提交到 git）
# 主要步骤：进入 backend，重建 .venv，激活，校验 Python 3.12，安装依赖并运行 flask

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Resolve-Path (Join-Path $ScriptDir "..")
$BackendDir = Join-Path $RepoRoot "backend"
$VenvDir = Join-Path $BackendDir ".venv"
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

# 删除并重建虚拟环境
if (Test-Path $VenvDir) {
  Write-Host "移除已有虚拟环境: $VenvDir"
  Remove-Item -Recurse -Force $VenvDir
}

Write-Host "使用 $PythonExeCmd $($PythonExeArgs -join ' ') 创建虚拟环境..."
& $PythonExeCmd @PythonExeArgs -m venv $VenvDir
if ($LASTEXITCODE -ne 0) {
  Write-Error "错误: 创建虚拟环境失败 (exit code $LASTEXITCODE)。"
  exit $LASTEXITCODE
}
if (-not (Test-Path $VenvDir)) {
  Write-Error "错误: 虚拟环境目录未创建: $VenvDir"
  exit 1
}

# 尝试激活虚拟环境；若不可用则直接使用 venv 的 python 路径
$ActivateDir = Join-Path $VenvDir "Scripts"
$ActivateScript = Join-Path $ActivateDir "Activate.ps1"
$VenvPythonWin = Join-Path $ActivateDir "python.exe"
$VenvPythonPosix = Join-Path $VenvDir "bin\\python"
$VenvPythonPosixAlt = Join-Path $VenvDir "bin\\python3.12"
$VenvPythonWinAlt = Join-Path $ActivateDir "python"
$PythonExe = $null

if (Test-Path $ActivateScript) {
  . $ActivateScript
  $PythonExe = "python"
} elseif (Test-Path $VenvPythonWin) {
  Write-Host "未找到 Activate.ps1，改用 venv 的 python: $VenvPythonWin"
  $PythonExe = $VenvPythonWin
} elseif (Test-Path $VenvPythonWinAlt) {
  Write-Host "未找到 Activate.ps1，改用 venv 的 python: $VenvPythonWinAlt"
  $PythonExe = $VenvPythonWinAlt
} elseif (Test-Path $VenvPythonPosix) {
  Write-Host "未找到 Activate.ps1，改用 venv 的 python: $VenvPythonPosix"
  $PythonExe = $VenvPythonPosix
} elseif (Test-Path $VenvPythonPosixAlt) {
  Write-Host "未找到 Activate.ps1，改用 venv 的 python: $VenvPythonPosixAlt"
  $PythonExe = $VenvPythonPosixAlt
} else {
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

Write-Host "使用的 Python: $(& $PythonExe -c \"import sys;print(sys.executable)\")"
& $PythonExe --version
& $PythonExe -c "import sys,site,platform;print(sys.executable);print(site.getsitepackages());print(platform.python_version())"

# 更新 pip 工具并安装依赖
Write-Host "升级 pip/setuptools/wheel..."
& $PythonExe -m pip install -U pip setuptools wheel

$RequirementsFile = Join-Path $BackendDir "requirements.txt"
if (Test-Path $RequirementsFile) {
  Write-Host "安装 requirements.txt 中的依赖..."
  & $PythonExe -m pip install -r $RequirementsFile
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
