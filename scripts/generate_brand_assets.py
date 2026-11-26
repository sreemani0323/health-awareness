"""
HealthAware Brand Asset Generator
Generates unified, pixel-perfect brand icons for:
- Web Tab Favicons: favicon.svg, favicon.ico (multi-size: 16, 24, 32, 48, 64, 128, 256), apple-touch-icon.png
- Web Brand Logo: logo.svg
- Android App Icons:
    - mipmap-mdpi (48px, round 48px, fg 108px)
    - mipmap-hdpi (72px, round 72px, fg 162px)
    - mipmap-xhdpi (96px, round 96px, fg 216px)
    - mipmap-xxhdpi (144px, round 144px, fg 324px)
    - mipmap-xxxhdpi (192px, round 192px, fg 432px)
    - Adaptive icon vector XMLs for Android API 26+
"""

import os
import math
from PIL import Image, ImageDraw, ImageFilter

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SCRIPT_DIR)
PUBLIC_DIR = os.path.join(BASE_DIR, "frontend", "public")
ANDROID_RES = os.path.join(BASE_DIR, "frontend", "android", "app", "src", "main", "res")

# 1. Master SVG Definitions
SVG_SQUIRCLE = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="512" height="512">
  <defs>
    <linearGradient id="haBg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#00897B"/>
      <stop offset="45%" stop-color="#00645C"/>
      <stop offset="100%" stop-color="#00423B"/>
    </linearGradient>
    <linearGradient id="heartGrad" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#00796B"/>
      <stop offset="100%" stop-color="#00443D"/>
    </linearGradient>
    <filter id="crossShadow" x="-20%" y="-20%" width="140%" height="140%">
      <feDropShadow dx="0" dy="8" stdDeviation="10" flood-color="#002823" flood-opacity="0.38"/>
    </filter>
  </defs>

  <!-- Squircle Base with Deep Teal Brand Gradient -->
  <rect x="16" y="16" width="480" height="480" rx="116" fill="url(#haBg)"/>
  <rect x="18" y="18" width="476" height="476" rx="114" fill="none" stroke="#FFFFFF" stroke-opacity="0.22" stroke-width="4"/>

  <!-- Medical Cross with Depth Shadow -->
  <g filter="url(#crossShadow)">
    <rect x="204" y="98" width="104" height="316" rx="34" fill="#FFFFFF"/>
    <rect x="98" y="204" width="316" height="104" rx="34" fill="#FFFFFF"/>
  </g>

  <!-- Centered Anatomical Heart Motif -->
  <path d="M 256,218 
           C 246,190 216,180 194,197 
           C 168,218 172,252 200,280 
           L 256,334 
           L 312,280 
           C 340,252 344,218 318,197 
           C 296,180 266,190 256,218 Z" 
        fill="url(#heartGrad)"/>

  <!-- Vital Pulse / ECG Lifeline -->
  <path d="M 194,256 L 224,256 L 236,236 L 254,280 L 268,242 L 278,256 L 318,256" 
        stroke="#E0F2F1" stroke-width="7" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
</svg>'''

SVG_ROUND = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="512" height="512">
  <defs>
    <linearGradient id="haBgR" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#00897B"/>
      <stop offset="45%" stop-color="#00645C"/>
      <stop offset="100%" stop-color="#00423B"/>
    </linearGradient>
    <linearGradient id="heartGradR" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#00796B"/>
      <stop offset="100%" stop-color="#00443D"/>
    </linearGradient>
    <filter id="crossShadowR" x="-20%" y="-20%" width="140%" height="140%">
      <feDropShadow dx="0" dy="8" stdDeviation="10" flood-color="#002823" flood-opacity="0.38"/>
    </filter>
  </defs>

  <!-- Circular Base with Deep Teal Brand Gradient -->
  <circle cx="256" cy="256" r="240" fill="url(#haBgR)"/>
  <circle cx="256" cy="256" r="238" fill="none" stroke="#FFFFFF" stroke-opacity="0.22" stroke-width="4"/>

  <!-- Medical Cross with Depth Shadow -->
  <g filter="url(#crossShadowR)">
    <rect x="204" y="98" width="104" height="316" rx="34" fill="#FFFFFF"/>
    <rect x="98" y="204" width="316" height="104" rx="34" fill="#FFFFFF"/>
  </g>

  <!-- Centered Heart Motif -->
  <path d="M 256,218 
           C 246,190 216,180 194,197 
           C 168,218 172,252 200,280 
           L 256,334 
           L 312,280 
           C 340,252 344,218 318,197 
           C 296,180 266,190 256,218 Z" 
        fill="url(#heartGradR)"/>

  <!-- Vital Pulse Line -->
  <path d="M 194,256 L 224,256 L 236,236 L 254,280 L 268,242 L 278,256 L 318,256" 
        stroke="#E0F2F1" stroke-width="7" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
</svg>'''

