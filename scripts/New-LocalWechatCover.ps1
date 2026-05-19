param(
  [Parameter(Mandatory=$true)][string]$Output,
  [Parameter(Mandatory=$true)][string]$Title,
  [string]$Subtitle = "",
  [string]$Kicker = "Media Transfer",
  [ValidateSet("market","thinking","chip","default")][string]$Theme = "default"
)

$ErrorActionPreference = "Stop"
Add-Type -AssemblyName System.Drawing

function New-Font([string]$Name, [float]$Size, [System.Drawing.FontStyle]$Style) {
  return [System.Drawing.Font]::new($Name, $Size, $Style, [System.Drawing.GraphicsUnit]::Pixel)
}

$width = 2560
$height = 1440
$bitmap = [System.Drawing.Bitmap]::new($width, $height)
$graphics = [System.Drawing.Graphics]::FromImage($bitmap)
$graphics.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
$graphics.TextRenderingHint = [System.Drawing.Text.TextRenderingHint]::AntiAliasGridFit

if ($Theme -eq "market") {
  $start = [System.Drawing.Color]::FromArgb(16, 24, 39)
  $end = [System.Drawing.Color]::FromArgb(30, 64, 175)
  $accent = [System.Drawing.Color]::FromArgb(248, 180, 41)
} elseif ($Theme -eq "thinking") {
  $start = [System.Drawing.Color]::FromArgb(12, 53, 48)
  $end = [System.Drawing.Color]::FromArgb(20, 122, 105)
  $accent = [System.Drawing.Color]::FromArgb(255, 214, 102)
} elseif ($Theme -eq "chip") {
  $start = [System.Drawing.Color]::FromArgb(17, 24, 39)
  $end = [System.Drawing.Color]::FromArgb(88, 28, 135)
  $accent = [System.Drawing.Color]::FromArgb(86, 204, 242)
} else {
  $start = [System.Drawing.Color]::FromArgb(24, 24, 27)
  $end = [System.Drawing.Color]::FromArgb(51, 65, 85)
  $accent = [System.Drawing.Color]::FromArgb(125, 211, 252)
}

$rect = [System.Drawing.Rectangle]::new(0, 0, $width, $height)
$background = [System.Drawing.Drawing2D.LinearGradientBrush]::new($rect, $start, $end, 35)
$graphics.FillRectangle($background, $rect)
$background.Dispose()

$softPen = [System.Drawing.Pen]::new([System.Drawing.Color]::FromArgb(46, 255, 255, 255), 3)
for ($i = 0; $i -lt 11; $i++) {
  $x = 160 + ($i * 225)
  $graphics.DrawLine($softPen, $x, 160, $x + 420, 1280)
}
$softPen.Dispose()

$glow = [System.Drawing.SolidBrush]::new([System.Drawing.Color]::FromArgb(42, $accent.R, $accent.G, $accent.B))
for ($i = 0; $i -lt 7; $i++) {
  $size = 260 + ($i * 55)
  $x = 1450 + ($i * 90)
  $y = 190 + ($i * 110)
  $graphics.FillEllipse($glow, $x, $y, $size, $size)
}
$glow.Dispose()

$accentBrush = [System.Drawing.SolidBrush]::new($accent)
$whiteBrush = [System.Drawing.SolidBrush]::new([System.Drawing.Color]::White)
$mutedBrush = [System.Drawing.SolidBrush]::new([System.Drawing.Color]::FromArgb(218, 255, 255, 255))
$panelBrush = [System.Drawing.SolidBrush]::new([System.Drawing.Color]::FromArgb(76, 0, 0, 0))
$graphics.FillRectangle($panelBrush, 150, 190, 1220, 104)

$kickerFont = New-Font "Microsoft YaHei UI" 44 ([System.Drawing.FontStyle]::Bold)
$titleFont = New-Font "Microsoft YaHei UI" 116 ([System.Drawing.FontStyle]::Bold)
$subtitleFont = New-Font "Microsoft YaHei UI" 44 ([System.Drawing.FontStyle]::Regular)
$smallFont = New-Font "Segoe UI" 34 ([System.Drawing.FontStyle]::Bold)
$format = [System.Drawing.StringFormat]::new()
$format.Alignment = [System.Drawing.StringAlignment]::Near

$graphics.DrawString($Kicker, $kickerFont, $accentBrush, 190, 212)
$graphics.DrawString($Title, $titleFont, $whiteBrush, [System.Drawing.RectangleF]::new(180, 430, 1480, 360), $format)
$graphics.DrawString($Subtitle, $subtitleFont, $mutedBrush, [System.Drawing.RectangleF]::new(185, 840, 1360, 180), $format)

$linePen = [System.Drawing.Pen]::new($accent, 12)
$graphics.DrawLine($linePen, 190, 1085, 780, 1085)
$graphics.DrawString("SOCIAL MEDIA TRANSPHER", $smallFont, $mutedBrush, 188, 1135)

if ($Theme -eq "market") {
  $chartPen = [System.Drawing.Pen]::new($accent, 10)
  $points = [System.Drawing.Point[]]@(
    [System.Drawing.Point]::new(1530,1010),
    [System.Drawing.Point]::new(1680,890),
    [System.Drawing.Point]::new(1810,940),
    [System.Drawing.Point]::new(1960,690),
    [System.Drawing.Point]::new(2110,750),
    [System.Drawing.Point]::new(2330,470)
  )
  $graphics.DrawLines($chartPen, $points)
  foreach ($point in $points) {
    $graphics.FillEllipse($whiteBrush, $point.X - 14, $point.Y - 14, 28, 28)
  }
  $chartPen.Dispose()
} elseif ($Theme -eq "thinking") {
  $shapePen = [System.Drawing.Pen]::new($accent, 8)
  for ($i = 0; $i -lt 5; $i++) {
    $graphics.DrawEllipse($shapePen, 1620 + ($i * 68), 420 + ($i * 48), 420 - ($i * 32), 420 - ($i * 32))
  }
  $shapePen.Dispose()
} else {
  $shapePen = [System.Drawing.Pen]::new($accent, 8)
  for ($i = 0; $i -lt 8; $i++) {
    $graphics.DrawRectangle($shapePen, 1540 + ($i * 80), 420 + ($i * 52), 360, 210)
  }
  $shapePen.Dispose()
}

$directory = Split-Path -Parent $Output
if ($directory) {
  New-Item -ItemType Directory -Force -Path $directory | Out-Null
}

$encoder = [System.Drawing.Imaging.ImageCodecInfo]::GetImageEncoders() | Where-Object { $_.MimeType -eq "image/jpeg" }
$parameters = [System.Drawing.Imaging.EncoderParameters]::new(1)
$parameters.Param[0] = [System.Drawing.Imaging.EncoderParameter]::new([System.Drawing.Imaging.Encoder]::Quality, 92L)
$bitmap.Save($Output, $encoder, $parameters)

$parameters.Dispose()
$format.Dispose()
$kickerFont.Dispose()
$titleFont.Dispose()
$subtitleFont.Dispose()
$smallFont.Dispose()
$linePen.Dispose()
$accentBrush.Dispose()
$whiteBrush.Dispose()
$mutedBrush.Dispose()
$panelBrush.Dispose()
$graphics.Dispose()
$bitmap.Dispose()

Write-Output $Output

