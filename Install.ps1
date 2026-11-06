param(
    [ValidateSet('Chinese','Input','Restore','Verify')][string]$Mode='Chinese',
    [string]$GameDirectory='',
    [ValidateSet('Chinese','Input')][string]$VerifyMode='Chinese',
    [string]$VerifyDirectory
)
$ErrorActionPreference='Stop'
Set-StrictMode -Version 2
Add-Type -AssemblyName System.IO.Compression.FileSystem

function Get-Hash([string]$Path) { return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant() }
function Copy-StreamRange($InputStream,$OutputStream,[long]$Offset,[long]$Length) {
    $null=$InputStream.Seek($Offset,[IO.SeekOrigin]::Begin)
    $buffer=New-Object byte[] 1048576
    while($Length -gt 0) {
        $count=$InputStream.Read($buffer,0,[int][Math]::Min($Length,$buffer.Length))
        if($count -le 0) { throw 'Unexpected end of patch/source data.' }
        $OutputStream.Write($buffer,0,$count)
        $Length-=$count
    }
}
function Get-SafeDataPath([string]$Root,[string]$Name) {
    if($Name -notmatch '^(level\d+|sharedassets\d+\.assets)$') { throw "Unexpected resource path: $Name" }
    $rootFull=[IO.Path]::GetFullPath($Root).TrimEnd('\')
    $resolved=[IO.Path]::GetFullPath((Join-Path $rootFull $Name))
    if([IO.Path]::GetDirectoryName($resolved) -ine $rootFull) { throw 'Resource path escaped the game data directory.' }
    return $resolved
}
function Write-PatchedFile($Zip,$Entry,[string]$Source,[string]$Destination) {
    $literalEntry=$Zip.GetEntry([string]$Entry.literal_entry)
    if($null -eq $literalEntry) { throw 'Patch literal entry is missing.' }
    $literalMemory=New-Object IO.MemoryStream
    $literalReader=$literalEntry.Open()
    try { $literalReader.CopyTo($literalMemory) } finally { $literalReader.Dispose() }
    $sourceStream=[IO.File]::OpenRead($Source)
    $outputStream=[IO.File]::Create($Destination)
    try {
        foreach($op in $Entry.ops) {
            if($op[0] -eq 'c') { Copy-StreamRange $sourceStream $outputStream ([long]$op[1]) ([long]$op[2]) }
            elseif($op[0] -eq 'a') { Copy-StreamRange $literalMemory $outputStream ([long]$op[1]) ([long]$op[2]) }
            else { throw 'Unknown patch operation.' }
        }
    } finally { $outputStream.Dispose();$sourceStream.Dispose();$literalMemory.Dispose() }
    if((Get-Item -LiteralPath $Destination).Length -ne [long]$Entry.target_size -or (Get-Hash $Destination) -ne $Entry.target_sha256) {
        throw "Patched file verification failed: $($Entry.path)"
    }
}

$archivePath=Join-Path $PSScriptRoot 'PatchData.zip'
if((Get-Hash $archivePath) -ne '__ARCHIVE_SHA__') { throw 'Patch archive checksum mismatch. Extract a fresh copy.' }

# Search only conventional game locations; otherwise ask for the Content folder.
if([string]::IsNullOrWhiteSpace($GameDirectory)) {
    $candidates=New-Object 'System.Collections.Generic.List[string]'
    foreach($drive in Get-PSDrive -PSProvider FileSystem) {
        if($drive.Root -notmatch '^[A-Za-z]:\\$') { continue }
        foreach($library in @('XboxGames','XBOX')) {
            foreach($title in @('Night in the Woods Win10','Night in the Woods')) {
                $candidate=Join-Path $drive.Root ($library+'\'+$title+'\Content')
                if(Test-Path -LiteralPath (Join-Path $candidate 'Night in the Woods.exe')) {
                    if(-not $candidates.Contains($candidate)) { $candidates.Add($candidate) }
                }
            }
        }
    }
    if($candidates.Count -eq 1) {
        $GameDirectory=$candidates[0]
        Write-Host "Game directory: $GameDirectory"
    } else {
        if($candidates.Count -gt 1) {
            Write-Host '找到多个安装目录，请复制要使用的 Content 目录路径：'
            foreach($candidate in $candidates) { Write-Host "  $candidate" }
        }
        $GameDirectory=Read-Host '请输入游戏 Content 文件夹路径（Xbox > 管理 > 文件 > 浏览；回车取消）'
        if([string]::IsNullOrWhiteSpace($GameDirectory)) { throw '已取消，未修改游戏文件。' }
    }
}
$GameDirectory=$GameDirectory.Trim().Trim('"')

$gameRoot=[IO.Path]::GetFullPath($GameDirectory).TrimEnd('\')
if(-not (Test-Path -LiteralPath (Join-Path $gameRoot 'Night in the Woods.exe'))) { throw "Game executable not found: $gameRoot" }
$dataRoot=Join-Path $gameRoot 'Night in the Woods_Data'
if(-not (Test-Path -LiteralPath $dataRoot)) { throw 'Game data directory not found.' }
$backupRoot=Join-Path $gameRoot '.nitw-xbox-cn-backup'
$statePath=Join-Path $backupRoot 'installed.json'
$previous=@()
if(Test-Path -LiteralPath $statePath) {
    $saved=Get-Content -LiteralPath $statePath -Raw -Encoding UTF8 | ConvertFrom-Json
    $previous=@($saved.files)
}
$zip=[IO.Compression.ZipFile]::OpenRead($archivePath)
try {
    $reader=New-Object IO.StreamReader($zip.GetEntry('manifest.json').Open(),[Text.Encoding]::UTF8)
    try { $manifest=$reader.ReadToEnd() | ConvertFrom-Json } finally { $reader.Dispose() }
    if($manifest.format -ne 1) { throw 'Unsupported patch format.' }
    $selected=@()
    $selectedMode=$Mode.ToLowerInvariant()
    if($Mode -eq 'Verify') { $selectedMode=$VerifyMode.ToLowerInvariant() }
    if($Mode -ne 'Restore') { $selected=@($manifest.files | Where-Object { $_.mode -eq $selectedMode }) }
    if($Mode -eq 'Restore' -and $previous.Count -eq 0) { Write-Host 'No installed patch was recorded.';exit 0 }
    if($Mode -ne 'Verify') {
        if(Get-Process -Name 'Night in the Woods' -ErrorAction SilentlyContinue) { throw 'Close Night in the Woods before installing or restoring. This tool will not close or launch the game.' }
    }
    if($Mode -eq 'Verify') {
        if(-not $VerifyDirectory) { throw 'VerifyDirectory is required for verification mode.' }
        $stageRoot=[IO.Path]::GetFullPath($VerifyDirectory)
        if($stageRoot -ieq $gameRoot -or $stageRoot.StartsWith($gameRoot+'\',[StringComparison]::OrdinalIgnoreCase)) { throw 'Verification output must be outside the game installation.' }
    } else {
        $stageRoot=Join-Path $backupRoot ('transactions\'+[Guid]::NewGuid().ToString('N'))
    }
    $null=New-Item -ItemType Directory -Path $stageRoot -Force
    $plans=New-Object 'System.Collections.Generic.List[object]'
    $selectedNames=@($selected | ForEach-Object { $_.path })
    $allEntries=@($selected)
    if($Mode -ne 'Verify') { $allEntries+=@($previous | Where-Object { $_.path -notin $selectedNames }) }
    foreach($entry in $allEntries) {
        $target=Get-SafeDataPath $dataRoot $entry.path
        $backup=Get-SafeDataPath $backupRoot $entry.path
        $original=$target
        $currentHash=Get-Hash $target
        if($currentHash -ne $entry.original_sha256) {
            $known=@($manifest.files | Where-Object { $_.path -eq $entry.path -and $_.target_sha256 -eq $currentHash })
            if($known.Count -eq 0 -or -not (Test-Path -LiteralPath $backup) -or (Get-Hash $backup) -ne $entry.original_sha256) {
                throw "Version/backup mismatch: $($entry.path). No files have been installed. Use Xbox Verify and Repair if the game was updated."
            }
            $original=$backup
        }
        if((Get-Hash $original) -ne $entry.original_sha256) { throw "Original checksum mismatch: $($entry.path)" }
        $staged=Get-SafeDataPath $stageRoot $entry.path
        if($entry.path -in $selectedNames) {
            Write-PatchedFile $zip $entry $original $staged
            $expected=$entry.target_sha256
        } else {
            Copy-Item -LiteralPath $original -Destination $staged -Force
            $expected=$entry.original_sha256
        }
        $plans.Add([pscustomobject]@{entry=$entry;target=$target;backup=$backup;original=$original;staged=$staged;expected=$expected;current=$currentHash})
    }
    if($Mode -eq 'Verify') {
        Write-Host "Verified $($plans.Count) resource files. Game files were not changed. Output: $stageRoot"
        exit 0
    }
    # Stage and verify every output before copying any resource into the game.
    $undoRoot=Join-Path $stageRoot 'undo'
    $null=New-Item -ItemType Directory -Path $undoRoot -Force
    foreach($plan in $plans) {
        if(-not (Test-Path -LiteralPath $plan.backup)) { Copy-Item -LiteralPath $plan.original -Destination $plan.backup }
        if((Get-Hash $plan.backup) -ne $plan.entry.original_sha256) { throw "Backup verification failed: $($plan.entry.path)" }
        Copy-Item -LiteralPath $plan.target -Destination (Get-SafeDataPath $undoRoot $plan.entry.path)
    }
    $committed=New-Object 'System.Collections.Generic.List[object]'
    try {
        foreach($plan in $plans) {
            if((Get-Hash $plan.target) -ne $plan.current) { throw "File changed during installation: $($plan.entry.path)" }
            $committed.Add($plan)
            Copy-Item -LiteralPath $plan.staged -Destination $plan.target -Force
            if((Get-Hash $plan.target) -ne $plan.expected) { throw 'Installed checksum mismatch.' }
        }
        $record=@($selected | Select-Object path,original_sha256,target_sha256)
        $newState=Join-Path $backupRoot 'installed.new.json'
        @{mode=$Mode;files=$record;installed_at=(Get-Date).ToString('o')} | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $newState -Encoding UTF8
        Move-Item -LiteralPath $newState -Destination $statePath -Force
    } catch {
        foreach($plan in $committed) { Copy-Item -LiteralPath (Get-SafeDataPath $undoRoot $plan.entry.path) -Destination $plan.target -Force }
        throw
    }
    $resolvedStage=[IO.Path]::GetFullPath($stageRoot)
    $allowedStage=[IO.Path]::GetFullPath((Join-Path $backupRoot 'transactions')).TrimEnd('\')+'\'
    if(-not $resolvedStage.StartsWith($allowedStage,[StringComparison]::OrdinalIgnoreCase)) { throw 'Staging cleanup path check failed.' }
    Remove-Item -LiteralPath $resolvedStage -Recurse -Force
    Write-Host "Completed: $Mode. Original resource backups: $backupRoot"
    Write-Host 'No game executable, Xbox authentication file, driver, or save file was changed.'
    Write-Host 'The game has not been launched. For keyboard controls, switch the IME to English; use arrows and Enter/C/F/X/Space.'
} finally { $zip.Dispose() }

