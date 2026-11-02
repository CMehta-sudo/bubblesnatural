#!/usr/bin/env python3
"""
compiler.py - Bubbles Natural Luxury Storefront Compiler

Reads catalog data from products.json, copies raw uncompressed images into
an accompanying 'images/' directory, generates a luxury-tier storefront with
a vanilla JavaScript shopping cart, quantity controls, floating bag, slide-out
overlay drawer, and invoice-style WhatsApp checkout.

Saves the output as standalone 'index.html' directly on Desktop (~/Desktop/index.html).
"""

from __future__ import annotations
import os
import sys
import json
import base64
import shutil
import mimetypes
import unicodedata
import urllib.parse
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any

# Attempt to import rich, with fallback if unavailable
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text
    from rich import box
    HAS_RICH = True
except ImportError:
    HAS_RICH = False


def normalize_string(s: str) -> str:
    """Normalize unicode strings to handle accents and combining characters."""
    return unicodedata.normalize("NFC", s)


def resolve_image_path(image_filename: str, search_dir: Path) -> Optional[Path]:
    """
    Locates an image file in the search directory handling NFC/NFD macOS differences.
    """
    if not image_filename:
        return None

    # Check direct relative path
    direct_path = search_dir / image_filename
    if direct_path.is_file():
        return direct_path

    # Check normalized NFC & NFD
    nfc_name = unicodedata.normalize("NFC", image_filename)
    nfd_name = unicodedata.normalize("NFD", image_filename)

    if (search_dir / nfc_name).is_file():
        return search_dir / nfc_name
    if (search_dir / nfd_name).is_file():
        return search_dir / nfd_name

    # Case-insensitive / normalized search in directory
    for item in search_dir.iterdir():
        if item.is_file():
            if (
                unicodedata.normalize("NFC", item.name).lower() == nfc_name.lower()
                or unicodedata.normalize("NFD", item.name).lower() == nfd_name.lower()
            ):
                return item

    return None


def generate_svg_placeholder(product_name: str) -> str:
    """
    Generates an inline SVG data URI as an elegant, luxury placeholder
    when a product photograph is missing or unreadable.
    """
    safe_title = product_name.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 600" width="100%" height="100%">
  <defs>
    <radialGradient id="luxGrad" cx="50%" cy="50%" r="70%">
      <stop offset="0%" stop-color="#FAF7F2"/>
      <stop offset="100%" stop-color="#EFE8DE"/>
    </radialGradient>
  </defs>
  <rect width="600" height="600" fill="url(#luxGrad)"/>
  <rect x="25" y="25" width="550" height="550" fill="none" stroke="#D8CEBF" stroke-width="1.5" stroke-dasharray="6,4" rx="12"/>
  <rect x="35" y="35" width="530" height="530" fill="none" stroke="#D8CEBF" stroke-width="0.8" rx="8"/>
  <circle cx="300" cy="240" r="60" fill="none" stroke="#1E352F" stroke-width="1.2"/>
  <circle cx="300" cy="240" r="54" fill="none" stroke="#A8854D" stroke-width="0.8"/>
  <path d="M300 195 C285 220 280 235 285 248 C290 260 300 265 300 265 C300 265 310 260 315 248 C320 235 315 220 300 195 Z" fill="#1E352F" opacity="0.85"/>
  <path d="M290 235 C295 245 300 250 305 245" stroke="#FFFFFF" stroke-width="1.2" fill="none" stroke-linecap="round"/>
  <text x="300" y="335" font-family="'Playfair Display', Georgia, serif" font-size="22" font-weight="600" fill="#1E352F" text-anchor="middle" letter-spacing="1.5">{safe_title}</text>
  <text x="300" y="365" font-family="'Montserrat', sans-serif" font-size="11" font-weight="500" fill="#A8854D" text-anchor="middle" letter-spacing="3.5">BUBBLES NATURAL</text>
  <text x="300" y="390" font-family="'Montserrat', sans-serif" font-size="10" font-weight="400" fill="#7A746B" text-anchor="middle" letter-spacing="1.5">ARTISANAL BOTANICAL</text>
