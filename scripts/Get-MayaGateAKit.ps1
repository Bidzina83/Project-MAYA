param(
    [string]$ArchiveSha256,
    [string]$ManifestSha256,
    [switch]$PermitDownload
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$script:MayaLimit = 64MB
$script:MayaEndpoint = 'https://stmayagatea26101701.blob.core.windows.net/gatea-input/python-comparison-26h2.zip'
$script:MayaEmptyDirectories = @(
    '.codex-build/governance-v2-lpac-stage/state',
    '.codex-build/governance-v2-lpac-stage/host',
    'observer/authorization',
    'observer/attempts'
)

function Assert-MayaTransfer {
    param([bool]$Condition)
    if (-not $Condition) { throw [IO.InvalidDataException]::new('transfer.validation_failed') }
}

function Get-MayaStreamHash {
    param([IO.Stream]$Stream)
    $sha = [Security.Cryptography.SHA256]::Create()
    try { return [BitConverter]::ToString($sha.ComputeHash($Stream)).Replace('-', '').ToLowerInvariant() }
    finally { $sha.Dispose() }
}

function Get-MayaFileHash {
    param([string]$Path)
    $stream = [IO.File]::OpenRead($Path)
    try { return Get-MayaStreamHash $stream } finally { $stream.Dispose() }
}

function Assert-MayaPlainPath {
    param([string]$Path)
    $current = [IO.Path]::GetFullPath($Path)
    while ($current) {
        # Get-Item also checks existing reparse entries, not just their targets.
        $item = Get-Item -LiteralPath $current -Force -ErrorAction SilentlyContinue
        if ($null -ne $item) {
            Assert-MayaTransfer (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -eq 0)
        } elseif (Test-Path -LiteralPath $current) {
            throw [IO.InvalidDataException]::new('transfer.path_unreadable')
        }
        $current = [IO.Path]::GetDirectoryName($current)
    }
}

function Assert-MayaRelativeName {
    param([string]$Name)
    Assert-MayaTransfer ($Name.Length -gt 0 -and $Name.Length -le 220)
    Assert-MayaTransfer ($Name -notmatch '[\\:\x00-\x1f\x7f-\uffff<>|"*?]')
    foreach ($part in $Name.Split('/')) {
        Assert-MayaTransfer ($part.Length -gt 0 -and $part -ne '.' -and $part -ne '..')
        Assert-MayaTransfer (-not $part.EndsWith('.') -and -not $part.EndsWith(' '))
        Assert-MayaTransfer ($part -notmatch '^(?i:CON|PRN|AUX|NUL|COM[0-9]|LPT[0-9])(?:\.|$)')
    }
}

function Get-MayaSasUri {
    param([string]$Token, [DateTimeOffset]$Now)
    Assert-MayaTransfer ($Token.Length -gt 0 -and $Token.Length -le 4096)
    Assert-MayaTransfer ($Token -notmatch '[?#\s]' -and $Token -notmatch '%(?![0-9a-fA-F]{2})')
    $fields = @{}
    $allowed = @('sv', 'sr', 'sp', 'spr', 'st', 'se', 'skoid', 'sktid', 'skt', 'ske', 'sks', 'skv', 'sig')
    foreach ($pair in $Token.Split('&')) {
        $parts = $pair.Split(@('='), 2)
        Assert-MayaTransfer ($parts.Count -eq 2 -and $allowed -ccontains $parts[0])
        Assert-MayaTransfer (-not $fields.ContainsKey($parts[0]) -and $parts[1].Length -gt 0)
        $fields.Add($parts[0], [Uri]::UnescapeDataString($parts[1]))
    }
    Assert-MayaTransfer ($fields.Count -eq $allowed.Count)
    Assert-MayaTransfer ($fields.sp -ceq 'r' -and $fields.sr -ceq 'b' -and $fields.spr -ceq 'https' -and $fields.sks -ceq 'b')
    foreach ($key in @('sv', 'skv')) { Assert-MayaTransfer ($fields[$key] -match '^\d{4}-\d{2}-\d{2}$') }
    foreach ($key in @('skoid', 'sktid')) {
        Assert-MayaTransfer ($fields[$key] -match '^[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}$')
        Assert-MayaTransfer ([Guid]::Parse($fields[$key]) -ne [Guid]::Empty)
    }
    $dates = @{}
    foreach ($key in @('st', 'se', 'skt', 'ske')) {
        Assert-MayaTransfer ($fields[$key] -match '^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$')
        $dates[$key] = [DateTimeOffset]::Parse($fields[$key], [Globalization.CultureInfo]::InvariantCulture)
    }
    Assert-MayaTransfer ($dates.st -le $Now -and $dates.se -gt $Now)
    Assert-MayaTransfer ($dates.se -gt $dates.st -and ($dates.se - $dates.st).TotalMinutes -le 30)
    Assert-MayaTransfer ($dates.skt -le $dates.st -and $dates.ske -ge $dates.se)
    Assert-MayaTransfer (($dates.ske - $dates.skt).TotalMinutes -le 30)
    Assert-MayaTransfer ([Convert]::FromBase64String($fields.sig).Length -eq 32)
    return [Uri]::new($script:MayaEndpoint + '?' + $Token)
}

function New-MayaHttpHandler {
    $handler = [Net.Http.HttpClientHandler]::new()
    $handler.AllowAutoRedirect = $false
    $handler.UseProxy = $false
    $handler.UseCookies = $false
    $handler.UseDefaultCredentials = $false
    $handler.PreAuthenticate = $false
    $handler.AutomaticDecompression = [Net.DecompressionMethods]::None
    $handler.SslProtocols = [Security.Authentication.SslProtocols]::Tls12
    return $handler
}

function Copy-MayaBoundedStream {
    param([IO.Stream]$InputStream, [IO.Stream]$OutputStream, [long]$Length,
          [Threading.CancellationToken]$CancellationToken)
    Assert-MayaTransfer ($Length -ge 0 -and $Length -le $script:MayaLimit)
    $buffer = [byte[]]::new(32768)
    [long]$count = 0
    while ($true) {
        $CancellationToken.ThrowIfCancellationRequested()
        $read = $InputStream.ReadAsync($buffer, 0, $buffer.Length, $CancellationToken).GetAwaiter().GetResult()
        if ($read -eq 0) { break }
        $count += $read
        Assert-MayaTransfer ($count -le $Length)
        $OutputStream.Write($buffer, 0, $read)
    }
    Assert-MayaTransfer ($count -eq $Length)
}

function Receive-MayaResponse {
    param([Net.Http.HttpResponseMessage]$Response, [Uri]$ExpectedUri,
          [IO.Stream]$OutputStream, [Threading.CancellationToken]$CancellationToken)
    Assert-MayaTransfer ([int]$Response.StatusCode -eq 200)
    Assert-MayaTransfer ($null -ne $Response.RequestMessage -and
        $Response.RequestMessage.RequestUri.OriginalString -ceq $ExpectedUri.OriginalString)
    Assert-MayaTransfer ($null -ne $Response.Content -and
        $null -ne $Response.Content.Headers.ContentLength -and
        $Response.Content.Headers.ContentEncoding.Count -eq 0)
    $stream = $Response.Content.ReadAsStreamAsync().GetAwaiter().GetResult()
    try { Copy-MayaBoundedStream $stream $OutputStream $Response.Content.Headers.ContentLength $CancellationToken }
    finally { $stream.Dispose() }
}

function Expand-MayaKit {
    param([string]$ArchivePath, [string]$Destination, [string]$ExpectedArchiveHash,
          [string]$ExpectedManifestHash)
    Assert-MayaTransfer ($ExpectedArchiveHash -cmatch '^[0-9a-f]{64}$' -and $ExpectedManifestHash -cmatch '^[0-9a-f]{64}$')
    Assert-MayaPlainPath $ArchivePath
    Assert-MayaPlainPath $Destination
    Assert-MayaTransfer (-not (Test-Path -LiteralPath $Destination))
    Assert-MayaTransfer ((Get-Item -LiteralPath $ArchivePath).Length -le $script:MayaLimit)
    # Hold the same non-writable archive handle for hashing, validation and extraction.
    $file = [IO.File]::Open($ArchivePath, [IO.FileMode]::Open, [IO.FileAccess]::Read, [IO.FileShare]::Read)
    try {
        Assert-MayaTransfer ((Get-MayaStreamHash $file) -ceq $ExpectedArchiveHash)
        $file.Position = 0
        $zip = [IO.Compression.ZipArchive]::new($file, [IO.Compression.ZipArchiveMode]::Read, $true)
        try {
            Assert-MayaTransfer ($zip.Entries.Count -gt 1 -and $zip.Entries.Count -le 4096)
            $entries = @{}
            [long]$expanded = 0
            foreach ($entry in $zip.Entries) {
                Assert-MayaRelativeName $entry.FullName
                Assert-MayaTransfer (-not $entries.ContainsKey($entry.FullName))
                Assert-MayaTransfer ($entry.Length -ge 0 -and $entry.Length -le $script:MayaLimit)
                Assert-MayaTransfer (($entry.ExternalAttributes -band 0x400) -eq 0)
                $unixType = ($entry.ExternalAttributes -shr 16) -band 0xf000
                Assert-MayaTransfer ($unixType -eq 0 -or $unixType -eq 0x8000)
                $expanded += $entry.Length
                Assert-MayaTransfer ($expanded -le $script:MayaLimit)
                $entries.Add($entry.FullName, $entry)
            }
            Assert-MayaTransfer ($entries.ContainsKey('kit-manifest.json') -and $entries['kit-manifest.json'].Length -le 1MB)
            $memory = [IO.MemoryStream]::new()
            $inputStream = $entries['kit-manifest.json'].Open()
            try {
                Copy-MayaBoundedStream $inputStream $memory $entries['kit-manifest.json'].Length ([Threading.CancellationToken]::None)
                $memory.Position = 0
                Assert-MayaTransfer ((Get-MayaStreamHash $memory) -ceq $ExpectedManifestHash)
                $rawManifest = $memory.ToArray()
                $manifest = [Text.UTF8Encoding]::new($false, $true).GetString($rawManifest) | ConvertFrom-Json
            } finally { $inputStream.Dispose(); $memory.Dispose() }
            Assert-MayaTransfer ($manifest.schema -ceq 'maya.gatea_transfer.v1')
            foreach ($flag in @('execution_authorized', 'external_sharing_authorized', 'production_qualified')) {
                Assert-MayaTransfer ($manifest.$flag -is [bool] -and $manifest.$flag -eq $false)
            }
            $expected = @{}
            foreach ($row in $manifest.files) {
                Assert-MayaRelativeName $row.path
                Assert-MayaTransfer ($row.path -cne 'kit-manifest.json' -and -not $expected.ContainsKey($row.path))
                Assert-MayaTransfer ($row.sha256 -cmatch '^[0-9a-f]{64}$' -and $row.size_bytes -ge 0)
                Assert-MayaTransfer ($entries.ContainsKey($row.path) -and $entries[$row.path].FullName -ceq $row.path)
                Assert-MayaTransfer ($entries[$row.path].Length -eq $row.size_bytes)
                $expected.Add($row.path, $row)
                $inputStream = $entries[$row.path].Open()
                try { Assert-MayaTransfer ((Get-MayaStreamHash $inputStream) -ceq $row.sha256) }
                finally { $inputStream.Dispose() }
            }
            Assert-MayaTransfer ($expected.Count + 1 -eq $entries.Count)
            $empty = @($manifest.empty_directories)
            Assert-MayaTransfer ($empty.Count -eq $script:MayaEmptyDirectories.Count)
            foreach ($name in $script:MayaEmptyDirectories) {
                Assert-MayaTransfer (@($empty | Where-Object { $_ -ceq $name }).Count -eq 1)
                foreach ($entryName in $entries.Keys) {
                    Assert-MayaTransfer (-not $entryName.StartsWith($name + '/', [StringComparison]::OrdinalIgnoreCase) -and
                        -not $entryName.Equals($name, [StringComparison]::OrdinalIgnoreCase))
                }
            }
            # Validation is complete before the destination is created. Failure retains partial evidence.
            [void][IO.Directory]::CreateDirectory($Destination)
            foreach ($entry in $zip.Entries) {
                $target = [IO.Path]::GetFullPath([IO.Path]::Combine($Destination, $entry.FullName.Replace('/', '\')))
                Assert-MayaTransfer ($target.StartsWith([IO.Path]::GetFullPath($Destination).TrimEnd('\') + '\',
                    [StringComparison]::OrdinalIgnoreCase))
                Assert-MayaPlainPath $target
                [void][IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($target))
                $output = [IO.File]::Open($target, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write, [IO.FileShare]::None)
                $inputStream = $entry.Open()
                try {
                    Copy-MayaBoundedStream $inputStream $output $entry.Length ([Threading.CancellationToken]::None)
                    $output.Flush($true)
                } finally { $inputStream.Dispose(); $output.Dispose() }
                $hash = if ($entry.FullName -ceq 'kit-manifest.json') { $ExpectedManifestHash } else { $expected[$entry.FullName].sha256 }
                Assert-MayaTransfer ((Get-MayaFileHash $target) -ceq $hash)
            }
            foreach ($name in $empty) {
                $target = Join-Path $Destination $name
                Assert-MayaPlainPath $target
                [void][IO.Directory]::CreateDirectory($target)
            }
        } finally { $zip.Dispose() }
    } finally { $file.Dispose() }
}

function Invoke-MayaKitDownload {
    param([string]$ArchiveHash, [string]$ManifestHash, [bool]$Permission)
    $handler = $client = $response = $request = $cancellation = $output = $secure = $null
    $pointer = [IntPtr]::Zero
    try {
        Assert-MayaTransfer ($Permission -and -not [Console]::IsInputRedirected)
        Assert-MayaTransfer ($ArchiveHash -cmatch '^[0-9a-f]{64}$' -and $ManifestHash -cmatch '^[0-9a-f]{64}$')
        Assert-MayaTransfer ($env:OS -ceq 'Windows_NT' -and [Environment]::Is64BitProcess)
        foreach ($path in @('C:\MayaGateA', 'C:\MayaGateA.download')) {
            Assert-MayaPlainPath $path
            Assert-MayaTransfer (-not (Test-Path -LiteralPath $path))
        }
        $answer = Read-Host ('Type AUTHORIZE TRANSFER ' + $ArchiveHash)
        Assert-MayaTransfer ($answer -ceq ('AUTHORIZE TRANSFER ' + $ArchiveHash))
        $secure = Read-Host 'Paste only the 30-minute read-only user-delegation SAS token (masked)' -AsSecureString
        $pointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
        $uri = Get-MayaSasUri ([Runtime.InteropServices.Marshal]::PtrToStringBSTR($pointer)) ([DateTimeOffset]::UtcNow)
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($pointer)
        $pointer = [IntPtr]::Zero
        $handler = New-MayaHttpHandler
        $client = [Net.Http.HttpClient]::new($handler)
        $cancellation = [Threading.CancellationTokenSource]::new(120000)
        $request = [Net.Http.HttpRequestMessage]::new([Net.Http.HttpMethod]::Get, $uri)
        $response = $client.SendAsync($request, [Net.Http.HttpCompletionOption]::ResponseHeadersRead,
            $cancellation.Token).GetAwaiter().GetResult()
        $output = [IO.File]::Open('C:\MayaGateA.download', [IO.FileMode]::CreateNew, [IO.FileAccess]::Write, [IO.FileShare]::None)
        Receive-MayaResponse $response $uri $output $cancellation.Token
        $output.Flush($true)
        $output.Dispose()
        $output = $null
        Expand-MayaKit 'C:\MayaGateA.download' 'C:\MayaGateA' $ArchiveHash $ManifestHash
        return '{"status":"downloaded_and_verified_not_executed","execution_authorized":false,"production_qualified":false}'
    } catch {
        # Never print HTTP exceptions, URLs, tokens or untrusted archive names.
        return '{"status":"blocked","reason_code":"transfer.failed","execution_authorized":false,"production_qualified":false}'
    } finally {
        if ($pointer -ne [IntPtr]::Zero) { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($pointer) }
        foreach ($item in @($output, $response, $request, $client, $handler, $cancellation, $secure)) {
            if ($null -ne $item) { $item.Dispose() }
        }
    }
}

Add-Type -AssemblyName System.Net.Http
Add-Type -AssemblyName System.IO.Compression
if ($MyInvocation.InvocationName -ne '.') {
    $result = Invoke-MayaKitDownload $ArchiveSha256 $ManifestSha256 ([bool]$PermitDownload)
    Write-Output $result
    if ($result -match '"status":"blocked"') { exit 1 }
}
