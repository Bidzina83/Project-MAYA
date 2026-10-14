# Test-only OS compatibility experiment; never called by product setup.
param(
    [Parameter(Mandatory=$true)]
    [ValidateSet('Grant', 'Restore', 'VerifyRestored')]
    [string]$Operation,
    [switch]$ConsentTestRegistryChange
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$stage = Join-Path $root '.codex-build\governance-v2-lpac-stage'
$helper = Join-Path $root '.codex-build\governance-v2-native-tools\GateANative.exe'
$snapshotPath = Join-Path $stage 'host\sidebyside-acl-experiment.json'
$resultPath = Join-Path $stage ('host\sidebyside-' + $Operation + '-result.json')
$keyName = 'SOFTWARE\Microsoft\Windows\CurrentVersion\SideBySide'
$helperHash = 'E72F101BEA8222D14E908C2F39E7FECDCA122B2F13B2ABE9D5293490B7856F63'
$sections = [Security.AccessControl.AccessControlSections]::Access -bor
    [Security.AccessControl.AccessControlSections]::Owner -bor
    [Security.AccessControl.AccessControlSections]::Group
$hive = $null
$key = $null
$phase = 'validation'

function Report($value) {
    $json = $value | ConvertTo-Json -Depth 5 -Compress
    [IO.File]::WriteAllText($resultPath, $json, [Text.UTF8Encoding]::new($false))
    Write-Output $json
}

try {
    Set-Location -LiteralPath $root
    if ((Get-FileHash -LiteralPath $helper -Algorithm SHA256).Hash -ne $helperHash) {
        throw 'sidebyside.helper_changed'
    }
    # The unchanged helper verifies the exact workspace and rejects reparse ancestors.
    $plan = (& $helper plan $stage 18765) | ConvertFrom-Json
    if ($LASTEXITCODE -ne 0 -or $plan.status -ne 'plan_only') {
        throw 'sidebyside.invalid_profile'
    }
    $sid = [Security.Principal.SecurityIdentifier]::new([string]$plan.sid)
    if ($Operation -ne 'VerifyRestored' -and -not $ConsentTestRegistryChange) {
        throw 'sidebyside.consent_required'
    }
    $rights = [Security.AccessControl.RegistryRights]::ReadKey
    if ($Operation -ne 'VerifyRestored') {
        $rights = $rights -bor [Security.AccessControl.RegistryRights]::ChangePermissions
    }
    $hive = [Microsoft.Win32.RegistryKey]::OpenBaseKey(
        [Microsoft.Win32.RegistryHive]::LocalMachine, [Microsoft.Win32.RegistryView]::Registry64)
    $mode = [Microsoft.Win32.RegistryKeyPermissionCheck]::ReadSubTree
    if ($Operation -ne 'VerifyRestored') {
        # .NET's writable-handle mode is separate from the narrow OS rights mask.
        # The host requests only ReadKey/ChangePermissions, never value-write rights.
        $mode = [Microsoft.Win32.RegistryKeyPermissionCheck]::ReadWriteSubTree
    }
    $key = $hive.OpenSubKey($keyName, $mode, $rights)
    if ($null -eq $key) { throw 'sidebyside.key_missing' }
    Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
public static class MayaSideBySideSecurity {
    [DllImport("advapi32.dll")]
    public static extern int RegSetKeySecurity(IntPtr key, uint information, byte[] descriptor);
}
'@
    $security = $key.GetAccessControl($sections)
    $current = $security.GetSecurityDescriptorSddlForm($sections)

    if ($Operation -eq 'Grant') {
        $phase = 'snapshot'
        $existing = @($security.GetAccessRules($true, $true,
            [Security.Principal.SecurityIdentifier]) | Where-Object {$_.IdentityReference -eq $sid})
        if ($existing.Count -ne 0) { throw 'sidebyside.preexisting_grant' }
        $beforeBinary = [Convert]::ToBase64String($security.GetSecurityDescriptorBinaryForm())
        $rule = [Security.AccessControl.RegistryAccessRule]::new($sid,
            [Security.AccessControl.RegistryRights]::ReadKey,
            [Security.AccessControl.InheritanceFlags]::None,
            [Security.AccessControl.PropagationFlags]::None,
            [Security.AccessControl.AccessControlType]::Allow)
        $security.AddAccessRule($rule)
        $during = $security.GetSecurityDescriptorSddlForm($sections)
        $snapshot = @{schema='maya.gate_a.sidebyside.v1'; key=$keyName; view='Registry64';
            sid=$sid.Value; helper_sha256=$helperHash; before_sddl=$current;
            before_binary=$beforeBinary; during_sddl=$during; production_qualified=$false}
        $bytes = [Text.UTF8Encoding]::new($false).GetBytes(($snapshot | ConvertTo-Json -Depth 5))
        # Never overwrite the rollback snapshot; persist it before changing the OS DACL.
        if (Test-Path -LiteralPath $snapshotPath) {
            # Retry a failed pre-mutation attempt only against identical originals.
            # Never replace rollback evidence or adopt an unexpected descriptor.
            $saved = [IO.File]::ReadAllText($snapshotPath) | ConvertFrom-Json
            if ($saved.schema -ne $snapshot.schema -or $saved.key -ne $keyName -or
                $saved.view -ne 'Registry64' -or $saved.sid -ne $sid.Value -or
                $saved.helper_sha256 -ne $helperHash -or $saved.before_sddl -ne $current -or
                $saved.before_binary -ne $beforeBinary -or $saved.during_sddl -ne $during) {
                throw 'sidebyside.snapshot_mismatch'
            }
        } else {
            $stream = [IO.FileStream]::new($snapshotPath, [IO.FileMode]::CreateNew,
                [IO.FileAccess]::Write, [IO.FileShare]::None)
            try { $stream.Write($bytes, 0, $bytes.Length); $stream.Flush($true) }
            finally { $stream.Dispose() }
        }
        $phase = 'grant'
        if ($key.GetAccessControl($sections).GetSecurityDescriptorSddlForm($sections) -ne $current) {
            throw 'sidebyside.descriptor_drift'
        }
        $status = [MayaSideBySideSecurity]::RegSetKeySecurity($key.Handle.DangerousGetHandle(),
            4, $security.GetSecurityDescriptorBinaryForm())
        if ($status -ne 0) { throw 'sidebyside.native_grant_failed' }
        if ($key.GetAccessControl($sections).GetSecurityDescriptorSddlForm($sections) -ne $during) {
            throw 'sidebyside.grant_readback_failed'
        }
        Report @{status='temporary_grant_verified'; sid=$sid.Value; rights='ReadKey';
            inheritance='None'; production_qualified=$false}
    } else {
        $phase = 'restore_validation'
        $snapshot = [IO.File]::ReadAllText($snapshotPath) | ConvertFrom-Json
        if ($snapshot.schema -ne 'maya.gate_a.sidebyside.v1' -or $snapshot.key -ne $keyName -or
            $snapshot.view -ne 'Registry64' -or $snapshot.sid -ne $sid.Value -or
            $snapshot.helper_sha256 -ne $helperHash) { throw 'sidebyside.invalid_snapshot' }
        if ($current -ne $snapshot.before_sddl) {
            # The initial .NET attempt added only the documented auto-inherited
            # control bit. Recognize that exact descriptor solely for rollback.
            $normalized = [Security.AccessControl.RawSecurityDescriptor]::new($snapshot.during_sddl)
            $normalized.SetFlags($normalized.ControlFlags -bor
                [Security.AccessControl.ControlFlags]::DiscretionaryAclAutoInherited)
            $normalizedSddl = $normalized.GetSddlForm($sections)
            if ($Operation -eq 'VerifyRestored' -or
                ($current -ne $snapshot.during_sddl -and $current -ne $normalizedSddl)) {
                throw 'sidebyside.descriptor_drift_restore_blocked'
            }
            $phase = 'restore'
            # Only DACL is changed. Owner, group and SACL are never written.
            $status = [MayaSideBySideSecurity]::RegSetKeySecurity($key.Handle.DangerousGetHandle(),
                4, [Convert]::FromBase64String($snapshot.before_binary))
            if ($status -ne 0) { throw 'sidebyside.native_restore_failed' }
        }
        $restored = $key.GetAccessControl($sections)
        if ($restored.GetSecurityDescriptorSddlForm($sections) -ne $snapshot.before_sddl -or
            [Convert]::ToBase64String($restored.GetSecurityDescriptorBinaryForm()) -ne $snapshot.before_binary) {
            throw 'sidebyside.exact_restore_failed'
        }
        Report @{status='original_descriptor_verified'; descriptor_exact=$true;
            descriptor_sections='owner/group/DACL'; sacl_written=$false; production_qualified=$false}
    }
} catch {
    $errorObject = $_.Exception
    while ($null -ne $errorObject.InnerException) { $errorObject = $errorObject.InnerException }
    $code = 'sidebyside.experiment_failed'
    if ($errorObject.Message -match '^sidebyside\.[a-z_]+$') { $code = $errorObject.Message }
    Report @{status='blocked'; reason_code=$code; phase=$phase;
        hresult=$errorObject.HResult; production_qualified=$false}
    exit 1
} finally {
    if ($null -ne $key) { $key.Dispose() }
    if ($null -ne $hive) { $hive.Dispose() }
}