</svg>"""
    encoded = base64.b64encode(svg.encode("utf-8")).decode("ascii")
    return f"data:image/svg+xml;base64,{encoded}"


def extract_price_number(price_str: str) -> int:
    """Extract integer price from string like '₹120' or '120'."""
    digits = "".join(ch for ch in str(price_str) if ch.isdigit())
    return int(digits) if digits else 0


def copy_raw_image(
    source_filename: str,
    search_dir: Path,
    dest_dirs: List[Path],
    product_name: str
) -> Tuple[str, bool, str]:
    """
    Finds source image, copies in full uncompressed raw quality to destination
    images/ directories without downgrading.
    Returns (relative_src_url, is_found, status_message).
    """
    resolved_path = resolve_image_path(source_filename, search_dir)
    placeholder = generate_svg_placeholder(product_name)

    if not resolved_path:
        return (placeholder, False, f"Missing ({source_filename}) - using SVG fallback")

    # Use the clean ASCII / NFC filename in destination
    clean_name = unicodedata.normalize("NFC", resolved_path.name)
    relative_path = f"images/{clean_name}"

    for d in dest_dirs:
        d.mkdir(parents=True, exist_ok=True)
        target = d / clean_name
        # Copy raw uncompressed file bytes directly
        try:
            shutil.copy2(resolved_path, target)
        except Exception as e:
            return (placeholder, False, f"Copy error ({source_filename}): {e}")

    size_kb = resolved_path.stat().st_size / 1024
    return (relative_path, True, f"Raw crystal-clear ({size_kb:.1f} KB, {clean_name})")


def compile_storefront_html(
    products: List[Dict[str, Any]],
    search_dir: Path,
    dest_image_dirs: List[Path]
) -> Tuple[str, List[Dict[str, Any]]]:
    """Compiles catalog data and cart logic into luxury standalone index.html storefront."""
    phone_number = "918240698338"
    email_address = "urvashi.mehta90@gmail.com"
    processed_items = []

    # Handle official Logo.png
    logo_src, logo_found, _ = copy_raw_image("Logo.png", search_dir, dest_image_dirs, "Bubbles Natural Logo")
    if not logo_found:
        logo_src, logo_found, _ = copy_raw_image("IMG_2886.jpg", search_dir, dest_image_dirs, "Bubbles Natural Logo")

    # Catalog JS data array for shopping cart
    cart_catalog_items = []
    cards_html = []

    for idx, p in enumerate(products):
        name = p.get("name", "Artisanal Creation")
        price = p.get("price", "₹0")
        price_num = extract_price_number(price)
        ingredients = p.get("ingredients", "Pure handcrafted botanicals, essential oils, and organic butters.")
        category = p.get("category", "soaps")

        raw_images = p.get("images") or p.get("image_paths") or [p.get("image_path", "")]
        if isinstance(raw_images, str):
            raw_images = [raw_images]
        raw_images = [img for img in raw_images if img]

        loaded_image_paths = []
        statuses = []
        for img_name in raw_images:
            img_rel_path, is_found, status_msg = copy_raw_image(img_name, search_dir, dest_image_dirs, name)
            loaded_image_paths.append(img_rel_path)
            statuses.append(status_msg)

        placeholder_fallback = generate_svg_placeholder(name)
        if not loaded_image_paths:
            loaded_image_paths.append(placeholder_fallback)
            statuses.append("No image provided - using SVG placeholder")

        primary_image = loaded_image_paths[0]

        cart_catalog_items.append({
            "id": idx,
            "name": name,
            "price": price,
            "priceNum": price_num,
            "image": primary_image,
            "category": category,
        })

        processed_items.append({
            "name": name,
            "category": category,
            "price": price,
            "image_count": len(loaded_image_paths),
            "status": "; ".join(statuses),
        })

        # Category Badge Label
        cat_badge_label = "Artisanal Creation"
        if category == "soaps":
            cat_badge_label = "Cold-Process Soap"
        elif category == "lip-care":
            cat_badge_label = "Botanical Lip Care"
        elif category == "lotions":
            cat_badge_label = "Nourishing Body Care"
        elif category == "perfumes":
            cat_badge_label = "Perfume & Aroma"
        elif category == "gifting":
            cat_badge_label = "Curated Gifting"

        # Media Container: Single Image vs Multi-Image Slider
        if len(loaded_image_paths) == 1:
            media_html = f"""
            <div class="card-media-wrapper">
              <span class="luxury-badge">{cat_badge_label}</span>
              <img src="{loaded_image_paths[0]}" alt="{name}" class="card-img" loading="lazy" onerror="this.onerror=null;this.src='{placeholder_fallback}'" />
            </div>"""
        else:
            slides_html = []
            indicators_html = []
            for s_idx, img_p in enumerate(loaded_image_paths):
                active_cls = " active" if s_idx == 0 else ""
                slides_html.append(
                    f'<div class="gallery-slide" data-slide-index="{s_idx}">'
                    f'<img src="{img_p}" alt="{name} photo {s_idx + 1}" class="card-img" loading="lazy" onerror="this.onerror=null;this.src=\'{placeholder_fallback}\'" />'
                    f'</div>'
                )
                indicators_html.append(
                    f'<span class="slider-dot{active_cls}" onclick="goToSlide(\'gallery-{idx}\', {s_idx})"></span>'
                )

            media_html = f"""
            <div class="card-media-wrapper gallery-wrapper" id="gallery-{idx}">
              <span class="luxury-badge">{cat_badge_label}</span>
              <span class="gallery-counter"><svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor" style="vertical-align: -1px; margin-right: 3px;"><path d="M21 19V5c0-1.1-.9-2-2-2H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2zM8.5 13.5l2.5 3.01L14.5 12l4.5 6H5l3.5-4.5z"/></svg>{len(loaded_image_paths)} Photos</span>
              <button type="button" class="slider-btn prev-btn" onclick="slideGallery('gallery-{idx}', -1)" aria-label="Previous photo">&#10094;</button>
              <div class="gallery-track" onscroll="updateSliderDots('gallery-{idx}')">
                {''.join(slides_html)}
              </div>
              <button type="button" class="slider-btn next-btn" onclick="slideGallery('gallery-{idx}', 1)" aria-label="Next photo">&#10095;</button>
              <div class="slider-dots-bar">
                {''.join(indicators_html)}
              </div>
            </div>"""

        card = f"""
        <!-- Product Card: {name} -->
        <article class="lux-card" data-category="{category}" id="card-{idx}">
          {media_html}
          <div class="card-body">
            <div class="card-header-row">
              <h3 class="product-title">{name}</h3>
              <div class="product-price">{price}</div>
            </div>
            <div class="ingredients-box">
              <span class="ingredients-label">✦ Ingredients &amp; Notes</span>
              <p class="ingredients-text">{ingredients}</p>
            </div>

            <!-- Quantity Selector & Add to Bag Action -->
            <div class="card-cart-controls">
              <div class="qty-control-block" aria-label="Quantity selector for {name}">
                <button type="button" class="qty-btn" onclick="adjustCardQty({idx}, -1)" aria-label="Decrease quantity">−</button>
                <span class="qty-display" id="card-qty-{idx}">1</span>
                <button type="button" class="qty-btn" onclick="adjustCardQty({idx}, 1)" aria-label="Increase quantity">+</button>
              </div>
              <button type="button" class="btn-add-to-bag" id="add-btn-{idx}" onclick="addProductToBag({idx})">
                <svg class="cart-btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M6 2L3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4z"/>
                  <line x1="3" y1="6" x2="21" y2="6"/>
                  <path d="M16 10a4 4 0 0 1-8 0"/>
                </svg>
                <span class="btn-text">Add to Bag</span>
              </button>
            </div>
          </div>
        </article>"""
        cards_html.append(card)

    cards_markup = "\n".join(cards_html)
    catalog_json_encoded = json.dumps(cart_catalog_items, ensure_ascii=False)

    html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>BUBBLES NATURAL | Luxury Handcrafted Botanicals &amp; Boutique Storefront</title>
  <meta name="description" content="Small-batch luxury organic boutique offering handcrafted cold-process soaps, botanical lip balms, fine perfumes, and curated hampers in Bengaluru.">
  <meta name="theme-color" content="#1E352F">
  <link rel="icon" type="image/png" href="{logo_src}">

  <!-- Google Fonts: Playfair Display (Serif) & Montserrat (Sans-Serif) -->
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Montserrat:ital,wght@0,300;0,400;0,500;0,600;0,700;1,400&family=Playfair+Display:ital,wght@0,400;0,500;0,600;0,700;1,400;1,600&display=swap" rel="stylesheet">

  <style>
    /* ==========================================================================
       RESET & ROOT VARIABLES
       ========================================================================== */
    *, *::before, *::after {{
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }}

    :root {{
      --bg-cream: #FDFBF7;
      --bg-surface: #FFFFFF;
      --bg-elevated: #F9F5EE;
      --text-deep: #222222;
      --text-muted: #645F59;
      --text-light: #8E877E;
      --forest-green: #1E352F;
      --forest-green-hover: #142420;
      --forest-green-soft: #28443C;
      --gold-accent: #A8854D;
      --gold-light: #E8DCC9;
      --border-soft: #EFE8DC;
      --border-card: #EAE3D6;
      --shadow-subtle: 0 4px 20px rgba(30, 53, 47, 0.05), 0 1px 3px rgba(0, 0, 0, 0.02);
      --shadow-hover: 0 14px 34px rgba(30, 53, 47, 0.10), 0 2px 6px rgba(0, 0, 0, 0.04);
      --transition-smooth: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
    }}

    html {{
      scroll-behavior: smooth;
      background-color: var(--bg-cream);
      color: var(--text-deep);
    }}

    body {{
      font-family: 'Montserrat', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      background-color: var(--bg-cream);
      color: var(--text-deep);
      line-height: 1.6;
      -webkit-font-smoothing: antialiased;
      -moz-osx-font-smoothing: grayscale;
      overflow-x: hidden;
    }}

    a {{
      color: inherit;
      text-decoration: none;
    }}

    img {{
      max-width: 100%;
      height: auto;
      display: block;
    }}

    /* ==========================================================================
       LUXURY ANNOUNCEMENT TOP BAR
       ========================================================================== */
    .top-announcement-bar {{
      background-color: var(--forest-green);
      color: #E8DCC9;
      font-size: 0.75rem;
      letter-spacing: 0.18em;
      text-transform: uppercase;
      font-weight: 500;
      padding: 10px 16px;
      text-align: center;
      border-bottom: 1px solid rgba(232, 220, 201, 0.15);
    }}

    .top-announcement-bar span {{
      display: inline-block;
      margin: 0 6px;
    }}

    /* ==========================================================================
       GLOBAL CONTAINER
       ========================================================================== */
    .container {{
      width: 100%;
      max-width: 1240px;
      margin-left: auto;
      margin-right: auto;
      padding-left: 24px;
      padding-right: 24px;
    }}

    /* ==========================================================================
       HEADER & BRAND IDENTITY
       ========================================================================== */
    .site-header {{
      padding: 48px 20px 36px;
      text-align: center;
      position: relative;
    }}

    .site-header::after {{
      content: '';
      position: absolute;
      bottom: 0;
      left: 50%;
      transform: translateX(-50%);
      width: 140px;
      height: 1px;
      background: linear-gradient(90deg, transparent, var(--gold-accent), transparent);
    }}

    .brand-logo-container {{
      display: inline-flex;
      justify-content: center;
      align-items: center;
      margin-bottom: 18px;
    }}

    .brand-logo-img {{
      max-width: 125px;
      max-height: 125px;
      object-fit: contain;
      border-radius: 12px;
      box-shadow: 0 4px 16px rgba(30, 53, 47, 0.06);
      transition: transform 0.4s cubic-bezier(0.16, 1, 0.3, 1);
    }}

    .brand-logo-img:hover {{
      transform: scale(1.04);
    }}

    .brand-title {{
      font-family: 'Playfair Display', Georgia, serif;
      font-size: clamp(2.3rem, 4.8vw, 3.6rem);
      font-weight: 600;
      letter-spacing: 0.22em;
      text-transform: uppercase;
      color: var(--forest-green);
      line-height: 1.15;
      margin-bottom: 10px;
    }}

    .brand-tagline {{
      font-family: 'Playfair Display', Georgia, serif;
      font-style: italic;
      font-size: clamp(1rem, 2.2vw, 1.25rem);
      color: var(--text-muted);
      font-weight: 400;
      letter-spacing: 0.04em;
      max-width: 680px;
      margin: 0 auto 22px;
    }}

    .trust-badges-bar {{
      display: inline-flex;
      flex-wrap: wrap;
      align-items: center;
      justify-content: center;
      gap: 12px 18px;
      padding: 10px 24px;
      background-color: rgba(255, 255, 255, 0.75);
      backdrop-filter: blur(8px);
      border: 1px solid var(--border-soft);
      border-radius: 40px;
      font-size: 0.8rem;
      font-weight: 500;
      color: var(--forest-green);
      letter-spacing: 0.08em;
      text-transform: uppercase;
      box-shadow: 0 2px 12px rgba(0, 0, 0, 0.02);
    }}

    .badge-sep {{
      color: var(--gold-accent);
      opacity: 0.6;
    }}

    /* ==========================================================================
       CATEGORY CHIPS / INTERACTIVE FILTER CAPSULES
       ========================================================================== */
    .catalog-intro-strip {{
      margin: 36px auto 40px;
      text-align: center;
    }}

    .section-eyebrow {{
      font-size: 0.72rem;
      letter-spacing: 0.28em;
      text-transform: uppercase;
      color: var(--gold-accent);
      font-weight: 600;
      margin-bottom: 8px;
      display: block;
    }}

    .section-headline {{
      font-family: 'Playfair Display', Georgia, serif;
      font-size: clamp(1.8rem, 3.5vw, 2.4rem);
      font-weight: 600;
      color: var(--forest-green);
      letter-spacing: 0.04em;
      margin-bottom: 12px;
    }}

    .section-desc {{
      color: var(--text-muted);
      max-width: 620px;
      margin: 0 auto 24px;
      font-size: 0.95rem;
      line-height: 1.65;
    }}

    .category-pills {{
      display: flex;
      flex-wrap: wrap;
      justify-content: center;
      gap: 12px;
      margin-top: 20px;
    }}

    .cat-pill {{
      cursor: pointer;
      appearance: none;
      -webkit-appearance: none;
      padding: 10px 22px;
      background-color: var(--bg-surface);
      border: 1px solid var(--border-soft);
      border-radius: 30px;
      font-family: 'Montserrat', sans-serif;
      font-size: 0.82rem;
      font-weight: 500;
      letter-spacing: 0.04em;
      color: var(--text-deep);
      transition: var(--transition-smooth);
      box-shadow: 0 2px 6px rgba(0, 0, 0, 0.02);
      user-select: none;
    }}

    .cat-pill:hover {{
      border-color: var(--forest-green);
      color: var(--forest-green);
      transform: translateY(-2px);
      box-shadow: 0 4px 12px rgba(30, 53, 47, 0.08);
    }}

    .cat-pill.active {{
      background-color: var(--forest-green);
      color: #FFFFFF;
      border-color: var(--forest-green);
      box-shadow: 0 4px 14px rgba(30, 53, 47, 0.25);
    }}

    /* ==========================================================================
       STRICT RESPONSIVE GRID BREAKPOINTS
       - Desktop (> 992px): 3 columns, spacious margins, ample whitespace
       - Tablet (768px - 992px): 2 columns
       - Mobile (< 768px): 1 column vertical scroll, full-width touch targets
       ========================================================================== */
    .products-grid {{
      display: grid;
      margin-bottom: 80px;
      transition: opacity 0.25s ease;
    }}

    /* Desktop Breakpoint (>992px) */
    @media (min-width: 993px) {{
      .products-grid {{
        grid-template-columns: repeat(3, 1fr);
        gap: 36px;
      }}
    }}

    /* Tablet Breakpoint (768px - 992px) */
    @media (min-width: 768px) and (max-width: 992px) {{
      .products-grid {{
        grid-template-columns: repeat(2, 1fr);
        gap: 26px;
      }}
    }}

    /* Mobile Phone Breakpoint (<768px) */
    @media (max-width: 767px) {{
      .products-grid {{
        grid-template-columns: 1fr;
        gap: 24px;
      }}
      .site-header {{
        padding: 36px 16px 28px;
      }}
      .brand-title {{
        letter-spacing: 0.16em;
      }}
      .trust-badges-bar {{
        font-size: 0.72rem;
        gap: 8px 12px;
        padding: 8px 16px;
      }}
      .cat-pill {{
        padding: 8px 16px;
        font-size: 0.78rem;
      }}
    }}

    /* ==========================================================================
       PRODUCT CARD AESTHETICS & MULTI-PHOTO SLIDER
       ========================================================================== */
    .lux-card {{
      background-color: var(--bg-surface);
      border: 1px solid var(--border-card);
      border-radius: 14px;
      overflow: hidden;
      display: flex;
      flex-direction: column;
      box-shadow: var(--shadow-subtle);
      transition: var(--transition-smooth);
      position: relative;
    }}

    .lux-card:hover {{
      transform: translateY(-5px);
      box-shadow: var(--shadow-hover);
      border-color: rgba(168, 133, 77, 0.45);
    }}

    .card-media-wrapper {{
      position: relative;
      width: 100%;
      height: 310px;
      background: linear-gradient(180deg, #F9F7F3 0%, #F3EEE4 100%);
      overflow: hidden;
      border-bottom: 1px solid var(--border-soft);
    }}

    .card-img {{
      width: 100%;
      height: 100%;
      object-fit: cover;
      object-position: center;
      transition: transform 0.6s cubic-bezier(0.16, 1, 0.3, 1);
    }}

    .lux-card:hover .card-img {{
      transform: scale(1.04);
    }}

    .luxury-badge {{
      position: absolute;
      top: 14px;
      left: 14px;
      z-index: 5;
      background-color: rgba(253, 251, 247, 0.94);
      color: var(--forest-green);
      font-size: 0.68rem;
      font-weight: 600;
      letter-spacing: 0.12em;
      text-transform: uppercase;
      padding: 5px 12px;
      border-radius: 20px;
      border: 1px solid rgba(234, 227, 214, 0.9);
      backdrop-filter: blur(4px);
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
      pointer-events: none;
    }}

    .gallery-counter {{
      position: absolute;
      top: 14px;
      right: 14px;
      z-index: 5;
      background-color: rgba(30, 53, 47, 0.85);
      color: #FFFFFF;
      font-size: 0.68rem;
      font-weight: 600;
      letter-spacing: 0.06em;
      padding: 4px 10px;
      border-radius: 14px;
      backdrop-filter: blur(4px);
      pointer-events: none;
    }}

    .gallery-track {{
      display: flex;
      width: 100%;
      height: 100%;
      overflow-x: auto;
      scroll-snap-type: x mandatory;
      scroll-behavior: smooth;
      -webkit-overflow-scrolling: touch;
      scrollbar-width: none;
    }}

    .gallery-track::-webkit-scrollbar {{
      display: none;
    }}

    .gallery-slide {{
      flex: 0 0 100%;
      width: 100%;
      height: 100%;
      scroll-snap-align: start;
      position: relative;
    }}

    .slider-btn {{
      position: absolute;
      top: 50%;
      transform: translateY(-50%);
      z-index: 6;
      width: 32px;
      height: 32px;
      border-radius: 50%;
      background-color: rgba(255, 255, 255, 0.88);
      color: var(--forest-green);
      border: 1px solid rgba(0, 0, 0, 0.08);
      font-size: 0.85rem;
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      opacity: 0;
      transition: var(--transition-smooth);
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
    }}

    .lux-card:hover .slider-btn {{
      opacity: 1;
    }}

    .prev-btn {{
      left: 10px;
    }}

    .next-btn {{
      right: 10px;
    }}

    .slider-btn:hover {{
      background-color: var(--forest-green);
      color: #FFFFFF;
      transform: translateY(-50%) scale(1.1);
    }}

    .slider-dots-bar {{
      position: absolute;
      bottom: 10px;
      left: 50%;
      transform: translateX(-50%);
      z-index: 5;
      display: flex;
      gap: 6px;
      padding: 4px 8px;
      background-color: rgba(0, 0, 0, 0.25);
      border-radius: 12px;
      backdrop-filter: blur(4px);
    }}

    .slider-dot {{
      width: 6px;
      height: 6px;
      border-radius: 50%;
      background-color: rgba(255, 255, 255, 0.5);
      cursor: pointer;
      transition: all 0.2s ease;
    }}

    .slider-dot.active {{
      background-color: #FFFFFF;
      transform: scale(1.3);
      width: 14px;
      border-radius: 4px;
    }}

    .card-body {{
      padding: 24px;
      display: flex;
      flex-direction: column;
      flex-grow: 1;
    }}

    .card-header-row {{
      display: flex;
      justify-content: space-between;
      align-items: baseline;
      gap: 12px;
      margin-bottom: 14px;
      padding-bottom: 12px;
      border-bottom: 1px solid rgba(239, 232, 220, 0.7);
    }}

    .product-title {{
      font-family: 'Playfair Display', Georgia, serif;
      font-size: 1.3rem;
      font-weight: 600;
      color: var(--forest-green);
      letter-spacing: 0.02em;
      line-height: 1.25;
    }}

    .product-price {{
      font-family: 'Montserrat', sans-serif;
      font-size: 1.22rem;
      font-weight: 700;
      color: var(--gold-accent);
      white-space: nowrap;
      letter-spacing: 0.02em;
    }}

    .ingredients-box {{
      margin-bottom: 20px;
      flex-grow: 1;
      background-color: #FAF8F4;
      border-radius: 8px;
      padding: 12px 14px;
      border: 1px solid rgba(239, 232, 220, 0.6);
    }}

    .ingredients-label {{
      display: block;
      font-size: 0.66rem;
      text-transform: uppercase;
      letter-spacing: 0.16em;
      font-weight: 600;
      color: var(--gold-accent);
      margin-bottom: 5px;
    }}

    .ingredients-text {{
      font-size: 0.85rem;
      color: var(--text-muted);
      line-height: 1.55;
    }}

    /* ==========================================================================
       QUANTITY CONTROLLER & ADD TO BAG BUTTON
       ========================================================================== */
    .card-cart-controls {{
      margin-top: auto;
      display: flex;
      align-items: center;
      gap: 12px;
    }}

    .qty-control-block {{
      display: inline-flex;
      align-items: center;
      background-color: #F8F5EE;
      border: 1px solid var(--border-soft);
      border-radius: 8px;
      overflow: hidden;
      height: 48px;
      flex-shrink: 0;
    }}

    .qty-btn {{
      background: none;
      border: none;
      width: 36px;
      height: 100%;
      font-size: 1.15rem;
      font-weight: 600;
      color: var(--forest-green);
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: background-color 0.2s ease, color 0.2s ease;
      user-select: none;
    }}

    .qty-btn:hover {{
      background-color: rgba(30, 53, 47, 0.1);
    }}

    .qty-btn:active {{
      background-color: rgba(30, 53, 47, 0.18);
    }}

    .qty-display {{
      min-width: 30px;
      text-align: center;
      font-weight: 600;
      font-size: 0.95rem;
      color: var(--text-deep);
      user-select: none;
    }}

    .btn-add-to-bag {{
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
      flex-grow: 1;
      height: 48px;
      background-color: var(--forest-green);
      color: #FFFFFF;
      font-family: 'Montserrat', sans-serif;
      font-size: 0.82rem;
      font-weight: 600;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      padding: 0 16px;
      border-radius: 8px;
      transition: var(--transition-smooth);
      border: 1px solid var(--forest-green);
      cursor: pointer;
      box-shadow: 0 3px 10px rgba(30, 53, 47, 0.12);
      user-select: none;
      white-space: nowrap;
    }}

    .btn-add-to-bag:hover {{
      background-color: var(--forest-green-hover);
      transform: translateY(-2px);
      box-shadow: 0 6px 16px rgba(30, 53, 47, 0.22);
    }}

    .btn-add-to-bag.added-flash {{
      background-color: #2F594C !important;
      border-color: #2F594C !important;
    }}

    .cart-btn-icon {{
      width: 17px;
      height: 17px;
      flex-shrink: 0;
    }}

    @media (max-width: 480px) {{
      .card-cart-controls {{
        flex-direction: column;
        align-items: stretch;
        gap: 10px;
      }}
      .qty-control-block {{
        width: 100%;
        justify-content: space-between;
      }}
      .qty-btn {{
        width: 48px;
      }}
      .btn-add-to-bag {{
        width: 100%;
        height: 50px;
      }}
    }}

    /* ==========================================================================
       EMPTY CATEGORY STATE
       ========================================================================== */
    .empty-category-container {{
      grid-column: 1 / -1;
      text-align: center;
      padding: 64px 24px;
      background-color: var(--bg-surface);
      border: 1px dashed var(--gold-accent);
      border-radius: 16px;
      margin: 10px 0 40px;
    }}

    .empty-icon {{
      font-size: 2.2rem;
      color: var(--gold-accent);
      margin-bottom: 14px;
    }}

    .empty-title {{
      font-family: 'Playfair Display', Georgia, serif;
      font-size: 1.6rem;
      font-weight: 600;
      color: var(--forest-green);
      margin-bottom: 10px;
    }}

    .empty-desc {{
      color: var(--text-muted);
      font-size: 0.95rem;
      max-width: 520px;
      margin: 0 auto 24px;
      line-height: 1.6;
    }}

    /* ==========================================================================
       BESPOKE GIFTING & CELEBRATION SECTION
       ========================================================================== */
    .bespoke-gifting-banner {{
      background: linear-gradient(135deg, #1E352F 0%, #2A4840 100%);
      color: #FFFFFF;
      border-radius: 18px;
      padding: 48px 36px;
      margin-bottom: 80px;
      position: relative;
      overflow: hidden;
      box-shadow: 0 16px 36px rgba(30, 53, 47, 0.12);
    }}

    .bespoke-gifting-banner::before {{
      content: '';
      position: absolute;
      top: -60px;
      right: -60px;
      width: 220px;
      height: 220px;
      border-radius: 50%;
      background: radial-gradient(circle, rgba(168, 133, 77, 0.3) 0%, transparent 70%);
      pointer-events: none;
    }}

    .gifting-inner {{
      position: relative;
      z-index: 2;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 32px;
      flex-wrap: wrap;
    }}

    .gifting-content {{
      max-width: 620px;
    }}

    .gifting-tag {{
      font-size: 0.72rem;
      text-transform: uppercase;
      letter-spacing: 0.24em;
      color: var(--gold-light);
      font-weight: 600;
      margin-bottom: 10px;
      display: inline-block;
    }}

    .gifting-title {{
      font-family: 'Playfair Display', Georgia, serif;
      font-size: clamp(1.6rem, 3vw, 2.2rem);
      font-weight: 600;
      line-height: 1.25;
      margin-bottom: 12px;
      color: #FFFFFF;
    }}

    .gifting-desc {{
      color: rgba(255, 255, 255, 0.85);
      font-size: 0.95rem;
      line-height: 1.6;
    }}

    .btn-gold {{
      display: inline-flex;
      align-items: center;
      gap: 10px;
      background-color: var(--gold-accent);
      color: #FFFFFF;
      font-weight: 600;
      font-size: 0.84rem;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      padding: 14px 26px;
      border-radius: 8px;
      transition: var(--transition-smooth);
      border: 1px solid var(--gold-accent);
      white-space: nowrap;
    }}

    .btn-gold:hover {{
      background-color: #93713D;
      transform: translateY(-2px);
      box-shadow: 0 8px 20px rgba(168, 133, 77, 0.3);
    }}

    /* ==========================================================================
       BUSINESS TRANSPARENCY LAYER ("HOW TO ORDER" 3-STEP RIBBON)
       ========================================================================== */
    .how-to-order-section {{
      background-color: var(--bg-surface);
      border: 1px solid var(--border-soft);
      border-radius: 18px;
      padding: 48px 36px;
      margin-bottom: 80px;
      box-shadow: var(--shadow-subtle);
      text-align: center;
    }}

    .order-ribbon-grid {{
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 28px;
      margin-top: 36px;
      position: relative;
    }}

    @media (max-width: 820px) {{
      .order-ribbon-grid {{
        grid-template-columns: 1fr;
        gap: 24px;
      }}
    }}

    .ribbon-step-card {{
      background-color: var(--bg-cream);
      border: 1px solid var(--border-card);
      border-radius: 12px;
      padding: 30px 22px;
      text-align: center;
      position: relative;
      transition: var(--transition-smooth);
    }}

    .ribbon-step-card:hover {{
      transform: translateY(-3px);
      border-color: var(--gold-accent);
    }}

    .step-number {{
      width: 44px;
      height: 44px;
      border-radius: 50%;
      background-color: var(--forest-green);
      color: #FFFFFF;
      font-family: 'Playfair Display', Georgia, serif;
      font-size: 1.15rem;
      font-weight: 700;
      display: flex;
      align-items: center;
      justify-content: center;
      margin: 0 auto 16px;
      box-shadow: 0 4px 10px rgba(30, 53, 47, 0.2);
    }}

    .step-title {{
      font-family: 'Playfair Display', Georgia, serif;
      font-size: 1.18rem;
      font-weight: 600;
      color: var(--forest-green);
      margin-bottom: 8px;
    }}

    .step-desc {{
      font-size: 0.85rem;
      color: var(--text-muted);
      line-height: 1.55;
    }}

    /* ==========================================================================
       COMPLETE CONTACT GRID FOOTER
       ========================================================================== */
    .site-footer {{
      background-color: #162823;
      color: #FAF7F2;
      padding: 64px 20px 32px;
      border-top: 1px solid rgba(232, 220, 201, 0.1);
    }}

    .footer-grid {{
      display: grid;
      grid-template-columns: 1.6fr 1.2fr 1.2fr;
      gap: 40px;
      margin-bottom: 48px;
    }}

    @media (max-width: 880px) {{
      .footer-grid {{
        grid-template-columns: 1fr;
        gap: 32px;
      }}
    }}

    .footer-brand-title {{
      font-family: 'Playfair Display', Georgia, serif;
      font-size: 1.8rem;
      letter-spacing: 0.18em;
      text-transform: uppercase;
      font-weight: 600;
      color: #FFFFFF;
      margin-bottom: 12px;
    }}

    .footer-tagline {{
      font-family: 'Playfair Display', Georgia, serif;
      font-style: italic;
      color: var(--gold-light);
      font-size: 0.95rem;
      margin-bottom: 18px;
    }}

    .footer-bio {{
      font-size: 0.88rem;
      color: #C5BFB5;
      line-height: 1.65;
      max-width: 380px;
    }}

    .footer-heading {{
      font-size: 0.76rem;
      letter-spacing: 0.22em;
      text-transform: uppercase;
      font-weight: 600;
      color: var(--gold-accent);
      margin-bottom: 18px;
    }}

    .contact-item {{
      display: flex;
      align-items: flex-start;
      gap: 12px;
      margin-bottom: 16px;
    }}

    .contact-icon {{
      width: 20px;
      height: 20px;
      flex-shrink: 0;
      color: var(--gold-light);
      margin-top: 2px;
    }}

    .contact-link {{
      color: #FFFFFF;
      font-size: 0.9rem;
      font-weight: 500;
      transition: color 0.2s;
    }}

    .contact-link:hover {{
      color: var(--gold-light);
      text-decoration: underline;
    }}

    .contact-sub {{
      display: block;
      font-size: 0.75rem;
      color: #9D968B;
      margin-top: 2px;
    }}

    .location-box {{
      font-size: 0.88rem;
      color: #C5BFB5;
      line-height: 1.6;
    }}

    .location-pill {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      background-color: rgba(255, 255, 255, 0.08);
      padding: 6px 14px;
      border-radius: 20px;
      font-size: 0.78rem;
      color: #E8DCC9;
      margin-top: 10px;
      border: 1px solid rgba(255, 255, 255, 0.12);
    }}

    .footer-bottom-bar {{
      padding-top: 28px;
      border-top: 1px solid rgba(255, 255, 255, 0.08);
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 16px;
      font-size: 0.8rem;
      color: #9D968B;
    }}

    .copyright-line {{
      letter-spacing: 0.02em;
    }}

    .footer-guarantee {{
      display: flex;
      align-items: center;
      gap: 8px;
    }}

    /* ==========================================================================
       PERSISTENT FLOATING SHOPPING BAG BUTTON
       ========================================================================== */
    .floating-bag-btn {{
      position: fixed;
      bottom: 28px;
      right: 28px;
      z-index: 999;
      background-color: var(--forest-green);
      color: #FFFFFF;
      border: 1px solid rgba(232, 220, 201, 0.35);
      border-radius: 36px;
      padding: 12px 22px;
      display: flex;
      align-items: center;
      gap: 12px;
      font-family: 'Montserrat', sans-serif;
      font-size: 0.88rem;
      font-weight: 600;
      letter-spacing: 0.06em;
      text-transform: uppercase;
      box-shadow: 0 10px 28px rgba(30, 53, 47, 0.35);
      cursor: pointer;
      transition: var(--transition-smooth);
    }}

    .floating-bag-btn:hover {{
      background-color: var(--forest-green-hover);
      transform: translateY(-3px) scale(1.02);
      box-shadow: 0 14px 32px rgba(30, 53, 47, 0.45);
    }}

    .floating-bag-icon {{
      width: 22px;
      height: 22px;
    }}

    .bag-badge {{
      background-color: var(--gold-accent);
      color: #FFFFFF;
      min-width: 24px;
      height: 24px;
      border-radius: 12px;
      font-size: 0.78rem;
      font-weight: 700;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      padding: 0 6px;
      transition: transform 0.2s cubic-bezier(0.16, 1, 0.3, 1);
    }}

    .bag-badge.pop {{
      transform: scale(1.3);
    }}

    @media (max-width: 600px) {{
      .floating-bag-btn {{
        bottom: 20px;
        right: 20px;
        padding: 12px 16px;
        gap: 8px;
      }}
      .floating-bag-btn .bag-label {{
        display: none;
      }}
    }}

    /* ==========================================================================
       CART OVERLAY DRAWER / SLIDE-OUT MODAL
       ========================================================================== */
    .cart-backdrop {{
      position: fixed;
      top: 0;
      left: 0;
      width: 100vw;
      height: 100vh;
      background-color: rgba(18, 30, 27, 0.55);
      backdrop-filter: blur(4px);
      z-index: 1000;
      opacity: 0;
      visibility: hidden;
      transition: opacity 0.3s ease, visibility 0.3s ease;
    }}

    .cart-backdrop.open {{
      opacity: 1;
      visibility: visible;
    }}

    .cart-drawer {{
      position: fixed;
      top: 0;
      right: 0;
      width: 100%;
      max-width: 460px;
      height: 100vh;
      background-color: #FFFFFF;
      z-index: 1001;
      box-shadow: -8px 0 32px rgba(0, 0, 0, 0.2);
      display: flex;
      flex-direction: column;
      transform: translateX(100%);
      transition: transform 0.35s cubic-bezier(0.16, 1, 0.3, 1);
    }}

    .cart-drawer.open {{
      transform: translateX(0);
    }}

    .cart-drawer-header {{
      padding: 24px;
      border-bottom: 1px solid var(--border-soft);
      display: flex;
      justify-content: space-between;
      align-items: center;
      background-color: var(--bg-cream);
    }}

    .cart-drawer-title {{
      font-family: 'Playfair Display', Georgia, serif;
      font-size: 1.4rem;
      font-weight: 600;
      color: var(--forest-green);
    }}

    .cart-close-btn {{
      background: none;
      border: none;
      font-size: 1.8rem;
      line-height: 1;
      color: var(--text-muted);
      cursor: pointer;
      padding: 4px 8px;
      transition: color 0.2s ease;
    }}

    .cart-close-btn:hover {{
      color: var(--forest-green);
    }}

    .cart-items-container {{
      flex-grow: 1;
      overflow-y: auto;
      padding: 20px 24px;
      display: flex;
      flex-direction: column;
      gap: 16px;
    }}

    .cart-item-row {{
      display: flex;
      align-items: center;
      gap: 14px;
      padding-bottom: 16px;
      border-bottom: 1px solid #F0ECE4;
    }}

    .cart-item-thumb {{
      width: 64px;
      height: 64px;
      border-radius: 8px;
      object-fit: cover;
      background-color: #F7F4EE;
      flex-shrink: 0;
      border: 1px solid var(--border-soft);
    }}

    .cart-item-info {{
      flex-grow: 1;
      min-width: 0;
    }}

    .cart-item-name {{
      font-family: 'Playfair Display', Georgia, serif;
      font-size: 0.98rem;
      font-weight: 600;
      color: var(--forest-green);
      margin-bottom: 4px;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }}

    .cart-item-unit-price {{
      font-size: 0.78rem;
      color: var(--text-muted);
      margin-bottom: 6px;
    }}

    .cart-item-controls {{
      display: flex;
      align-items: center;
      gap: 8px;
    }}

    .cart-qty-btn {{
      width: 24px;
      height: 24px;
      border-radius: 4px;
      background-color: #F0EDE5;
      border: 1px solid var(--border-soft);
      font-size: 0.85rem;
      font-weight: 600;
      color: var(--forest-green);
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      user-select: none;
    }}

    .cart-qty-btn:hover {{
      background-color: var(--gold-light);
    }}

    .cart-qty-num {{
      font-size: 0.88rem;
      font-weight: 600;
      min-width: 20px;
      text-align: center;
    }}

    .cart-item-subtotal {{
      text-align: right;
      font-weight: 700;
      font-size: 1rem;
      color: var(--gold-accent);
      white-space: nowrap;
      margin-left: 8px;
    }}

    .cart-item-remove-btn {{
      background: none;
      border: none;
      color: #A39B90;
      font-size: 1.15rem;
      cursor: pointer;
      padding: 4px;
      transition: color 0.2s ease;
      line-height: 1;
    }}

    .cart-item-remove-btn:hover {{
      color: #B93838;
    }}

    .empty-cart-notice {{
      text-align: center;
      padding: 60px 16px;
      color: var(--text-muted);
    }}

    .empty-cart-icon {{
      font-size: 2.5rem;
      color: var(--gold-accent);
      margin-bottom: 12px;
    }}

    .empty-cart-notice h4 {{
      font-family: 'Playfair Display', Georgia, serif;
      font-size: 1.3rem;
      color: var(--forest-green);
      margin-bottom: 8px;
    }}

    .cart-drawer-footer {{
      padding: 24px;
      background-color: var(--bg-cream);
      border-top: 1px solid var(--border-soft);
    }}

    .cart-total-row {{
      display: flex;
      justify-content: space-between;
      align-items: baseline;
      margin-bottom: 14px;
    }}

    .cart-total-label {{
      font-family: 'Montserrat', sans-serif;
      font-size: 0.9rem;
      text-transform: uppercase;
      letter-spacing: 0.1em;
      font-weight: 600;
      color: var(--text-deep);
    }}

    .cart-total-amount {{
      font-family: 'Montserrat', sans-serif;
      font-size: 1.5rem;
      font-weight: 700;
      color: var(--forest-green);
    }}

    .cart-shipping-note {{
      font-size: 0.76rem;
      color: var(--text-muted);
      line-height: 1.45;
      margin-bottom: 18px;
      text-align: center;
    }}

    .btn-confirm-whatsapp {{
      width: 100%;
      height: 52px;
      background-color: var(--forest-green);
      color: #FFFFFF;
      border: 1px solid var(--forest-green);
      border-radius: 8px;
      font-family: 'Montserrat', sans-serif;
      font-size: 0.88rem;
      font-weight: 600;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 10px;
      cursor: pointer;
      box-shadow: 0 4px 14px rgba(30, 53, 47, 0.2);
      transition: var(--transition-smooth);
    }}

    .btn-confirm-whatsapp:hover {{
      background-color: var(--forest-green-hover);
      transform: translateY(-2px);
      box-shadow: 0 6px 18px rgba(30, 53, 47, 0.3);
    }}

    .btn-confirm-whatsapp:disabled {{
      opacity: 0.5;
      cursor: not-allowed;
      transform: none;
    }}

    .wa-invoice-icon {{
      width: 20px;
      height: 20px;
      flex-shrink: 0;
    }}
  </style>
</head>
<body>

  <!-- Top Announcement Bar -->
  <div class="top-announcement-bar">
    <span>✦ Pure Botanicals</span>
    <span>•</span>
    <span>100% Handcrafted Luxury</span>
    <span>•</span>
    <span>Small-Batch Atelier</span>
    <span>•</span>
    <span>Pan-India Shipping ✦</span>
  </div>

  <!-- Header Section -->
  <header class="site-header">
    <div class="container">
      <div class="brand-logo-container">
        <img src="{logo_src}" alt="Bubbles Natural Logo" class="brand-logo-img" />
      </div>
      <h1 class="brand-title">Bubbles Natural</h1>
      <p class="brand-tagline">Handcrafted Organic Soaps, Botanical Lip Care, Fine Perfumes &amp; Bespoke Gifting</p>
      
      <!-- User Specified Subtle Trust Ribbon -->
      <div class="trust-badges-bar">
        <span>✦ 100% Handcrafted</span>
        <span class="badge-sep">|</span>
        <span>✦ Small-Batch Local Production</span>
        <span class="badge-sep">|</span>
        <span>✦ Bengaluru, IN</span>
      </div>
    </div>
  </header>

  <!-- Main Content Area -->
  <main class="container">

    <!-- Catalog Intro & Category Filters -->
    <section class="catalog-intro-strip">
      <span class="section-eyebrow">Mindful Formulations</span>
      <h2 class="section-headline">The Curated Botanical Collection</h2>
      <p class="section-desc">
        Formulated with cold-pressed botanical oils, raw plant butters, and therapeutic aromatics.
        Select your handcrafted favorites below and curate your order directly in your bag.
      </p>

      <!-- Category Filter Capsules -->
      <nav class="category-pills" aria-label="Product Categories">
        <button type="button" class="cat-pill active" data-filter="all">✦ All Creations</button>
        <button type="button" class="cat-pill" data-filter="soaps">Cold-Process Soaps</button>
        <button type="button" class="cat-pill" data-filter="lip-care">Botanical Lip Balms</button>
        <button type="button" class="cat-pill" data-filter="lotions">Magnesium Lotions</button>
        <button type="button" class="cat-pill" data-filter="perfumes">Perfumes &amp; Aromas</button>
        <button type="button" class="cat-pill" data-filter="gifting">Curated Gift Hampers</button>
      </nav>
    </section>

    <!-- Strict Responsive Grid Breakpoints (Desktop: 3-Col, Tablet: 2-Col, Mobile: 1-Col) -->
    <section class="products-grid" id="productGrid" aria-label="Product Showcase">
      {cards_markup}

      <!-- Empty State Container -->
      <div id="emptyCategoryState" class="empty-category-container" style="display: none;">
        <div class="empty-icon">✦</div>
        <h3 class="empty-title">No Creations Currently in this Category</h3>
        <p class="empty-desc">
          Every creation at Bubbles Natural is produced in small, limited artisanal batches.
          Custom orders, bespoke hampers, and ingredient requests are warmly welcomed directly on WhatsApp!
        </p>
        <button type="button" onclick="openCustomWhatsApp()" class="btn-add-to-bag" style="display: inline-flex; width: auto; padding: 12px 28px; margin: 0 auto;">
          Inquire on WhatsApp
        </button>
      </div>
    </section>

    <!-- Bespoke Gifting Banner -->
    <section class="bespoke-gifting-banner">
      <div class="gifting-inner">
        <div class="gifting-content">
          <span class="gifting-tag">✦ Custom Gifting &amp; Celebrations</span>
          <h2 class="gifting-title">Curated Gift Hampers &amp; Bespoke Favors</h2>
          <p class="gifting-desc">
            Planning wedding favors, baby announcements, festive hampers, or corporate wellness gifts? We craft personalized botanical sets featuring custom aroma profiles, handcrafted soaps, nourishing balms, and luxury packaging tailored to your celebrations.
          </p>
        </div>
        <div>
          <a href="https://wa.me/{phone_number}?text=Hi!%20I%20would%20like%20to%20inquire%20about%20Custom%20Gifting%20%26%20Bespoke%20Hampers" target="_blank" rel="noopener noreferrer" class="btn-gold">
            <svg class="wa-invoice-icon" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12.031 6.172c-3.181 0-5.767 2.586-5.768 5.766-.001 1.298.38 2.27 1.019 3.287l-.582 2.128 2.182-.573c.978.58 1.911.928 3.145.929 3.178 0 5.767-2.587 5.768-5.766 0-3.18-2.587-5.771-5.764-5.771zm3.392 8.244c-.144.405-.837.774-1.17.824-.299.045-.677.063-1.092-.069-.252-.08-.575-.187-.988-.365-1.739-.751-2.874-2.502-2.961-2.617-.087-.116-.708-.94-.708-1.793s.448-1.273.607-1.446c.159-.173.346-.217.462-.217l.332.007c.106.005.249-.04.39.299.144.347.491 1.2.534 1.287.043.087.072.188.014.304-.058.116-.087.188-.173.289l-.26.304c-.087.086-.177.18-.076.353.101.173.45 1.082 1.343 1.879.893.797 1.64 1.045 1.871 1.16.231.116.368.101.505-.058.138-.159.588-.686.746-.921.159-.235.318-.196.534-.116.217.08 1.372.646 1.608.762.236.116.393.173.45.27.058.097.058.56-.086.965z"/>
            </svg>
            <span>Inquire for Custom Gifting</span>
          </a>
        </div>
      </div>
    </section>

    <!-- Business Transparency Layer: 3-Step Ribbon (Add to Bag → Review Order → Confirm via WhatsApp) -->
    <section class="how-to-order-section">
      <span class="section-eyebrow">Seamless &amp; Direct</span>
      <h2 class="section-headline">How to Order</h2>
      <p class="section-desc">
        Enjoy a refined, personalized purchasing experience directly connecting you with our atelier.
      </p>

      <div class="order-ribbon-grid">
        <!-- Step 1 -->
        <div class="ribbon-step-card">
          <div class="step-number">1</div>
          <h3 class="step-title">Add to Bag</h3>
          <p class="step-desc">
            Choose your desired quantity on any product card and click 'Add to Bag'.
          </p>
        </div>

        <!-- Step 2 -->
        <div class="ribbon-step-card">
          <div class="step-number">2</div>
          <h3 class="step-title">Review Order</h3>
          <p class="step-desc">
            Open your Shopping Bag to verify quantities, subtotal amounts, and estimated total.
          </p>
        </div>

        <!-- Step 3 -->
        <div class="ribbon-step-card">
          <div class="step-number">3</div>
          <h3 class="step-title">Confirm via WhatsApp</h3>
          <p class="step-desc">
            Click 'Confirm Order via WhatsApp' to send your structured invoice directly to our concierge.
          </p>
        </div>
      </div>
    </section>

  </main>

  <!-- Complete Contact Grid Footer -->
  <footer class="site-footer">
    <div class="container">
      <div class="footer-grid">
        
        <!-- Brand Summary -->
        <div>
          <div class="footer-brand-title">Bubbles Natural</div>
          <p class="footer-tagline">Pure Botanicals • Conscious Luxury</p>
          <p class="footer-bio">
            Rooted in mindful formulation, we curate luxury-tier organic soaps, natural lip balms, nourishing magnesium lotions, and fine perfumes. Crafted in small batches to preserve botanical efficacy.
          </p>
        </div>

        <!-- Direct Contact Channels -->
        <div>
          <h3 class="footer-heading">Direct Concierge</h3>
          
          <div class="contact-item">
            <svg class="contact-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/>
              <polyline points="22,6 12,13 2,6"/>
            </svg>
            <div>
              <a href="mailto:{email_address}" class="contact-link">{email_address}</a>
              <span class="contact-sub">Official Business Email ID</span>
            </div>
          </div>

          <div class="contact-item">
            <svg class="contact-icon" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12.031 6.172c-3.181 0-5.767 2.586-5.768 5.766-.001 1.298.38 2.27 1.019 3.287l-.582 2.128 2.182-.573c.978.58 1.911.928 3.145.929 3.178 0 5.767-2.587 5.768-5.766 0-3.18-2.587-5.771-5.764-5.771zm3.392 8.244c-.144.405-.837.774-1.17.824-.299.045-.677.063-1.092-.069-.252-.08-.575-.187-.988-.365-1.739-.751-2.874-2.502-2.961-2.617-.087-.116-.708-.94-.708-1.793s.448-1.273.607-1.446c.159-.173.346-.217.462-.217l.332.007c.106.005.249-.04.39.299.144.347.491 1.2.534 1.287.043.087.072.188.014.304-.058.116-.087.188-.173.289l-.26.304c-.087.086-.177.18-.076.353.101.173.45 1.082 1.343 1.879.893.797 1.64 1.045 1.871 1.16.231.116.368.101.505-.058.138-.159.588-.686.746-.921.159-.235.318-.196.534-.116.217.08 1.372.646 1.608.762.236.116.393.173.45.27.058.097.058.56-.086.965z"/>
            </svg>
            <div>
              <a href="https://wa.me/{phone_number}" target="_blank" rel="noopener noreferrer" class="contact-link">+91 82406 98338</a>
              <span class="contact-sub">WhatsApp Support &amp; Concierge</span>
            </div>
          </div>
        </div>

        <!-- Studio & Dispatch Details -->
        <div>
          <h3 class="footer-heading">Studio &amp; Dispatch</h3>
          <div class="location-box">
            <p>100% Handcrafted in small batches.</p>
            <p>Carefully dispatched pan-India with eco-conscious protective packaging.</p>
            <div class="location-pill">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/>
                <circle cx="12" cy="10" r="3"/>
              </svg>
              <span>Bengaluru, Karnataka, India</span>
            </div>
          </div>
        </div>

      </div>

      <!-- Bottom Line -->
      <div class="footer-bottom-bar">
        <div class="copyright-line">
          &copy; 2026 Bubbles Natural. All rights reserved. Handcrafted with care in Bengaluru, India.
        </div>
        <div class="footer-guarantee">
          <span>✦ 100% Handcrafted</span>
          <span>•</span>
          <span>Small-Batch Local Production</span>
          <span>•</span>
          <span>Cruelty-Free</span>
        </div>
      </div>
    </div>
  </footer>

  <!-- ==========================================================================
       PERSISTENT FLOATING SHOPPING BAG
       ========================================================================== -->
  <button type="button" class="floating-bag-btn" id="floatingBagBtn" onclick="toggleCartDrawer(true)" aria-label="Open Shopping Bag">
    <svg class="floating-bag-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
      <path d="M6 2L3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4z"/>
      <line x1="3" y1="6" x2="21" y2="6"/>
      <path d="M16 10a4 4 0 0 1-8 0"/>
    </svg>
    <span class="bag-label">Shopping Bag</span>
    <span class="bag-badge" id="bagBadge">0</span>
  </button>

  <!-- ==========================================================================
       MINIMALIST SLIDE-OUT CART OVERLAY
       ========================================================================== -->
  <div class="cart-backdrop" id="cartBackdrop" onclick="toggleCartDrawer(false)"></div>

  <aside class="cart-drawer" id="cartDrawer" role="dialog" aria-modal="true" aria-label="Shopping Bag">
    <div class="cart-drawer-header">
      <h3 class="cart-drawer-title">Your Shopping Bag</h3>
      <button type="button" class="cart-close-btn" onclick="toggleCartDrawer(false)" aria-label="Close Shopping Bag">&times;</button>
    </div>

    <div class="cart-items-container" id="cartItemsContainer">
      <!-- Items dynamically injected via JavaScript -->
    </div>

    <div class="cart-drawer-footer">
      <div class="cart-total-row">
        <span class="cart-total-label">Estimated Total:</span>
        <span class="cart-total-amount" id="cartTotalDisplay">₹0</span>
      </div>
      <p class="cart-shipping-note">
        ✦ Orders are confirmed directly with our atelier on WhatsApp. Shipping address &amp; UPI details finalized upon dispatch confirmation.
      </p>
      <button type="button" class="btn-confirm-whatsapp" id="btnConfirmWhatsApp" onclick="confirmOrderWhatsApp()">
        <svg class="wa-invoice-icon" viewBox="0 0 24 24" fill="currentColor">
          <path d="M12.031 6.172c-3.181 0-5.767 2.586-5.768 5.766-.001 1.298.38 2.27 1.019 3.287l-.582 2.128 2.182-.573c.978.58 1.911.928 3.145.929 3.178 0 5.767-2.587 5.768-5.766 0-3.18-2.587-5.771-5.764-5.771zm3.392 8.244c-.144.405-.837.774-1.17.824-.299.045-.677.063-1.092-.069-.252-.08-.575-.187-.988-.365-1.739-.751-2.874-2.502-2.961-2.617-.087-.116-.708-.94-.708-1.793s.448-1.273.607-1.446c.159-.173.346-.217.462-.217l.332.007c.106.005.249-.04.39.299.144.347.491 1.2.534 1.287.043.087.072.188.014.304-.058.116-.087.188-.173.289l-.26.304c-.087.086-.177.18-.076.353.101.173.45 1.082 1.343 1.879.893.797 1.64 1.045 1.871 1.16.231.116.368.101.505-.058.138-.159.588-.686.746-.921.159-.235.318-.196.534-.116.217.08 1.372.646 1.608.762.236.116.393.173.45.27.058.097.058.56-.086.965z"/>
        </svg>
        <span>Confirm Order via WhatsApp</span>
      </button>
    </div>
  </aside>

  <!-- ==========================================================================
       VANILLA JAVASCRIPT: SHOPPING CART & INVOICE-STYLE WHATSAPP LOGIC
       ========================================================================== -->
  <script>
    // Product catalog data
    const CATALOG = {catalog_json_encoded};
    const PHONE_NUMBER = "{phone_number}";

    // Shopping Bag State: {{ productId: quantity }}
    let cart = {{}};

    // Card Quantity Selectors State: {{ productId: currentVal }}
    let cardQuantities = {{}};

    // -------------------------------------------------------------------------
    // CARD QUANTITY SELECTOR
    // -------------------------------------------------------------------------
    function adjustCardQty(productId, delta) {{
      const current = cardQuantities[productId] || 1;
      const updated = Math.max(1, current + delta);
      cardQuantities[productId] = updated;

      const display = document.getElementById('card-qty-' + productId);
      if (display) {{
        display.textContent = updated;
      }}
    }}

    // -------------------------------------------------------------------------
    // ADD PRODUCT TO BAG
    // -------------------------------------------------------------------------
    function addProductToBag(productId) {{
      const qtyToAdd = cardQuantities[productId] || 1;
      cart[productId] = (cart[productId] || 0) + qtyToAdd;

      // Reset card counter back to 1
      cardQuantities[productId] = 1;
      const display = document.getElementById('card-qty-' + productId);
      if (display) display.textContent = 1;

      // Visual feedback on button
      const btn = document.getElementById('add-btn-' + productId);
      if (btn) {{
        btn.classList.add('added-flash');
        const textSpan = btn.querySelector('.btn-text');
        const originalText = textSpan.textContent;
        textSpan.textContent = '✓ Added to Bag';
        setTimeout(function() {{
          textSpan.textContent = originalText;
          btn.classList.remove('added-flash');
        }}, 900);
      }}

      // Update Cart & Animate Floating Badge
      updateCartUI();
      animateBadge();
    }}

    function animateBadge() {{
      const badge = document.getElementById('bagBadge');
      if (badge) {{
        badge.classList.add('pop');
        setTimeout(function() {{
          badge.classList.remove('pop');
        }}, 250);
      }}
    }}

    // -------------------------------------------------------------------------
    // CART QUANTITY MODIFIERS INSIDE DRAWER
    // -------------------------------------------------------------------------
    function modifyCartItemQty(productId, delta) {{
      if (!cart[productId]) return;
      const newQty = cart[productId] + delta;
      if (newQty <= 0) {{
        delete cart[productId];
      }} else {{
        cart[productId] = newQty;
      }}
      updateCartUI();
    }}

    function removeCartItem(productId) {{
      delete cart[productId];
      updateCartUI();
    }}

    // -------------------------------------------------------------------------
    // UPDATE CART UI & DYNAMICALLY CALCULATE TOTAL
    // -------------------------------------------------------------------------
    function updateCartUI() {{
      const container = document.getElementById('cartItemsContainer');
      const badge = document.getElementById('bagBadge');
      const totalDisplay = document.getElementById('cartTotalDisplay');
      const confirmBtn = document.getElementById('btnConfirmWhatsApp');

      const productIds = Object.keys(cart);
      let totalItems = 0;
      let grandTotal = 0;

      if (productIds.length === 0) {{
        container.innerHTML = `
          <div class="empty-cart-notice">
            <div class="empty-cart-icon">✦</div>
            <h4>Your Shopping Bag is Empty</h4>
            <p>Explore our handcrafted botanical creations above to curate your bag.</p>
          </div>
        `;
        badge.textContent = '0';
        totalDisplay.textContent = '₹0';
        confirmBtn.disabled = true;
        return;
      }}

      let itemsHtml = '';
      productIds.forEach(function(pid) {{
        const id = parseInt(pid, 10);
        const item = CATALOG.find(function(c) {{ return c.id === id; }});
        if (!item) return;

        const qty = cart[id];
        totalItems += qty;
        const subtotal = item.priceNum * qty;
        grandTotal += subtotal;

        itemsHtml += `
          <div class="cart-item-row" id="cart-item-${{id}}">
            <img src="${{item.image}}" alt="${{item.name}}" class="cart-item-thumb" />
            <div class="cart-item-info">
              <div class="cart-item-name">${{item.name}}</div>
              <div class="cart-item-unit-price">${{item.price}} each</div>
              <div class="cart-item-controls">
                <button type="button" class="cart-qty-btn" onclick="modifyCartItemQty(${{id}}, -1)" aria-label="Decrease quantity">−</button>
                <span class="cart-qty-num">${{qty}}</span>
                <button type="button" class="cart-qty-btn" onclick="modifyCartItemQty(${{id}}, 1)" aria-label="Increase quantity">+</button>
                <button type="button" class="cart-item-remove-btn" onclick="removeCartItem(${{id}})" aria-label="Remove item" title="Remove">&times;</button>
              </div>
            </div>
            <div class="cart-item-subtotal">₹${{subtotal}}</div>
          </div>
        `;
      }});

      container.innerHTML = itemsHtml;
      badge.textContent = totalItems.toString();
      totalDisplay.textContent = '₹' + grandTotal;
      confirmBtn.disabled = false;
    }}

    // -------------------------------------------------------------------------
    // DRAWER TOGGLE
    // -------------------------------------------------------------------------
    function toggleCartDrawer(isOpen) {{
      const backdrop = document.getElementById('cartBackdrop');
      const drawer = document.getElementById('cartDrawer');
      if (isOpen) {{
        backdrop.classList.add('open');
        drawer.classList.add('open');
        document.body.style.overflow = 'hidden';
      }} else {{
        backdrop.classList.remove('open');
        drawer.classList.remove('open');
        document.body.style.overflow = '';
      }}
    }}

    // Close drawer on Escape key
    document.addEventListener('keydown', function(e) {{
      if (e.key === 'Escape') {{
        toggleCartDrawer(false);
      }}
    }});

    // -------------------------------------------------------------------------
    // INVOICE-STYLE WHATSAPP MESSAGE FORMATTING
    // -------------------------------------------------------------------------
    function confirmOrderWhatsApp() {{
      const productIds = Object.keys(cart);
      if (productIds.length === 0) return;

      let itemsFormatted = '';
      let totalAmount = 0;

      productIds.forEach(function(pid) {{
        const id = parseInt(pid, 10);
        const item = CATALOG.find(function(c) {{ return c.id === id; }});
        if (!item) return;

        const qty = cart[id];
        const subtotal = item.priceNum * qty;
        totalAmount += subtotal;

        itemsFormatted += `• ${{qty}} x ${{item.name}} (₹${{subtotal}})\\n`;
      }});

      // Exact Invoice Format per prompt specifications
      const invoiceText = 
`Hi! I would like to place an order:
----------------------------------
${{itemsFormatted.trim()}}
----------------------------------
Total Amount: ₹${{totalAmount}}

Shipping Details:
Name: 
Address: `;

      const waUrl = `https://wa.me/${{PHONE_NUMBER}}?text=${{encodeURIComponent(invoiceText)}}`;
      window.open(waUrl, '_blank');
    }}

    function openCustomWhatsApp() {{
      const text = "Hi! I would like to inquire about custom orders and bespoke hampers.";
      const waUrl = `https://wa.me/${{PHONE_NUMBER}}?text=${{encodeURIComponent(text)}}`;
      window.open(waUrl, '_blank');
    }}

    // -------------------------------------------------------------------------
    // CATEGORY FILTER CAPSULE LOGIC
    // -------------------------------------------------------------------------
    document.addEventListener('DOMContentLoaded', function() {{
      updateCartUI();

      const pills = document.querySelectorAll('.cat-pill');
      const cards = document.querySelectorAll('.lux-card');
      const emptyState = document.getElementById('emptyCategoryState');

      pills.forEach(function(pill) {{
        pill.addEventListener('click', function() {{
          pills.forEach(function(p) {{ p.classList.remove('active'); }});
          this.classList.add('active');

          const filter = this.getAttribute('data-filter');
          let visibleCount = 0;

          cards.forEach(function(card) {{
            const cardCat = card.getAttribute('data-category');
            if (filter === 'all' || cardCat === filter) {{
              card.style.display = 'flex';
              visibleCount++;
            }} else {{
              card.style.display = 'none';
            }}
          }});

          if (visibleCount === 0) {{
            emptyState.style.display = 'block';
          }} else {{
            emptyState.style.display = 'none';
          }}
        }});
      }});
    }});

    // -------------------------------------------------------------------------
    // MULTI-PHOTO GALLERY SLIDER LOGIC
    // -------------------------------------------------------------------------
    function slideGallery(galleryId, direction) {{
      const gallery = document.getElementById(galleryId);
      if (!gallery) return;
      const track = gallery.querySelector('.gallery-track');
      if (!track) return;
      const slideWidth = track.clientWidth;
      track.scrollBy({{ left: direction * slideWidth, behavior: 'smooth' }});
    }}

    function goToSlide(galleryId, slideIndex) {{
      const gallery = document.getElementById(galleryId);
      if (!gallery) return;
      const track = gallery.querySelector('.gallery-track');
      if (!track) return;
      const slideWidth = track.clientWidth;
      track.scrollTo({{ left: slideIndex * slideWidth, behavior: 'smooth' }});
    }}

    function updateSliderDots(galleryId) {{
      const gallery = document.getElementById(galleryId);
      if (!gallery) return;
      const track = gallery.querySelector('.gallery-track');
      const dots = gallery.querySelectorAll('.slider-dot');
      if (!track || !dots.length) return;

      const slideWidth = track.clientWidth;
      const scrollPos = track.scrollLeft;
      const activeIdx = Math.round(scrollPos / slideWidth);

      dots.forEach(function(dot, idx) {{
        if (idx === activeIdx) {{
          dot.classList.add('active');
        }} else {{
          dot.classList.remove('active');
        }}
      }});
    }}
  </script>

</body>
</html>"""

    return html_template, processed_items


