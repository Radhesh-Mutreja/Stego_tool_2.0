"""
=========================================================
🕷️  NOIR STEGO TOOL — Web Application Backend
---------------------------------------------------------
Author      : Radhesh Mutreja
Course      : DFIS
Technique   : Caesar Cipher + LSB Steganography
Framework   : Flask
Version     : 2.0 (Web)
=========================================================
"""

from flask import Flask, request, jsonify
from PIL import Image
import numpy as np
import io
import base64
import os

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 32 * 1024 * 1024   # 32 MB max upload

END_MARKER = "<<<END>>>"


# ======================================================
# CAESAR CIPHER
# ======================================================

def caesar_encrypt(text, shift):
    """Encrypt plaintext using Caesar (ROT-N) cipher.
    Only alphabetic characters are shifted; everything else passes through."""
    result = []
    for char in text:
        if char.isalpha():
            base = ord('A') if char.isupper() else ord('a')
            result.append(chr((ord(char) - base + shift) % 26 + base))
        else:
            result.append(char)
    return "".join(result)


def caesar_decrypt(text, shift):
    """Decrypt Caesar cipher by encrypting with the inverse shift."""
    return caesar_encrypt(text, -shift)


# ======================================================
# BINARY CONVERSION
# ======================================================

def text_to_binary(text):
    """Convert a UTF-8 string to a flat binary string (8 bits per char)."""
    return "".join(format(ord(c), "08b") for c in text)


def binary_to_text(binary):
    """Convert a flat binary string back to a UTF-8 string."""
    chars = [binary[i:i + 8] for i in range(0, len(binary) - (len(binary) % 8), 8)]
    return "".join(chr(int(c, 2)) for c in chars)


# ======================================================
# STEGANOGRAPHY CORE
# ======================================================

def encode_text_in_image(image_bytes, secret_text, shift):
    """
    1. Encrypt plaintext with Caesar cipher.
    2. Append END_MARKER so the decoder knows where to stop.
    3. Convert encrypted text to binary.
    4. Embed each bit into the LSB of every pixel channel (R, G, B).
    5. Return the stego image as a BytesIO PNG.

    Raises ValueError if the message is too large for the image.
    """
    encrypted_text = caesar_encrypt(secret_text, shift) + END_MARKER
    binary_text    = text_to_binary(encrypted_text)

    img    = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    pixels = np.array(img, dtype=np.uint8)

    height, width, channels = pixels.shape
    capacity = height * width * channels

    if len(binary_text) > capacity:
        max_chars = (capacity // 8) - len(END_MARKER)
        raise ValueError(
            f"Message too large for this image. "
            f"Maximum payload ≈ {max_chars:,} characters."
        )

    flat      = pixels.flatten()
    bit_array = np.array(list(binary_text), dtype=np.uint8)
    flat[:len(bit_array)] = (flat[:len(bit_array)] & 254) | bit_array
    pixels    = flat.reshape((height, width, channels))

    output = io.BytesIO()
    Image.fromarray(pixels).save(output, format="PNG")
    output.seek(0)
    return output, width, height


def decode_text_from_image(image_bytes, shift):
    """
    1. Read every LSB from the image pixels in row-major order.
    2. Reconstruct binary string → UTF-8 text.
    3. Locate END_MARKER; return None if absent.
    4. Caesar-decrypt the payload with the given shift.
    """
    img    = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    pixels = np.array(img, dtype=np.uint8)

    flat = pixels.flatten()
    bits = "".join(str(b & 1) for b in flat)
    text = binary_to_text(bits)

    if END_MARKER not in text:
        return None

    encrypted = text.split(END_MARKER)[0]
    return caesar_decrypt(encrypted, shift)


# ======================================================
# SHIFT KEY VALIDATION (shared helper)
# ======================================================

def parse_shift(raw):
    """Parse and validate a shift key string. Returns (int, None) or (None, error_str)."""
    try:
        shift = int(raw)
        if not (1 <= shift <= 25):
            raise ValueError()
        return shift, None
    except (TypeError, ValueError):
        return None, "Shift key must be an integer between 1 and 25."


# ======================================================
# ROUTES
# ======================================================

@app.route("/")
def index():
    """Serve the single-page frontend."""
    html_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "index.html")
    with open(html_path, "r", encoding="utf-8") as f:
        return f.read(), 200, {"Content-Type": "text/html; charset=utf-8"}


@app.route("/api/image-info", methods=["POST"])
def api_image_info():
    """
    Accepts:  multipart/form-data  { image: <file> }
    Returns:  { filename, width, height, capacity }
    """
    if "image" not in request.files:
        return jsonify({"error": "No image provided."}), 400

    file        = request.files["image"]
    image_bytes = file.read()

    try:
        img  = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        w, h = img.size
        capacity = (w * h * 3) // 8 - len(END_MARKER)
        return jsonify({
            "filename": file.filename,
            "width":    w,
            "height":   h,
            "capacity": capacity,
        })
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400


@app.route("/api/encode", methods=["POST"])
def api_encode():
    """
    Accepts:  multipart/form-data  { image: <file>, message: str, shift: int }
    Returns:  { image_b64: <base64 PNG>, width: int, height: int }
    """
    if "image" not in request.files:
        return jsonify({"error": "No image provided."}), 400

    file        = request.files["image"]
    image_bytes = file.read()
    message     = request.form.get("message", "").strip()
    shift, err  = parse_shift(request.form.get("shift", ""))

    if not message:
        return jsonify({"error": "Message cannot be empty."}), 400
    if err:
        return jsonify({"error": err}), 400

    try:
        output_io, w, h = encode_text_in_image(image_bytes, message, shift)
        img_b64 = base64.b64encode(output_io.read()).decode("utf-8")
        return jsonify({"image_b64": img_b64, "width": w, "height": h})
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception as exc:
        return jsonify({"error": f"Encoding failed: {exc}"}), 500


@app.route("/api/decode", methods=["POST"])
def api_decode():
    """
    Accepts:  multipart/form-data  { image: <file>, shift: int }
    Returns:  { found: bool, message: str|null, length: int }
    """
    if "image" not in request.files:
        return jsonify({"error": "No image provided."}), 400

    file        = request.files["image"]
    image_bytes = file.read()
    shift, err  = parse_shift(request.form.get("shift", ""))

    if err:
        return jsonify({"error": err}), 400

    try:
        message = decode_text_from_image(image_bytes, shift)
        if message is None:
            return jsonify({"found": False, "message": None, "length": 0})
        return jsonify({"found": True, "message": message, "length": len(message)})
    except Exception as exc:
        return jsonify({"error": f"Decoding failed: {exc}"}), 500


# ======================================================
# ENTRY POINT
# ======================================================

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5050)