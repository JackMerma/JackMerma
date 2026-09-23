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
        "series": ["#7fd8a0", "#64c9b0", "#9ad97a", "#4fae87", "#b7e3a8", "#3f8f7a", "#a8dfd0", "#6f9f5f"],
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
        "series": ["#2f8f5b", "#2b8b84", "#5a9e3a", "#217a5f", "#79b06a", "#1c6b63", "#4f9e8c", "#557f3e"],
    },
}
