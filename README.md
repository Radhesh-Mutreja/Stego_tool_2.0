# 🕷️ Noir Stego Tool

> **Caesar Cipher + LSB Steganography** — Digital Forensics Utility  
> Built with Python & Tkinter | DFIS Course Project

---

## 📸 Overview

**Noir Stego Tool** is a desktop steganography application that lets you secretly hide encrypted text messages inside ordinary image files. It uses two layers of security:

1. **Caesar Cipher** — encrypts the plaintext before embedding
2. **LSB (Least Significant Bit) Steganography** — hides the encrypted data inside pixel channels of a PNG/JPEG image, invisible to the naked eye

The GUI is built with a full **noir dark theme** using Tkinter.

---

## ✨ Features

- 🔒 **Encode** — Encrypt a message with Caesar cipher and silently embed it into any PNG/JPEG image
- 🔓 **Decode** — Extract and decrypt a hidden message from a stego image
- 🎨 **Noir Dark UI** — Styled dark theme with red, amber, and green accents
- 📊 **Live Character Counter** — See how many characters you've typed, with capacity warnings
- 📷 **Image Info** — Displays resolution and maximum payload capacity on load
- 💾 **Save-As Dialog** — Choose exactly where to save your stego image output
- 📋 **Copy to Clipboard** — One-click copy of any decoded message
- ⚡ **Threaded Operations** — Encode/decode runs in a background thread; UI stays responsive
- 🛡️ **Input Validation** — Shift key enforced to valid range (1–25), friendly error messages
- 💬 **Status Bar** — Live feedback on every operation

---

## 🛠️ Tech Stack

| Component | Library |
|---|---|
| GUI | `tkinter` + `scrolledtext` |
| Image processing | `Pillow (PIL)` |
| Pixel manipulation | `NumPy` |
| Cipher | Caesar Cipher (custom implementation) |
| Steganography | LSB (Least Significant Bit) |
| Threading | `threading` (stdlib) |

---

## 📦 Installation

**Requirements:** Python 3.8+

```bash
# Clone the repository
git clone https://github.com/your-username/noir-stego-tool.git
cd noir-stego-tool

# Install dependencies
pip install pillow numpy

# Run the app
python noir_stego_tool.py
```

---

## 🚀 How to Use

### Hiding a Message (Encode)

1. Click **📂 Choose Image** and select a PNG or JPEG cover image
2. Enter a **Caesar Shift Key** (any number from 1 to 25)
3. Type your secret message in the **Message to Hide** box
4. Click **🔒 Encode & Hide**
5. Choose where to save the output PNG — share this file with your recipient

### Extracting a Message (Decode)

1. Click **📂 Choose Image** and select the stego image (the output PNG)
2. Enter the **same Caesar Shift Key** that was used to encode
3. Click **🔓 Decode & Decrypt**
4. The hidden message appears in the **Decoded Message** panel
5. Use **📋 Copy** to copy it to your clipboard

> ⚠️ Both sender and receiver must use the **same shift key** — it acts as the shared secret.

---

## 🔬 How It Works

```
Plaintext  ──► Caesar Encrypt ──► Encrypted Text + <<<END>>> marker
                                          │
                                   Text → Binary
                                          │
                              Each bit replaces the LSB
                              of one pixel channel (R/G/B)
                                          │
                                   Output PNG saved
```

**LSB steganography** works because flipping the last bit of a pixel's colour value changes its brightness by at most 1 out of 255 — completely imperceptible to the human eye, but perfectly readable by the decoder.

**Example capacity:** A 1920 × 1080 image can hold approximately **777,592 characters** of hidden text.

---

## 📁 Project Structure

```
noir-stego-tool/
│
├── noir_stego_tool.py      # Main application (single-file)
├── README.md
└── sample_images/          # Optional: test images
```

---

## ⚠️ Limitations & Disclaimer

- **Caesar cipher is not cryptographically secure.** It is trivially brute-forced with only 25 possible keys. This tool is intended for **educational and forensics demonstration purposes only**.
- Output must be saved as **PNG** (lossless). JPEG re-compression will destroy the hidden bits.
- The tool does not support images with alpha channels (RGBA) — they are auto-converted to RGB on load.
- Very large messages in small images will raise a capacity error.

> 📚 **Educational Use Only** — Created as part of a Digital Forensics course project.

---

## 🔮 Possible Future Improvements

- [ ] AES or Vigenère cipher for real cryptographic security
- [ ] Brute-force decode button (tries all 25 shifts)
- [ ] Drag-and-drop image support
- [ ] Histogram comparison view (original vs stego image)
- [ ] CLI mode for scripting / automation
- [ ] Support for RGBA and BMP images

---

## 👤 Author

**Radhesh Mutreja**  
Digital Forensics & Information Security (DFIS) Course  
© 2026 — All rights reserved

---

## 📄 License

This project is for academic and educational purposes. Please do not use steganography tools to conceal illegal activity.
