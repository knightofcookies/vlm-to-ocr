# Define the files and directories to delete
$filesToDelete = @(
    "pipeline.db",
    "pipeline.db-wal",
    "pipeline.db-shm",
    "pipeline.log",
    "pipeline.db-journal"
)

$dataDir = "data/"

# Delete the specified files
foreach ($file in $filesToDelete) {
    if (Test-Path $file) {
        Remove-Item -Path $file -Force
        Write-Host "File '$file' has been deleted."
    } else {
        Write-Host "File '$file' does not exist."
    }
}

# Delete the data directory if it exists
if (Test-Path $dataDir) {
    Remove-Item -Path $dataDir -Recurse -Force
    Write-Host "Directory '$dataDir' has been deleted."
} else {
    Write-Host "Directory '$dataDir' does not exist."
}