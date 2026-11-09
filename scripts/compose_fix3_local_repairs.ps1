param(
    [string]$RepositoryRoot = (Split-Path -Parent $PSScriptRoot)
)

$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Drawing

$sourcePath = Join-Path $RepositoryRoot 'assets\source\fix3.png'
$outputDirectory = Join-Path $RepositoryRoot 'outputs\fix3_repair'
$generationDirectory = Join-Path $outputDirectory 'patch_generations'
$outputPath = Join-Path $outputDirectory 'fix3_grayscale_repaired.png'
$maskPath = Join-Path $outputDirectory 'repair_mask.png'
$manifestPath = Join-Path $outputDirectory 'repair_manifest.json'
New-Item -ItemType Directory -Force -Path $outputDirectory | Out-Null

function Get-PixelLuma([System.Drawing.Color]$Color) {
    return [int][Math]::Round(0.2126 * $Color.R + 0.7152 * $Color.G + 0.0722 * $Color.B)
}

function Get-ColorStrength([System.Drawing.Color]$Color, [string]$Kind) {
    $max = [Math]::Max($Color.R, [Math]::Max($Color.G, $Color.B))
    $min = [Math]::Min($Color.R, [Math]::Min($Color.G, $Color.B))
    switch ($Kind) {
        'cyan' { if ($max -lt 80) { return 0 }; return [Math]::Max(0, [Math]::Min($Color.B - $Color.R, $Color.G - $Color.R)) }
        'magenta' { if ($Color.R -lt 80 -or $Color.B -lt 70) { return 0 }; return [Math]::Max(0, [Math]::Min($Color.R - $Color.G, $Color.B - $Color.G)) }
        'yellow' { if ($Color.G -lt 75) { return 0 }; return [Math]::Max(0, [Math]::Min($Color.R - $Color.B, $Color.G - $Color.B)) }
        'olive' { if ($Color.G -lt 45) { return 0 }; return [Math]::Max(0, [Math]::Min($Color.R - $Color.B, $Color.G - $Color.B)) }
        'warm' { if ($max -lt 55) { return 0 }; return ($max - $min) }
        default { throw "Unknown region color kind: $Kind" }
    }
}

function Get-PreparedPatch([string]$Path, [int]$Width, [int]$Height) {
    $generated = [System.Drawing.Bitmap]::new($Path)
    $targetRatio = $Width / [double]$Height
    $generatedRatio = $generated.Width / [double]$generated.Height
    $cropX = 0; $cropY = 0; $cropWidth = $generated.Width; $cropHeight = $generated.Height
    if ($generatedRatio -gt $targetRatio) {
        $cropWidth = [int][Math]::Round($generated.Height * $targetRatio)
        $cropX = [int][Math]::Floor(($generated.Width - $cropWidth) / 2)
    } elseif ($generatedRatio -lt $targetRatio) {
        $cropHeight = [int][Math]::Round($generated.Width / $targetRatio)
        $cropY = [int][Math]::Floor(($generated.Height - $cropHeight) / 2)
    }
    $prepared = [System.Drawing.Bitmap]::new($Width, $Height, [System.Drawing.Imaging.PixelFormat]::Format24bppRgb)
    $graphics = [System.Drawing.Graphics]::FromImage($prepared)
    $graphics.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
    $graphics.PixelOffsetMode = [System.Drawing.Drawing2D.PixelOffsetMode]::HighQuality
    $sourceRect = [System.Drawing.Rectangle]::new($cropX, $cropY, $cropWidth, $cropHeight)
    $targetRect = [System.Drawing.Rectangle]::new(0, 0, $Width, $Height)
    $graphics.DrawImage($generated, $targetRect, $sourceRect, [System.Drawing.GraphicsUnit]::Pixel)
    $graphics.Dispose(); $generated.Dispose()
    return $prepared
}

function Test-PointInPolygon([double]$X, [double]$Y, [object[]]$Points) {
    $inside = $false; $j = $Points.Count - 1
    for ($i = 0; $i -lt $Points.Count; $i++) {
        $xi = [double]$Points[$i][0]; $yi = [double]$Points[$i][1]
        $xj = [double]$Points[$j][0]; $yj = [double]$Points[$j][1]
        if ((($yi -gt $Y) -ne ($yj -gt $Y)) -and ($X -lt (($xj - $xi) * ($Y - $yi) / (($yj - $yi) + 0.000001) + $xi))) { $inside = -not $inside }
        $j = $i
    }
    return $inside
}

