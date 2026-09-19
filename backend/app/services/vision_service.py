"""Computer-vision service — DEMO implementation.

This module is the plug-in point for a real plant-disease model (YOLO,
EfficientNet, PlantVillage CNN, ...). V1 ships a clearly-labelled heuristic
detector: it analyses basic colour statistics of the uploaded image with Pillow
and maps colour patterns to knowledge-graph symptom names.

* model_status is always 'demo' for this implementation.
* Confidence values produced here are DEMO VALUES derived from image
  statistics, not metrics of a trained model. Do not present them as accuracy.
"""
from __future__ import annotations

import io
import hashlib

from PIL import Image

MODEL_STATUS = 'demo'

# Rough colour rules for the demo detector (H in degrees, S/V in 0..1).
def _classify_pixels(image: Image.Image) -> dict[str, float]:
    rgb = image.convert('RGB').resize((160, 160))
    hsv = rgb.convert('HSV')
    pixels = list(hsv.getdata())
    total = len(pixels) or 1
    counts = {'yellow': 0, 'brown': 0, 'dark': 0, 'white': 0, 'green': 0}
    for h, s, v in pixels:
        hf, sf, vf = h / 255.0, s / 255.0, v / 255.0
        hue = hf * 360
        if vf < 0.18:
            counts['dark'] += 1          # very dark: necrosis / shadow
        elif sf < 0.15 and vf > 0.75:
            counts['white'] += 1         # bright, unsaturated: powder-like
        elif 35 <= hue <= 75 and sf > 0.25:
            counts['yellow'] += 1        # yellowing (chlorosis-like)
        elif (10 <= hue < 40 or 300 <= hue <= 360) and sf > 0.25 and vf < 0.65:
            counts['brown'] += 1         # brown necrotic tones
        elif 70 < hue < 170:
            counts['green'] += 1         # healthy-looking green
    return {k: round(n / total, 4) for k, n in counts.items()}


def _symptoms_from_fractions(f: dict[str, float]) -> list[str]:
    symptoms: list[str] = []
    if f['brown'] >= 0.05:
        symptoms.append('Brown Spots')
    if f['yellow'] >= 0.08:
        symptoms.append('Yellow Leaves')
    if f['white'] >= 0.10:
        symptoms.append('White Powder')
    if f['dark'] >= 0.15:
        symptoms.append('Dark Lesions')
    if f['green'] < 0.20 and f['yellow'] >= 0.05:
        symptoms.append('Leaf Curling')  # weak foliage proxy in demo mode
    return symptoms


def analyze_image(image_bytes: bytes) -> dict:
    """Analyze a plant image.

    Returns:
        {
          'predicted_condition': provisional condition (refined later by the
              reasoning engine using species + knowledge graph),
          'symptoms': [knowledge-graph symptom names],
          'confidence': demo confidence in [0, 1],
          'model_status': 'demo',
          'observations': colour-statistics used by the demo detector,
          'note': demo disclaimer,
        }
    """
    try:
        image = Image.open(io.BytesIO(image_bytes))
        image.load()
        fractions = _classify_pixels(image)
        stats_error = None
    except Exception as exc:  # unreadable / non-image upload
        fractions = {'yellow': 0.0, 'brown': 0.0, 'dark': 0.0, 'white': 0.0, 'green': 0.0}
        stats_error = f'Image could not be decoded ({exc}); demo detector returned no signals.'

    symptoms = _symptoms_from_fractions(fractions)

    if symptoms:
        # Deterministic provisional condition from the strongest colour signal.
        if 'White Powder' in symptoms:
            provisional = 'Powdery Mildew'
        elif 'Dark Lesions' in symptoms and fractions['dark'] > fractions['brown']:
            provisional = 'Late Blight'
        elif 'Brown Spots' in symptoms:
            provisional = 'Early Blight'
        else:
            provisional = 'Nitrogen Deficiency'
        # Demo confidence: dominated by signal strength, bounded to 60-90%.
        strength = min(1.0, 0.25 * len(symptoms) + sum(
            fractions[k] for k in ('brown', 'yellow', 'white', 'dark')))
        # Stable jitter from the image bytes so identical images give identical
        # results, while different images differ slightly (still deterministic).
        jitter = (int(hashlib.sha256(image_bytes).hexdigest()[:8], 16) % 9) / 200
        confidence = round(min(0.9, max(0.6, 0.55 + 0.35 * strength + jitter)), 2)
    else:
        provisional = 'No Visible Disease'
        confidence = round(0.55 + 0.2 * fractions['green'], 2)

    result = {
        'predicted_condition': provisional,
        'symptoms': symptoms,
        'confidence': confidence,
        'model_status': MODEL_STATUS,
        'observations': fractions,
        'note': ('Demo Vision Model: heuristic colour analysis, not a trained '
                 'disease classifier. Confidence is a demo value.'),
    }
    if stats_error:
        result['error'] = stats_error
    return result