def main():
    script_dir = Path(__file__).resolve().parent
    json_path = script_dir / "products.json"

    # Destination on User's Desktop
    desktop_dir = Path.home() / "Desktop"
    desktop_html_path = desktop_dir / "index.html"
    desktop_images_dir = desktop_dir / "images"

    # Local workspace copies
    local_html_path = script_dir / "index.html"
    local_images_dir = script_dir / "images"

    if not json_path.is_file():
        err_msg = f"Catalog file not found: {json_path}"
        if HAS_RICH:
            Console().print(f"[bold red]Error:[/bold red] {err_msg}")
        else:
            print(f"Error: {err_msg}")
        sys.exit(1)

    try:
        with open(json_path, "r", encoding="utf-8") as f:
            products_data = json.load(f)
    except Exception as e:
        err_msg = f"Failed to parse {json_path}: {e}"
        if HAS_RICH:
            Console().print(f"[bold red]Error:[/bold red] {err_msg}")
        else:
            print(f"Error: {err_msg}")
        sys.exit(1)

    dest_image_dirs = [desktop_images_dir, local_images_dir]

    # Compile Storefront HTML
    compiled_html, processed_items = compile_storefront_html(products_data, script_dir, dest_image_dirs)

    # Write output to Desktop/index.html & workspace/index.html
    try:
        desktop_html_path.write_text(compiled_html, encoding="utf-8")
        local_html_path.write_text(compiled_html, encoding="utf-8")
    except Exception as e:
        err_msg = f"Failed to write file: {e}"
        if HAS_RICH:
            Console().print(f"[bold red]Error:[/bold red] {err_msg}")
        else:
            print(f"Error: {err_msg}")
        sys.exit(1)

    file_size_kb = desktop_html_path.stat().st_size / 1024

    # Rich logging
    if HAS_RICH:
        console = Console()

        # Product summary table
        table = Table(
            title="✦ Bubbles Natural Shopping Bag Storefront ✦",
            box=box.ROUNDED,
            header_style="bold gold1",
            title_style="bold chartreuse3",
        )
        table.add_column("No.", justify="center", style="dim")
        table.add_column("Product Name", style="bold white")
        table.add_column("Category", style="cyan")
        table.add_column("Price", justify="right", style="green")
        table.add_column("Photos", justify="center", style="magenta")
        table.add_column("Raw Imagery Status", style="italic")

        for idx, item in enumerate(processed_items, start=1):
            table.add_row(
                str(idx),
                item["name"],
                item["category"],
                item["price"],
                str(item["image_count"]),
                item["status"][:45] + ("..." if len(item["status"]) > 45 else ""),
            )

        console.print()
        console.print(table)
        console.print()

        banner_text = Text()
        banner_text.append("✨ STOREFRONT & CART COMPILED SUCCESSFULLY ✨\n\n", style="bold chartreuse1")
        banner_text.append("• Standalone Output: ", style="bold")
        banner_text.append(f"{desktop_html_path} ({file_size_kb:.1f} KB)\n", style="cyan underline")
        banner_text.append("• Accompanying Images: ", style="bold")
        banner_text.append(f"{desktop_images_dir}/ (Raw uncompressed crystal-clear imagery)\n", style="italic")
        banner_text.append("• Shopping Cart System: ", style="bold")
        banner_text.append("Vanilla JS quantity selectors, dynamic total, floating bag & slide-out overlay\n")
        banner_text.append("• WhatsApp Invoice Checkout: ", style="bold")
        banner_text.append("Structured invoice with line items, sub-totals, total amount, & shipping prompt\n")
        banner_text.append("• Responsive Breakpoints: ", style="bold")
        banner_text.append("3-column desktop (>992px), 2-column tablet (768-992px), 1-column mobile (<768px)\n")
        banner_text.append("• Trust Ribbon: ", style="bold")
        banner_text.append("✦ 100% Handcrafted | ✦ Small-Batch Local Production | ✦ Bengaluru, IN\n\n")
        banner_text.append("Ready to launch and accept customer orders!", style="italic gold1")

        console.print(
            Panel(
                banner_text,
                title="[bold gold1]✦ BUBBLES NATURAL • EXPORT COMPLETE ✦[/bold gold1]",
                border_style="green",
                padding=(1, 2),
            )
        )
    else:
        print("\n" + "=" * 60)
        print("BUBBLES NATURAL - COMPILED SUCCESSFULLY")
        print("=" * 60)
        print(f"Output File: {desktop_html_path}")
        print(f"Images Directory: {desktop_images_dir}")
        print(f"Total Products: {len(products_data)}")
        print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
