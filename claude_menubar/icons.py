"""Generate menu bar taxi icons programmatically."""
from pathlib import Path

from PIL import Image, ImageDraw

CACHE_DIR = Path.home() / ".claude-menubar"
_ICON_VERSION = 4


def _ensure_cache():
    CACHE_DIR.mkdir(parents=True, exist_ok=True)


def _icon_path(name: str) -> str:
    return str(CACHE_DIR / f"{name}_v{_ICON_VERSION}.png")


def generate_icons() -> tuple[str, str]:
    """Generate idle and active taxi icons. Returns (idle_path, active_path)."""
    _ensure_cache()

    idle_path = _icon_path("taxi_idle")
    active_path = _icon_path("taxi_active")

    if not Path(idle_path).exists():
        _make_taxi(idle_path, light_on=False)
    if not Path(active_path).exists():
        _make_taxi(active_path, light_on=True)

    return idle_path, active_path


def _make_taxi(path: str, light_on: bool):
    """Draw a wider 36x22 yellow taxi with checker stripe.

    Saved at 2x for retina displays.
    """
    w, h = 36, 22
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Colors
    yellow = (255, 204, 0, 255)          # classic taxi yellow
    yellow_dark = (220, 175, 0, 255)     # slightly darker for depth
    window_color = (70, 130, 180, 220)   # steel blue tinted glass
    wheel_color = (40, 40, 40, 255)
    wheel_hub = (100, 100, 100, 255)
    bumper_color = (80, 80, 80, 255)
    checker_black = (30, 30, 30, 255)
    checker_white = (240, 240, 240, 255)
    light_off = (120, 100, 40, 200)
    light_on_color = (255, 220, 60, 255)
    light_glow = (255, 230, 80, 100)
    outline = (180, 150, 0, 255)

    # === Main body (lower) ===
    draw.rounded_rectangle([(2, 10), (33, 18)], radius=3, fill=yellow)
    # Subtle outline
    draw.rounded_rectangle([(2, 10), (33, 18)], radius=3, outline=outline)

    # === Cabin/roof (upper) ===
    # Trapezoidal cabin - use polygon for the sloped windshields
    cabin_pts = [
        (9, 10),   # bottom-left
        (11, 5),   # top-left (sloped windshield)
        (25, 5),   # top-right (sloped rear window)
        (27, 10),  # bottom-right
    ]
    draw.polygon(cabin_pts, fill=yellow_dark)
    draw.polygon(cabin_pts, outline=outline)

    # === Windows ===
    # Front windshield (sloped)
    draw.polygon([(10, 9), (12, 6), (15, 6), (15, 9)], fill=window_color)
    # Rear window (sloped)
    draw.polygon([(21, 9), (21, 6), (24, 6), (26, 9)], fill=window_color)
    # Middle window
    draw.rectangle([(16, 6), (20, 9)], fill=window_color)

    # === Checker stripe ===
    # Row of alternating black/white squares along the door area
    checker_y = 13
    checker_size = 2
    for i in range(10):
        x = 7 + i * checker_size
        if x + checker_size > 30:
            break
        color = checker_black if i % 2 == 0 else checker_white
        draw.rectangle(
            [(x, checker_y), (x + checker_size - 1, checker_y + checker_size - 1)],
            fill=color,
        )

    # === Bumpers ===
    draw.rectangle([(1, 14), (3, 17)], fill=bumper_color)
    draw.rectangle([(32, 14), (34, 17)], fill=bumper_color)

    # === Headlight / taillight ===
    draw.rectangle([(33, 12), (34, 13)], fill=(255, 255, 200, 255))  # headlight
    draw.rectangle([(1, 12), (2, 13)], fill=(255, 60, 60, 255))      # taillight

    # === Wheels ===
    draw.ellipse([(5, 16), (10, 21)], fill=wheel_color)
    draw.ellipse([(6, 17), (9, 20)], fill=wheel_hub)
    draw.ellipse([(25, 16), (30, 21)], fill=wheel_color)
    draw.ellipse([(26, 17), (29, 20)], fill=wheel_hub)

    # === Roof light ===
    if light_on:
        # Glow
        draw.ellipse([(15, 0), (22, 6)], fill=light_glow)
        # Light body
        draw.rounded_rectangle([(16, 1), (21, 5)], radius=2, fill=light_on_color)
        draw.rounded_rectangle([(16, 1), (21, 5)], radius=2, outline=(200, 170, 0, 255))
    else:
        draw.rounded_rectangle([(16, 2), (21, 5)], radius=2, fill=light_off)

    # Scale down 20%, then save at 2x for retina
    out_w, out_h = round(w * 0.8), round(h * 0.8)  # 29x18
    img_retina = img.resize((out_w * 2, out_h * 2), Image.LANCZOS)
    img_retina.save(path, "PNG")