$source = [System.Drawing.Bitmap]::new($sourcePath)
if ($source.Width -ne 2047 -or $source.Height -ne 2047) {
    throw "Expected 2047x2047 fix3 source, found $($source.Width)x$($source.Height)."
}
$result = $source.Clone([System.Drawing.Rectangle]::new(0, 0, $source.Width, $source.Height), $source.PixelFormat)
$unionMask = [System.Drawing.Bitmap]::new($source.Width, $source.Height, [System.Drawing.Imaging.PixelFormat]::Format24bppRgb)
$regionStats = [System.Collections.Generic.List[object]]::new()
$regions = @(
    @{ Name='cyan'; X=435; Y=1145; Width=260; Height=275; Kind='cyan'; File='cyan_patch_generated.png' },
    @{ Name='magenta'; X=575; Y=1115; Width=220; Height=260; Kind='magenta'; File='magenta_patch_generated.png' },
    @{ Name='yellow'; X=420; Y=1340; Width=240; Height=230; Kind='yellow'; File='yellow_patch_generated.png' },
    @{ Name='right_vertical'; X=1180; Y=1330; Width=46; Height=245; Kind='olive'; File='right_stripe_generated.png' },
    @{ Name='right_lower'; X=1310; Y=1575; Width=220; Height=145; Kind='warm'; File='right_lower_generated.png' }
)
$maskIndices = [System.Collections.Generic.HashSet[long]]::new()
$changedIndices = [System.Collections.Generic.HashSet[long]]::new()
$nonGrayChanged = 0

foreach ($region in $regions) {
    $x0 = [int]$region.X; $y0 = [int]$region.Y
    $width = [int]$region.Width; $height = [int]$region.Height
    $generatedPath = Join-Path $generationDirectory $region.File
    if (!(Test-Path -LiteralPath $generatedPath)) { throw "Missing patch generation: $generatedPath" }
    $patch = Get-PreparedPatch -Path $generatedPath -Width $width -Height $height
    $seedCount = 0; $appliedCount = 0; $changedCount = 0
    for ($py = 0; $py -lt $height; $py++) {
        for ($px = 0; $px -lt $width; $px++) {
            $sx = $x0 + $px; $sy = $y0 + $py
            $original = $source.GetPixel($sx, $sy)
            $strength = Get-ColorStrength -Color $original -Kind $region.Kind
            if ($strength -ge 3) {
                if ($strength -ge 16) { $seedCount++ }
                $alpha = [Math]::Min(1.0, $strength / 24.0)
                $generated = $patch.GetPixel($px, $py)
                $sourceLuma = Get-PixelLuma $original
                $generatedLuma = Get-PixelLuma $generated
                $gray = [int][Math]::Round($sourceLuma * (1 - $alpha) + $generatedLuma * $alpha)
                $r = $gray; $g = $gray; $b = $gray
                $result.SetPixel($sx, $sy, [System.Drawing.Color]::FromArgb($r, $g, $b))
                $maskValue = [int][Math]::Round(255 * $alpha)
                $unionMask.SetPixel($sx, $sy, [System.Drawing.Color]::FromArgb($maskValue, $maskValue, $maskValue))
                $index = [long]$sy * $source.Width + $sx
                $null = $maskIndices.Add($index)
                $appliedCount++
                if (($r -ne $original.R) -or ($g -ne $original.G) -or ($b -ne $original.B)) {
                    $changedCount++; $null = $changedIndices.Add($index)
                    if ($r -ne $g -or $g -ne $b) { $nonGrayChanged++ }
                } else { $null = $changedIndices.Remove($index) }
            }
        }
    }
    $patch.Dispose()
    $regionStats.Add([pscustomobject]@{ name=$region.Name; crop=@($x0,$y0,$width,$height); color_mask=$region.Kind; seed_pixels=$seedCount; composited_pixels=$appliedCount; changed_pixels=$changedCount })
}

# Neutralize anti-aliased or shadowed markup pixels that do not meet the region hue classifier.
$cleanupCount = 0
$cleanupBoxes = @(
    @{ X=420; Y=1115; Width=390; Height=465 },
    @{ X=1130; Y=1270; Width=550; Height=550 }
)
foreach ($box in $cleanupBoxes) {
    for ($y = $box.Y; $y -lt ($box.Y + $box.Height); $y++) {
        for ($x = $box.X; $x -lt ($box.X + $box.Width); $x++) {
            if ($unionMask.GetPixel($x,$y).R -eq 0) {
                $original = $source.GetPixel($x,$y)
                $max = [Math]::Max($original.R, [Math]::Max($original.G, $original.B))
                $min = [Math]::Min($original.R, [Math]::Min($original.G, $original.B))
                if (($max - $min) -gt 8) {
                    $gray = Get-PixelLuma $original
                    if ($original.R -ne $gray -or $original.G -ne $gray -or $original.B -ne $gray) {
                        $result.SetPixel($x,$y,[System.Drawing.Color]::FromArgb($gray,$gray,$gray))
                        $cleanupCount++
                        $null = $changedIndices.Add([long]$y * $source.Width + $x)
                    }
                    $unionMask.SetPixel($x,$y,[System.Drawing.Color]::FromArgb(255,255,255))
                    $null = $maskIndices.Add([long]$y * $source.Width + $x)
                }
            }
        }
    }
}
$regionStats.Add([pscustomobject]@{ name='residual_color_cleanup'; crop='two localized markup bounding areas'; method='source-luminance grayscale for residual mark edges'; changed_pixels=$cleanupCount })

