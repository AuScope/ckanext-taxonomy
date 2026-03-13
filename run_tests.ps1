<#
.SYNOPSIS
    Runs ckanext-taxonomy unit tests inside a Docker container.
.DESCRIPTION
    Builds a test Docker image and runs pytest against the test suite.
    No local Python environment is required.
.PARAMETER Rebuild
    Force a rebuild of the Docker image (skip cache).
.PARAMETER Filter
    Pass a pytest -k filter expression to run specific tests.
.EXAMPLE
    .\run_tests.ps1
.EXAMPLE
    .\run_tests.ps1 -Rebuild
.EXAMPLE
    .\run_tests.ps1 -Filter "test_language"
#>
param(
    [switch]$Rebuild,
    [string]$Filter
)

$ErrorActionPreference = "Stop"
$imageName = "ckanext-taxonomy-test"

$buildArgs = @("build", "-f", "Dockerfile.test", "-t", $imageName, ".")
if ($Rebuild) {
    $buildArgs = @("build", "--no-cache", "-f", "Dockerfile.test", "-t", $imageName, ".")
}

Write-Host "Building test image..." -ForegroundColor Cyan
docker @buildArgs
if ($LASTEXITCODE -ne 0) { throw "Docker build failed" }

$runArgs = @("run", "--rm", $imageName)
if ($Filter) {
    $runArgs = @("run", "--rm", $imageName, "pytest", "-v", "ckanext/taxonomy/tests/test_skos_loader.py", "-k", $Filter)
}

Write-Host "Running tests..." -ForegroundColor Cyan
docker @runArgs
exit $LASTEXITCODE