SVG_FOREGROUND_ANDROID = '''<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="108dp"
    android:height="108dp"
    android:viewportWidth="108"
    android:viewportHeight="108">
    <!-- Safe zone 72x72dp centered at (54, 54) -->
    <!-- Medical Cross in pure white -->
    <path
        android:fillColor="#FFFFFF"
        android:pathData="M50,26 h8 a4,4 0 0 1 4,4 v48 a4,4 0 0 1 -4,4 h-8 a4,4 0 0 1 -4,-4 v-48 a4,4 0 0 1 4,-4 z" />
    <path
        android:fillColor="#FFFFFF"
        android:pathData="M26,50 h48 a4,4 0 0 1 4,4 v8 a4,4 0 0 1 -4,4 h-48 a4,4 0 0 1 -4,-4 v-8 a4,4 0 0 1 4,-4 z" />
    <!-- Center Heart in Deep Teal #00645C -->
    <path
        android:fillColor="#00645C"
        android:pathData="M54,48 C52,43 46,41 42,44 C38,48 39,53 44,59 L54,69 L64,59 C69,53 70,48 66,44 C62,41 56,43 54,48 Z" />
    <!-- Pulse Line in Mint -->
    <path
        android:strokeColor="#E0F2F1"
        android:strokeWidth="1.4"
        android:strokeLineCap="round"
        android:strokeLineJoin="round"
        android:pathData="M43,54 L48,54 L50,51 L53,58 L56,52 L58,54 L65,54" />
</vector>'''


