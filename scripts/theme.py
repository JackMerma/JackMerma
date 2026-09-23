"""Single source of truth for the palette used by every generated SVG."""

THEMES = ("dark", "light")

PALETTES = {
    "dark": {
        "bg": "#0d1117",
        "panel": "#0c1512",
        "border": "#1d2b24",
        "grid": "#1a2721",
        "dim": "#2f4438",
        "text": "#c6d4cd",
        "muted": "#7d8f87",
        "accent": "#7fd8a0",
        "accent_ink": "#08110d",
        "fill_opacity": "0.24",
    },
    "light": {
        "bg": "#ffffff",
        "panel": "#f6faf7",
        "border": "#d3e0d8",
        "grid": "#dde8e1",
        "dim": "#a9bdb2",
        "text": "#1f2a24",
        "muted": "#5b6b63",
        "accent": "#2f8f5b",
        "accent_ink": "#ffffff",
        "fill_opacity": "0.18",
    },
}
