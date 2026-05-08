$jojoba = '(např. <a href="https://bewit.love/produkt/bio-jojoba-oil?i=3fqlzp0xrllj7" target="_blank" rel="noopener">jojobový</a>)'

Get-ChildItem '*.html' | ForEach-Object {
    $content = Get-Content $_.FullName -Raw -Encoding UTF8
    $newContent = [regex]::Replace(
        $content,
        '(<p class="produkt-jak">.*?</p>)',
        {
            param($m)
            $m.Value -replace 'v nosném oleji', ('v nosném oleji ' + $jojoba)
        },
        [System.Text.RegularExpressions.RegexOptions]::Singleline
    )
    if ($newContent -ne $content) {
        Set-Content $_.FullName $newContent -Encoding UTF8 -NoNewline
        Write-Host $_.Name
    }
}
Write-Host 'Hotovo'
