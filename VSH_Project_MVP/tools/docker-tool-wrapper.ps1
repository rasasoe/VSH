param(
    [Parameter(Mandatory = $true)]
    [string]$Image,

    [Parameter(Mandatory = $false)]
    [string[]]$CommandPrefix = @(),

    [Parameter(Mandatory = $false)]
    [string[]]$ToolArgs
)

function Convert-WindowsPathToDockerPath {
    param([string]$Value)

    if ($Value -match '^[A-Za-z]:\\') {
        $drive = $Value.Substring(0, 1).ToLowerInvariant()
        $rest = $Value.Substring(2).Replace('\', '/')
        return "/mnt/$drive$rest"
    }

    return $Value
}

$rewrittenArgs = @()
foreach ($arg in ($ToolArgs | Where-Object { $_ -ne $null })) {
    $rewrittenArgs += (Convert-WindowsPathToDockerPath -Value $arg)
}

$dockerArgs = @(
    "run",
    "--rm",
    "-v", "a:\:/mnt/a",
    "-v", "c:\:/mnt/c",
    $Image
) + $CommandPrefix + $rewrittenArgs

& docker @dockerArgs
exit $LASTEXITCODE