def render_master_icon(size=1024, round_shape=False, for_android_fg=False):
    """
    Renders high-resolution raster icon using Pillow supersampling at 2048x2048.
    Ensures crystal clear Lanczos downsampling to any target resolution.
    """
    canvas_dim = 2048
    scale = canvas_dim / 512.0
    c = canvas_dim / 2.0

    img = Image.new("RGBA", (canvas_dim, canvas_dim), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    if not for_android_fg:
        pad = int(16 * scale)
        # Background gradient
        bg = Image.new("RGBA", (canvas_dim, canvas_dim), (0, 0, 0, 0))
        bg_draw = ImageDraw.Draw(bg)

        # Teal gradient: #00897B (top) to #00423B (bottom)
        for y in range(canvas_dim):
            t = y / float(canvas_dim)
            r = int(0 * (1 - t) + 0 * t)
            g = int(137 * (1 - t) + 66 * t)
            b = int(123 * (1 - t) + 59 * t)
            bg_draw.line([(0, y), (canvas_dim, y)], fill=(r, g, b, 255))

        mask = Image.new("L", (canvas_dim, canvas_dim), 0)
        mask_draw = ImageDraw.Draw(mask)
        if round_shape:
            mask_draw.ellipse([pad, pad, canvas_dim - pad, canvas_dim - pad], fill=255)
        else:
            rx = int(116 * scale)
            mask_draw.rounded_rectangle([pad, pad, canvas_dim - pad, canvas_dim - pad], radius=rx, fill=255)

        img.paste(bg, (0, 0), mask)

        # Highlight ring
        highlight_color = (255, 255, 255, 55)
        rim_w = int(4 * scale)
        if round_shape:
            draw.ellipse([pad + rim_w, pad + rim_w, canvas_dim - pad - rim_w, canvas_dim - pad - rim_w],
                         outline=highlight_color, width=rim_w)
        else:
            rx = int(114 * scale)
            draw.rounded_rectangle([pad + rim_w, pad + rim_w, canvas_dim - pad - rim_w, canvas_dim - pad - rim_w],
                                   radius=rx, outline=highlight_color, width=rim_w)

    # Cross dimensions
    factor = 0.54 if for_android_fg else 0.62
    cross_span = int(512 * factor * scale)
    arm_w = int(cross_span * 0.33)
    arm_r = int(arm_w * 0.34)

    half_span = cross_span // 2
    half_w = arm_w // 2

    # Draw shadow if not foreground
    if not for_android_fg:
        shadow = Image.new("RGBA", (canvas_dim, canvas_dim), (0, 0, 0, 0))
        s_draw = ImageDraw.Draw(shadow)
        s_off = int(10 * scale)
        s_color = (0, 36, 31, 100)
        # Vertical arm shadow
        s_draw.rounded_rectangle([c - half_w, c - half_span + s_off, c + half_w, c + half_span + s_off],
                                 radius=arm_r, fill=s_color)
        # Horizontal arm shadow
        s_draw.rounded_rectangle([c - half_span, c - half_w + s_off, c + half_span, c + half_w + s_off],
                                 radius=arm_r, fill=s_color)
        shadow = shadow.filter(ImageFilter.GaussianBlur(radius=int(12 * scale)))
        img = Image.alpha_composite(img, shadow)

    # Cross layer
    cross_layer = Image.new("RGBA", (canvas_dim, canvas_dim), (0, 0, 0, 0))
    cd = ImageDraw.Draw(cross_layer)

    # White arms
    cd.rounded_rectangle([c - half_w, c - half_span, c + half_w, c + half_span],
                         radius=arm_r, fill=(255, 255, 255, 255))
    cd.rounded_rectangle([c - half_span, c - half_w, c + half_span, c + half_w],
                         radius=arm_r, fill=(255, 255, 255, 255))

    # Heart in center
    heart_scale = (arm_w * 0.44) / 16.0
    heart_points = []
    heart_cy = c - (4 * scale)
    for deg in range(0, 360, 2):
        t = math.radians(deg)
        x = 16 * (math.sin(t) ** 3)
        y = -(13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t))
        px = c + x * heart_scale
        py = heart_cy + y * heart_scale
        heart_points.append((px, py))

    # Heart color
    heart_color = (0, 80, 72, 255) if not for_android_fg else (0, 100, 92, 255)
    cd.polygon(heart_points, fill=heart_color)

    # Vital pulse line across heart
    pulse_w = max(int(2 * scale), int(heart_scale * 1.8))
    pulse_color = (224, 242, 241, 255)
    h_span = heart_scale * 14

    p_y = heart_cy + int(1 * scale)
    pts = [
        (c - h_span * 0.95, p_y),
        (c - h_span * 0.4, p_y),
        (c - h_span * 0.2, p_y - int(h_span * 0.4)),
        (c, p_y + int(h_span * 0.5)),
        (c + h_span * 0.2, p_y - int(h_span * 0.3)),
        (c + h_span * 0.35, p_y),
        (c + h_span * 0.95, p_y),
    ]

    for i in range(len(pts) - 1):
        cd.line([pts[i], pts[i + 1]], fill=pulse_color, width=pulse_w)
        cd.ellipse([pts[i][0] - pulse_w // 2, pts[i][1] - pulse_w // 2,
                    pts[i][0] + pulse_w // 2, pts[i][1] + pulse_w // 2], fill=pulse_color)

    cd.ellipse([pts[-1][0] - pulse_w // 2, pts[-1][1] - pulse_w // 2,
                pts[-1][0] + pulse_w // 2, pts[-1][1] + pulse_w // 2], fill=pulse_color)

    img = Image.alpha_composite(img, cross_layer)

    if size != canvas_dim:
        return img.resize((size, size), Image.Resampling.LANCZOS)
    return img


def generate_all():
    print("Generating brand assets...")

    fav_svg_path = os.path.join(PUBLIC_DIR, "favicon.svg")
    with open(fav_svg_path, "w", encoding="utf-8") as f:
        f.write(SVG_SQUIRCLE)
    print("  -> Created:", fav_svg_path)

    logo_svg_dir = os.path.join(PUBLIC_DIR, "assets", "images")
    os.makedirs(logo_svg_dir, exist_ok=True)
    logo_svg_path = os.path.join(logo_svg_dir, "logo.svg")
    with open(logo_svg_path, "w", encoding="utf-8") as f:
        f.write(SVG_SQUIRCLE)
    print("  -> Created:", logo_svg_path)

    ico_sizes = [16, 24, 32, 48, 64, 128, 256]
    ico_frames = [render_master_icon(s, round_shape=False) for s in ico_sizes]
    fav_ico_path = os.path.join(PUBLIC_DIR, "favicon.ico")
    ico_frames[3].save(fav_ico_path, format="ICO", sizes=[(s, s) for s in ico_sizes], append_images=ico_frames)
    print("  -> Created multi-resolution ICO (16..256):", fav_ico_path)

    apple_icon_path = os.path.join(PUBLIC_DIR, "apple-touch-icon.png")
    apple_img = render_master_icon(180, round_shape=False)
    apple_img.save(apple_icon_path, "PNG")
    print("  -> Created Apple Touch Icon:", apple_icon_path)

    densities = {
        "mipmap-mdpi": (48, 108),
        "mipmap-hdpi": (72, 162),
        "mipmap-xhdpi": (96, 216),
        "mipmap-xxhdpi": (144, 324),
        "mipmap-xxxhdpi": (192, 432)
    }

    for folder, (std_size, fg_size) in densities.items():
        dir_path = os.path.join(ANDROID_RES, folder)
        os.makedirs(dir_path, exist_ok=True)

        std_img = render_master_icon(std_size, round_shape=False)
        std_path = os.path.join(dir_path, "ic_launcher.png")
        std_img.save(std_path, "PNG")

        round_img = render_master_icon(std_size, round_shape=True)
        round_path = os.path.join(dir_path, "ic_launcher_round.png")
        round_img.save(round_path, "PNG")

        fg_img = render_master_icon(fg_size, round_shape=False, for_android_fg=True)
        fg_path = os.path.join(dir_path, "ic_launcher_foreground.png")
        fg_img.save(fg_path, "PNG")

        print(f"  -> Generated {folder}: {std_size}px squircle, {std_size}px round, {fg_size}px fg")

    v24_dir = os.path.join(ANDROID_RES, "drawable-v24")
    os.makedirs(v24_dir, exist_ok=True)
    fg_xml_path = os.path.join(v24_dir, "ic_launcher_foreground.xml")
    with open(fg_xml_path, "w", encoding="utf-8") as f:
        f.write(SVG_FOREGROUND_ANDROID)
    print("  -> Updated:", fg_xml_path)

    print("\nAll brand assets successfully generated!")

if __name__ == "__main__":
    generate_all()
