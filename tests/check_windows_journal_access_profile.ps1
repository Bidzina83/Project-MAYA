$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
$compiler = Join-Path $env:WINDIR 'Microsoft.NET/Framework64/v4.0.30319/csc.exe'
$runtime = Join-Path $root 'src/project_maya/windows_runtime'
$sources = @(Get-ChildItem -LiteralPath $runtime -Filter '*.cs' | ForEach-Object FullName)
$fixture = Join-Path $PSScriptRoot 'windows_journal_access_profile_fixtures.cs'
$refs = '/reference:System.Windows.Forms.dll,System.Drawing.dll,System.Web.Extensions.dll,System.IO.Compression.dll,System.IO.Compression.FileSystem.dll'
$scratch = Join-Path $env:TEMP ('MayaJournalAccessProfile-' + [guid]::NewGuid().ToString('N'))
$null = New-Item -ItemType Directory -Path $scratch
$common = 'HERMES_BRIDGE,HERMES_CONSTRUCTION,HERMES_IMPORT'
$access = "HERMES_JOURNAL_ACCESS,$common"
$compileOnly = Join-Path $scratch 'compile-only.exe'
& $compiler /nologo /warnaserror+ /platform:x64 /target:exe /main:ProjectMaya.WindowsRuntime.ProtectedPython "/define:$access" $refs "/out:$compileOnly" $sources
if ($LASTEXITCODE -ne 0) { throw 'Access launcher compilation failed' }
foreach ($profile in @($access,$common,"$common,HERMES_MODEL,HERMES_MODEL_VALIDATION,HERMES_MODEL_FINAL")) {
    $out = Join-Path $scratch ('fixture-' + [guid]::NewGuid().ToString('N') + '.exe')
    & $compiler /nologo /warnaserror+ /platform:x64 /target:exe /main:JournalAccessProfileFixtures "/define:$profile" $refs "/out:$out" $sources $fixture
    if ($LASTEXITCODE -ne 0) { throw "Compile failed: $profile" }
    & $out
    if ($LASTEXITCODE -ne 0) { throw "Fixture failed: $profile" }
}
$invalid = @(foreach ($missing in $common.Split(',')) {
    ($access.Split(',') | Where-Object { $_ -ne $missing }) -join ','
})
$launcher = Get-Content -LiteralPath (Join-Path $runtime 'ProtectedPython.cs') |
    Where-Object { $_ -like '#if HERMES_JOURNAL_ACCESS &&*' } | Select-Object -First 1
$exclusions = @([regex]::Matches($launcher,'HERMES_MODEL[A-Z_]*|HERMES_STATE|HERMES_MEMORY|MAYA_[A-Z_]+') | ForEach-Object Value)
if ($exclusions.Count -lt 22) { throw 'Missing incompatible flags in access-profile guard' }
foreach ($flag in $exclusions) { $invalid += "$access,$flag" }
foreach ($profile in $invalid) {
    $out = Join-Path $scratch 'invalid.exe'
    $diagnostics = & $compiler /nologo /platform:x64 /target:exe /main:JournalAccessProfileFixtures "/define:$profile" $refs "/out:$out" $sources $fixture
    if ($LASTEXITCODE -eq 0 -or -not ($diagnostics -match 'HERMES_JOURNAL_ACCESS requires')) {
        throw "Missing dedicated compile rejection: $profile"
    }
}
"Journal access compile exclusions: $($invalid.Count)"
$launcherText = Get-Content -LiteralPath (Join-Path $runtime 'ProtectedPython.cs') -Raw
if ($launcherText -notmatch '(?s)screen.Stage = "job_stop";\s*isolation.Stop\(\);.*?bridge.Stop\(\);.*?ProductFiles.Revoke\(.*?isolation.DeleteProfile\(\);.*?isolation.RemoveNetwork\(\);') {
    throw 'Stop-before-revocation order changed'
}
'Journal access cleanup ordering: source check passed'
