[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$c = Get-Content uzkost.html -Raw -Encoding UTF8
# Get bytes of key substring
$idx = $c.IndexOf('v nosn')
if ($idx -ge 0) {
    $sub = $c.Substring($idx, 15)
    Write-Host "Found substring: $sub"
    $bytes = [System.Text.Encoding]::UTF8.GetBytes($sub)
    Write-Host "Bytes: $($bytes -join ' ')"
} else {
    Write-Host "Not found with IndexOf"
}

# Try matching with regex
$m = [regex]::Match($c, 'v nosn.m oleji')
Write-Host "Regex match 'v nosn.m oleji': $($m.Success) -> $($m.Value)"
