param(
    [string[]]$SkillPaths = @((Join-Path $PSScriptRoot '..\onsite-audit-https')),
    [string]$UserRoot = [Environment]::GetFolderPath('UserProfile')
)
$ErrorActionPreference = 'Stop'
# Single source in Git; Windows junctions make updates visible to each client.
# Cursor reads .agents/skills and .claude/skills; no third physical copy.
$roots = @((Join-Path $UserRoot '.agents\skills'), (Join-Path $UserRoot '.claude\skills'))
foreach ($skillPath in $SkillPaths) {
    $source = (Resolve-Path -LiteralPath $skillPath).Path
    $manifest = Join-Path $source 'SKILL.md'
    if (!(Test-Path -LiteralPath $manifest -PathType Leaf)) { throw "Missing SKILL.md: $source" }
    $name = Split-Path $source -Leaf
    if ($name -notmatch '^[a-z0-9][a-z0-9-]{0,63}$') { throw "Invalid skill folder: $name" }
    foreach ($root in $roots) {
        New-Item -ItemType Directory -Path $root -Force | Out-Null
        $destination = Join-Path $root $name
        if (Test-Path -LiteralPath $destination) {
            $item = Get-Item -LiteralPath $destination -Force
            if ($item.LinkType -eq 'Junction' -and @($item.Target)[0] -eq $source) {
                Write-Output "Already linked: $destination"
                continue
            }
            throw "Existing skill preserved: $destination. Resolve this conflict manually."
        }
        New-Item -ItemType Junction -Path $destination -Target $source | Out-Null
        if ((Get-FileHash -LiteralPath (Join-Path $destination 'SKILL.md')).Hash -ne (Get-FileHash -LiteralPath $manifest).Hash) { throw "Link verification failed: $destination" }
        Write-Output "Linked: $destination"
    }
}
