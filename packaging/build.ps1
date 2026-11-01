# Define the target Python executable
$pythonExe = "C:\Users\fabia\AppData\Local\Programs\Python\Python312\python.exe"

# Define the virtual environment path
$venvPath = ".venv"

# Create a virtual environment if it doesn't exist
if (-not (Test-Path $venvPath)) {
    Write-Host "Creating virtual environment at $venvPath..."
    & $pythonExe -m venv $venvPath
    Write-Host "Virtual environment created."
}

# Activate the virtual environment
Write-Host "Activating virtual environment..."
if ($IsWindows) {
    # Windows activation script
    & (Join-Path $venvPath "Scripts\Activate.ps1")
} else {
    # Unix-like activation script (for completeness, though we're on Windows)
    . (Join-Path $venvPath "bin\activate")
}
Write-Host "Virtual environment activated."

# Install dependencies
Write-Host "Installing dependencies from requirements.txt..."
pip install -r ../requirements.txt
Write-Host "Dependencies installed."

# Install PyInstaller
Write-Host "Installing PyInstaller..."
pip install pyinstaller
Write-Host "PyInstaller installed."

# Run PyInstaller
Write-Host "Running PyInstaller..."
pyinstaller packaging/Aurora.spec --noconfirm --clean
Write-Host "PyInstaller finished."

# Print the path to the executable
$exePath = "dist/Aurora/Aurora.exe"
Write-Host " "
Write-Host "============================================================"
Write-Host "     Aurora executable can be found at: $PWD\$exePath"
Write-Host "============================================================"
