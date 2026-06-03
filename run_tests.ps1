param()

Write-Host "Intentando ejecutar tests usando el entorno Python local..."
python .\run_tests.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "El comando devolvió código $LASTEXITCODE"
    exit $LASTEXITCODE
}
