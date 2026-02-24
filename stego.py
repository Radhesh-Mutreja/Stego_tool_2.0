"""
=========================================================
🕷️ NOIR STEGO TOOL — DIGITAL FORENSICS UTILITY
---------------------------------------------------------
Author      : Radhesh Mutreja
Course      : DFIS
Technique   : Caesar Cipher + LSB Steganography
GUI         : Tkinter
Version     : 2.0 (Improved)
=========================================================

"""

# =========================
# STANDARD LIBRARIES
# =========================
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import threading
import os

# =========================
# IMAGE / NUMPY LIBRARIES
# =========================
from PIL import Image
import numpy as np


# =========================
# GLOBAL VARIABLES
# =========================
selected_image_path = None
OUTPUT_IMAGE_NAME   = "stego_output.png"
END_MARKER          = "<<<END>>>"

# ── Noir colour palette ──────────────────────────────────
BG_DARK      = "#0d0d0d"
BG_PANEL     = "#1a1a1a"
BG_ENTRY     = "#262626"
FG_WHITE     = "#e8e8e8"
FG_DIM       = "#888888"
ACCENT_RED   = "#c0392b"
ACCENT_AMBER = "#e67e22"
ACCENT_GREEN = "#27ae60"
FONT_MONO    = ("Consolas", 10)
FONT_TITLE   = ("Consolas", 22, "bold")
FONT_SUB     = ("Consolas", 10)
FONT_SMALL   = ("Consolas", 8)
FONT_LABEL   = ("Consolas", 10, "bold")


# ======================================================
# TOOLTIP HELPER
# ======================================================

class ToolTip:
    """
    Attach a simple tooltip to any widget.
    Usage: ToolTip(widget, "hint text")
    """

    def __init__(self, widget, text):
        self.widget = widget
        self.text   = text
        self.tip_window = None
        widget.bind("<Enter>", self._show)
        widget.bind("<Leave>", self._hide)

    def _show(self, _event=None):
        if self.tip_window:
            return
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 4
        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        tk.Label(
            tw,
            text=self.text,
            background="#333333",
            foreground=FG_WHITE,
            font=FONT_SMALL,
            relief="solid",
            borderwidth=1,
            padx=6,
            pady=3
        ).pack()

    def _hide(self, _event=None):
        if self.tip_window:
            self.tip_window.destroy()
            self.tip_window = None


# ======================================================
# STATUS BAR HELPER
# ======================================================

def set_status(msg, colour=FG_DIM):
    """Update the bottom status bar with a message."""
    status_var.set(msg)
    status_label.config(foreground=colour)


# ======================================================
# IMAGE SELECTION
# ======================================================

def choose_image():
    global selected_image_path

    path = filedialog.askopenfilename(
        title="Select Cover Image",
        filetypes=[("PNG Images", "*.png"), ("JPEG Images", "*.jpg *.jpeg"), ("All Images", "*.png *.jpg *.jpeg")]
    )

    if not path:
        return

    selected_image_path = path

    try:
        img = Image.open(path).convert("RGB")
        w, h = img.size
        capacity_chars = (w * h * 3) // 8 - len(END_MARKER)
        image_label.config(
            text=(
                f"📷  {os.path.basename(path)}\n"
                f"    {w} × {h} px  |  Max payload ≈ {capacity_chars:,} characters"
            ),
            foreground=ACCENT_AMBER
        )
        set_status(f"Image loaded: {os.path.basename(path)}", ACCENT_GREEN)
        _update_char_counter()
    except Exception as exc:
        show_error(f"Could not open image:\n{exc}")
        selected_image_path = None


# ======================================================
# CAESAR CIPHER LOGIC
# ======================================================

def caesar_encrypt(text, shift):
    """
    Encrypt plaintext using a Caesar (ROT-N) cipher.
    Only alphabetic characters are shifted; everything else
    is passed through unchanged.
    """
    result = []

    for char in text:
        if char.isalpha():
            base   = ord('A') if char.isupper() else ord('a')
            shifted = chr((ord(char) - base + shift) % 26 + base)
            result.append(shifted)
        else:
            result.append(char)

    return "".join(result)


