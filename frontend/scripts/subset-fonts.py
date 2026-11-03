"""Regenerate with: uv run --with 'fonttools[woff]==4.68.0' python scripts/subset-fonts.py"""

from pathlib import Path
from fontTools import subset
from fontTools.varLib.instancer import instantiateVariableFont

root = Path(__file__).resolve().parents[1]
destination = root / "src/app/fonts"
destination.mkdir(exist_ok=True)
sources = {
    "OpenRunde-Regular": "OpenRunde-Regular.3i5t8uahr2766.woff2",
    "OpenRunde-Medium": "OpenRunde-Medium.2h62s-mncjiz2.woff2",
    "OpenRunde-Semibold": "OpenRunde-Semibold.0ajyrq9sz83xf.woff2",
    "Exposure": "Exposure-205TF-VAR.1_3-0jqo3454y.woff2",
}

for name, source in sources.items():
    options = subset.Options()
    options.flavor = "woff2"
    font = subset.load_font(str(root / "public/poke" / source), options)
    # Keep Latin, currency (including ₹), punctuation and arrows. Other scripts
    # already use system fallbacks. Preserve both EXPO styles used by the UI.
    subsetter = subset.Subsetter(options=options)
    subsetter.populate(unicodes=subset.parse_unicodes(
        "U+0000-024F,U+2000-206F,U+20A0-20CF,U+2190-21FF,U+FEFF,U+FFFD"))
    subsetter.subset(font)
    if name == "Exposure":
        font = instantiateVariableFont(font, {"EXPO": (-10, 0)}, inplace=True)
    path = destination / f"{name}.woff2"
    subset.save_font(font, str(path), options)
    print(f"{path.name}: {path.stat().st_size:,} bytes")