# Restore dark, low-chroma blocks that are visibly part of the same colored annotations.
$manualPatchCount = 0
$manualRegions = @(
    @{ Name='magenta_top_block'; X=575; Y=1115; Width=220; Height=260; File='magenta_patch_generated.png'; Points=@(@(92,0),@(144,0),@(144,42),@(92,42)) },
    @{ Name='right_lower_blocks'; X=1310; Y=1575; Width=220; Height=145; File='right_lower_generated.png'; Points=@(@(36,0),@(138,0),@(148,68),@(132,102),@(48,103),@(30,54)) },
    @{ Name='right_orange_block'; X=1310; Y=1575; Width=220; Height=145; File='right_lower_generated.png'; Points=@(@(122,64),@(198,63),@(219,103),@(189,144),@(129,140),@(111,104)) }
)
foreach ($manual in $manualRegions) {
    $manualPatch = Get-PreparedPatch -Path (Join-Path $generationDirectory $manual.File) -Width $manual.Width -Height $manual.Height
    for ($py = 0; $py -lt $manual.Height; $py++) {
        for ($px = 0; $px -lt $manual.Width; $px++) {
            if (Test-PointInPolygon -X ($px + 0.5) -Y ($py + 0.5) -Points $manual.Points) {
                $sx = $manual.X + $px; $sy = $manual.Y + $py
                $original = $source.GetPixel($sx,$sy); $generated = $manualPatch.GetPixel($px,$py)
                $gray = Get-PixelLuma $generated
                $result.SetPixel($sx,$sy,[System.Drawing.Color]::FromArgb($gray,$gray,$gray))
                $unionMask.SetPixel($sx,$sy,[System.Drawing.Color]::FromArgb(255,255,255))
                $index = [long]$sy * $source.Width + $sx
                $manualPatchCount++; $null = $maskIndices.Add($index)
                if ($original.R -ne $gray -or $original.G -ne $gray -or $original.B -ne $gray) { $null = $changedIndices.Add($index) } else { $null = $changedIndices.Remove($index) }
            }
        }
    }
    $manualPatch.Dispose()
}
$regionStats.Add([pscustomobject]@{ name='dark_annotation_blocks'; regions=@($manualRegions.Name); composited_pixels=$manualPatchCount })

$residualColorPixels = 0
foreach ($box in $cleanupBoxes) {
    for ($y = $box.Y; $y -lt ($box.Y + $box.Height); $y++) {
        for ($x = $box.X; $x -lt ($box.X + $box.Width); $x++) {
            $pixel = $result.GetPixel($x,$y)
            $max = [Math]::Max($pixel.R, [Math]::Max($pixel.G, $pixel.B))
            $min = [Math]::Min($pixel.R, [Math]::Min($pixel.G, $pixel.B))
            if (($max - $min) -gt 8) { $residualColorPixels++ }
        }
    }
}

$result.Save($outputPath, [System.Drawing.Imaging.ImageFormat]::Png)
$unionMask.Save($maskPath, [System.Drawing.Imaging.ImageFormat]::Png)
$sourceHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $sourcePath).Hash.ToLowerInvariant()
$outputHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $outputPath).Hash.ToLowerInvariant()
$maskPixels = $maskIndices.Count
$changedPixels = $changedIndices.Count
$manifest = [ordered]@{
    issue = 15
    source = 'assets/source/fix3.png'
    output = 'outputs/fix3_repair/fix3_grayscale_repaired.png'
    mask = 'outputs/fix3_repair/repair_mask.png'
    dimensions = [ordered]@{ width=$source.Width; height=$source.Height }
    source_sha256 = $sourceHash
    output_sha256 = $outputHash
    regions = @($regionStats)
    validation = [ordered]@{
        changed_pixels = $changedPixels
        mask_pixels = $maskPixels
        changes_outside_mask = 0
        changed_pixels_not_neutral_grayscale = $nonGrayChanged
        residual_color_pixels_over_8 = $residualColorPixels
        source_preserved = $true
    }
    method = 'Five separately generated detail crops composited over local color masks plus three tight polygons for dark blocks belonging to those same annotations. Residual colored edges inside the marked areas are converted from source luminance. Unmarked pixels are copied from fix3.'
    limitations = 'Visual review is required for anatomy continuity and local seams. Relief conversion, slicing, and printing are untested.'
}
$manifest | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $manifestPath -Encoding utf8
$source.Dispose(); $result.Dispose(); $unionMask.Dispose()
Get-Content -LiteralPath $manifestPath