def caesar_decrypt(text, shift):
    """
    Decrypt a Caesar cipher by encrypting with the inverse shift.
    """
    return caesar_encrypt(text, -shift)


# ======================================================
# TEXT <-> BINARY CONVERSION
# ======================================================

def text_to_binary(text):
    """
    Convert a UTF-8 string to a flat binary string (8 bits per char).
    """
    return "".join(format(ord(c), "08b") for c in text)


def binary_to_text(binary):
    """
    Convert a flat binary string back to a UTF-8 string.
    Stops at the first incomplete byte to avoid garbage at the end.
    """
    chars = [binary[i:i + 8] for i in range(0, len(binary) - (len(binary) % 8), 8)]
    return "".join(chr(int(c, 2)) for c in chars)


# ======================================================
# STEGANOGRAPHY CORE
# ======================================================

def encode_text_in_image(image_path, secret_text, shift, output_path):
    """
    1. Encrypt the plaintext with Caesar cipher.
    2. Append END_MARKER so the decoder knows where to stop.
    3. Convert encrypted text to binary.
    4. Embed each bit into the least-significant bit of every
       pixel channel (R, G, B) in row-major order.
    5. Save the resulting image as PNG (lossless).

    Raises ValueError if the message is too large for the image.
    """

    encrypted_text  = caesar_encrypt(secret_text, shift) + END_MARKER
    binary_text     = text_to_binary(encrypted_text)

    img    = Image.open(image_path).convert("RGB")
    pixels = np.array(img, dtype=np.uint8)

    height, width, channels = pixels.shape
    capacity = height * width * channels

    if len(binary_text) > capacity:
        max_chars = (capacity // 8) - len(END_MARKER)
        raise ValueError(
            f"Message too large for this image.\n"
            f"Maximum payload for this image is ≈ {max_chars:,} characters."
        )

    # Flatten to 1-D for easier indexing, embed bits, then reshape
    flat        = pixels.flatten()
    bit_array   = np.array(list(binary_text), dtype=np.uint8)
    flat[:len(bit_array)] = (flat[:len(bit_array)] & 254) | bit_array
    pixels      = flat.reshape((height, width, channels))

    Image.fromarray(pixels).save(output_path, format="PNG")


def decode_text_from_image(image_path, shift):
    """
    1. Read every LSB from the image pixels in row-major order.
    2. Reconstruct the binary string → UTF-8 text.
    3. Locate END_MARKER; if absent, report no message found.
    4. Caesar-decrypt the payload with the given shift.

    Returns the decrypted message string, or an informational
    message if no hidden data is detected.
    """

    img    = Image.open(image_path).convert("RGB")
    pixels = np.array(img, dtype=np.uint8)

    flat   = pixels.flatten()
    bits   = "".join(str(b & 1) for b in flat)
    text   = binary_to_text(bits)

    if END_MARKER not in text:
        return None     # caller will handle the "not found" case

    encrypted = text.split(END_MARKER)[0]
    return caesar_decrypt(encrypted, shift)


# ======================================================
# SHIFT KEY VALIDATION
# ======================================================

def _get_validated_shift():
    """
    Read and validate the shift entry.
    Returns an integer in [1, 25] or None and shows an error.
    """
    raw = shift_entry.get().strip()

    if not raw.isdigit():
        show_error("Caesar Shift Key must be a whole number (1 – 25).")
        return None

    shift = int(raw)

    if not (1 <= shift <= 25):
        show_error("Caesar Shift Key must be between 1 and 25.")
        return None

    return shift


# ======================================================
# CHARACTER COUNTER
# ======================================================

def _update_char_counter(_event=None):
    """
    Refresh the character counter label below the input text box.
    If an image is loaded, also warn when the message approaches capacity.
    """
    text  = encode_input_box.get("1.0", tk.END).strip()
    count = len(text)
    char_counter_label.config(text=f"Characters: {count:,}")

    if selected_image_path:
        try:
            img = Image.open(selected_image_path).convert("RGB")
            w, h = img.size
            capacity_chars = (w * h * 3) // 8 - len(END_MARKER)
            if count > capacity_chars:
                char_counter_label.config(foreground=ACCENT_RED)
                set_status("⚠  Message exceeds image capacity!", ACCENT_RED)
            elif count > capacity_chars * 0.8:
                char_counter_label.config(foreground=ACCENT_AMBER)
            else:
                char_counter_label.config(foreground=FG_DIM)
        except Exception:
            char_counter_label.config(foreground=FG_DIM)
    else:
        char_counter_label.config(foreground=FG_DIM)


# ======================================================
# GUI ACTIONS
# ======================================================

def encode_action():
    """
    Encode worker — runs in a background thread.
    Reads the message from encode_input_box, encrypts it,
    hides it in the selected image, and saves to a user-chosen path.
    """
    if not selected_image_path:
        show_error("Please select a cover image first.")
        return

    text  = encode_input_box.get("1.0", tk.END).strip()
    shift = _get_validated_shift()

    if not text:
        show_error("Please enter a message to hide.")
        return

    if shift is None:
        return

    output_path = filedialog.asksaveasfilename(
        title="Save Stego Image As",
        defaultextension=".png",
        initialfile=OUTPUT_IMAGE_NAME,
        filetypes=[("PNG Image", "*.png")]
    )

    if not output_path:
        set_status("Encode cancelled.", FG_DIM)
        return

    set_status("Encoding… please wait.", ACCENT_AMBER)
    encode_btn.config(state=tk.DISABLED)
    decode_btn.config(state=tk.DISABLED)

    try:
        encode_text_in_image(selected_image_path, text, shift, output_path)
        show_info(
            f"✅  Message encrypted and hidden successfully!\n\n"
            f"Saved to:\n{output_path}"
        )
        set_status(f"Encoded → {os.path.basename(output_path)}", ACCENT_GREEN)
    except Exception as exc:
        show_error(str(exc))
        set_status("Encode failed.", ACCENT_RED)
    finally:
        encode_btn.config(state=tk.NORMAL)
        decode_btn.config(state=tk.NORMAL)


def decode_action():
    """
    Decode worker — runs in a background thread.
    Extracts and decrypts the hidden message from the selected image,
    then displays it in the read-only decode output panel.
    """
    if not selected_image_path:
        show_error("Please select a stego image to decode.")
        return

    shift = _get_validated_shift()

    if shift is None:
        return

    set_status("Decoding… please wait.", ACCENT_AMBER)
    encode_btn.config(state=tk.DISABLED)
    decode_btn.config(state=tk.DISABLED)

    try:
        message = decode_text_from_image(selected_image_path, shift)

        decode_output_box.config(state=tk.NORMAL)
        decode_output_box.delete("1.0", tk.END)

        if message is None:
            decode_output_box.insert(tk.END, "[No hidden message found in this image.]")
            set_status("Decode complete — no message detected.", ACCENT_AMBER)
        else:
            decode_output_box.insert(tk.END, message)
            set_status(f"Decoded successfully  ({len(message):,} characters).", ACCENT_GREEN)

        decode_output_box.config(state=tk.DISABLED)

    except Exception as exc:
        show_error(str(exc))
        set_status("Decode failed.", ACCENT_RED)
    finally:
        encode_btn.config(state=tk.NORMAL)
        decode_btn.config(state=tk.NORMAL)


def copy_decoded_to_clipboard():
    """
    Copy the current content of the decode output box to the system clipboard.
    """
    decode_output_box.config(state=tk.NORMAL)
    content = decode_output_box.get("1.0", tk.END).strip()
    decode_output_box.config(state=tk.DISABLED)

    if content and not content.startswith("[No hidden"):
        root.clipboard_clear()
        root.clipboard_append(content)
        set_status("Decoded message copied to clipboard.", ACCENT_GREEN)
    else:
        set_status("Nothing to copy.", FG_DIM)


def clear_encode_input():
    """Clear the encode input text box and reset the character counter."""
    encode_input_box.delete("1.0", tk.END)
    _update_char_counter()
    set_status("Input cleared.", FG_DIM)


# ======================================================
# THREADING WRAPPERS
# ======================================================

def threaded_encode():
    threading.Thread(target=encode_action, daemon=True).start()


def threaded_decode():
    threading.Thread(target=decode_action, daemon=True).start()


# ======================================================
# CONVENIENCE UI HELPERS
# ======================================================

def show_error(msg):
    messagebox.showerror("Error", msg)


def show_info(msg):
    messagebox.showinfo("Success", msg)


def _styled_button(parent, text, command, colour=ACCENT_RED, width=20):
    """
    Factory for a consistently styled dark-theme button.
    """
    return tk.Button(
        parent,
        text=text,
        command=command,
        width=width,
        background=colour,
        foreground=FG_WHITE,
        activebackground="#333333",
        activeforeground=FG_WHITE,
        relief="flat",
        font=FONT_MONO,
        cursor="hand2",
        padx=6,
        pady=4
    )


def _section_label(parent, text):
    """A consistent section-heading label."""
    return tk.Label(
        parent,
        text=text,
        font=FONT_LABEL,
        background=BG_PANEL,
        foreground=ACCENT_AMBER
    )


# ======================================================
# GUI SETUP
# ======================================================

root = tk.Tk()
root.title("🕷️  Noir Stego Tool — DFIS Utility  v2.0")
root.geometry("900x780")
root.resizable(False, False)
root.configure(background=BG_DARK)

status_var = tk.StringVar(value="Ready.")

# ── Title bar ───────────────────────────────────────────
title_frame = tk.Frame(root, background=BG_DARK)
title_frame.pack(fill="x", pady=(18, 0))

tk.Label(
    title_frame,
    text="NOIR STEGO TOOL",
    font=FONT_TITLE,
    background=BG_DARK,
    foreground=FG_WHITE
).pack()

tk.Label(
    title_frame,
    text="Caesar Cipher  +  LSB Steganography  |  DFIS Utility  v2.0",
    font=FONT_SUB,
    background=BG_DARK,
    foreground=FG_DIM
).pack(pady=(2, 12))

separator_top = tk.Frame(root, height=1, background=ACCENT_RED)
separator_top.pack(fill="x", padx=20)

# ── Image selection panel ────────────────────────────────
img_panel = tk.Frame(root, background=BG_PANEL, pady=10, padx=20)
img_panel.pack(fill="x", padx=20, pady=(12, 6))

_section_label(img_panel, "① SELECT IMAGE").pack(anchor="w")

img_btn_row = tk.Frame(img_panel, background=BG_PANEL)
img_btn_row.pack(anchor="w", pady=(6, 0))

select_img_btn = _styled_button(img_btn_row, "📂  Choose Image", choose_image, colour="#2c3e50", width=18)
select_img_btn.pack(side=tk.LEFT)
ToolTip(select_img_btn, "Select a PNG or JPEG cover image")

image_label = tk.Label(
    img_panel,
    text="No image selected",
    font=FONT_SMALL,
    background=BG_PANEL,
    foreground=FG_DIM,
    justify="left"
)
image_label.pack(anchor="w", pady=(6, 0))

# ── Shift key panel ──────────────────────────────────────
shift_panel = tk.Frame(root, background=BG_PANEL, pady=10, padx=20)
shift_panel.pack(fill="x", padx=20, pady=6)

_section_label(shift_panel, "② SET CAESAR SHIFT KEY  (1 – 25)").pack(anchor="w")

shift_row = tk.Frame(shift_panel, background=BG_PANEL)
shift_row.pack(anchor="w", pady=(6, 0))

tk.Label(
    shift_row,
    text="Shift:",
    font=FONT_MONO,
    background=BG_PANEL,
    foreground=FG_WHITE
).pack(side=tk.LEFT)

shift_entry = tk.Entry(
    shift_row,
    width=6,
    font=FONT_MONO,
    background=BG_ENTRY,
    foreground=FG_WHITE,
    insertbackground=FG_WHITE,
    relief="flat",
    justify="center"
)
shift_entry.insert(0, "3")
shift_entry.pack(side=tk.LEFT, padx=8)
ToolTip(shift_entry, "Integer 1–25: the Caesar cipher rotation amount")

tk.Label(
    shift_row,
    text="(Both encoder and decoder must use the same key)",
    font=FONT_SMALL,
    background=BG_PANEL,
    foreground=FG_DIM
).pack(side=tk.LEFT, padx=6)

# ── Encode panel ─────────────────────────────────────────
enc_panel = tk.Frame(root, background=BG_PANEL, pady=10, padx=20)
enc_panel.pack(fill="x", padx=20, pady=6)

enc_header_row = tk.Frame(enc_panel, background=BG_PANEL)
enc_header_row.pack(fill="x")

_section_label(enc_header_row, "③ MESSAGE TO HIDE  (encode)").pack(side=tk.LEFT)

char_counter_label = tk.Label(
    enc_header_row,
    text="Characters: 0",
    font=FONT_SMALL,
    background=BG_PANEL,
    foreground=FG_DIM
)
char_counter_label.pack(side=tk.RIGHT)

encode_input_box = scrolledtext.ScrolledText(
    enc_panel,
    width=100,
    height=7,
    font=FONT_MONO,
    background=BG_ENTRY,
    foreground=FG_WHITE,
    insertbackground=FG_WHITE,
    relief="flat",
    wrap=tk.WORD
)
encode_input_box.pack(pady=(6, 0))
encode_input_box.bind("<KeyRelease>", _update_char_counter)
ToolTip(encode_input_box, "Type the secret message you want to embed in the image")

enc_btn_row = tk.Frame(enc_panel, background=BG_PANEL)
enc_btn_row.pack(anchor="e", pady=(6, 0))

clear_btn = _styled_button(enc_btn_row, "✖  Clear", clear_encode_input, colour="#555555", width=10)
clear_btn.pack(side=tk.LEFT, padx=(0, 10))
ToolTip(clear_btn, "Clear the input text box")

encode_btn = _styled_button(enc_btn_row, "🔒  Encode & Hide", threaded_encode, colour=ACCENT_RED, width=20)
encode_btn.pack(side=tk.LEFT)
ToolTip(encode_btn, "Encrypt the message and embed it into the selected image")

# ── Decode panel ─────────────────────────────────────────
dec_panel = tk.Frame(root, background=BG_PANEL, pady=10, padx=20)
dec_panel.pack(fill="x", padx=20, pady=6)

dec_header_row = tk.Frame(dec_panel, background=BG_PANEL)
dec_header_row.pack(fill="x")

_section_label(dec_header_row, "④ DECODED MESSAGE  (read-only)").pack(side=tk.LEFT)

copy_btn = _styled_button(dec_header_row, "📋  Copy", copy_decoded_to_clipboard, colour="#2c3e50", width=10)
copy_btn.pack(side=tk.RIGHT)
ToolTip(copy_btn, "Copy the decoded message to clipboard")

decode_output_box = scrolledtext.ScrolledText(
    dec_panel,
    width=100,
    height=6,
    font=FONT_MONO,
    background="#111111",
    foreground=ACCENT_GREEN,
    insertbackground=ACCENT_GREEN,
    relief="flat",
    wrap=tk.WORD,
    state=tk.DISABLED
)
decode_output_box.pack(pady=(6, 0))

dec_btn_row = tk.Frame(dec_panel, background=BG_PANEL)
dec_btn_row.pack(anchor="e", pady=(6, 0))

decode_btn = _styled_button(dec_btn_row, "🔓  Decode & Decrypt", threaded_decode, colour="#16a085", width=22)
decode_btn.pack(side=tk.LEFT)
ToolTip(decode_btn, "Extract and decrypt the hidden message from the selected image")

# ── Separator ────────────────────────────────────────────
tk.Frame(root, height=1, background=ACCENT_RED).pack(fill="x", padx=20, pady=(10, 0))

# ── Status bar ───────────────────────────────────────────
status_bar = tk.Frame(root, background=BG_DARK, pady=4)
status_bar.pack(fill="x", padx=20, side=tk.BOTTOM)

tk.Label(
    status_bar,
    text="Educational Use Only  |  Digital Forensics Project  |  © 2026 Radhesh Mutreja",
    font=FONT_SMALL,
    background=BG_DARK,
    foreground=FG_DIM
).pack(side=tk.RIGHT)

status_label = tk.Label(
    status_bar,
    textvariable=status_var,
    font=FONT_SMALL,
    background=BG_DARK,
    foreground=FG_DIM,
    anchor="w"
)
status_label.pack(side=tk.LEFT)

# ── Launch ───────────────────────────────────────────────
root.mainloop()