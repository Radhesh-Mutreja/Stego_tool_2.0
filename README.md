# 🕷️ Noir Stego Tool

<div align="center">

![Python](https://img.shields.io/badge/Python-3.8+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.0+-000000?style=for-the-badge&logo=flask&logoColor=white)
![NumPy](https://img.shields.io/badge/NumPy-1.24+-013243?style=for-the-badge&logo=numpy&logoColor=white)
![License](https://img.shields.io/badge/License-Educational-red?style=for-the-badge)
![Status](https://img.shields.io/badge/Status-Active-00ff88?style=for-the-badge)

**Caesar Cipher + LSB Steganography — Web Application**

*Hide encrypted messages inside images. Built for DFIS coursework at NFSU Delhi.*

[Features](#-features) · [How It Works](#-how-it-works) · [Setup](#-setup--run) · [API](#-api-reference) · [Screenshots](#-screenshots)

</div>

---

## 🧠 What Is This?

Noir Stego Tool is a web-based **steganography utility** that combines two classic information hiding techniques:

1. **Caesar Cipher** — encrypts your plaintext message by rotating each alphabetic character by a chosen shift value (1–25)
2. **LSB (Least Significant Bit) Steganography** — embeds the encrypted message bit-by-bit into the least significant bits of every pixel channel (R, G, B) in a cover image

The result is a stego image that looks visually identical to the original but carries a hidden, encrypted payload. The output is always saved as **PNG** (lossless) to preserve the embedded data — saving as JPEG would corrupt it.

Built as part of the **MSc Digital Forensics & Information Security** programme at **NFSU Delhi**.

---

## ✨ Features

- 🔒 **Encode** — encrypt a message and hide it inside any PNG/JPEG image
- 🔓 **Decode** — extract and decrypt a hidden message from a stego image
- 🌐 **Web UI** — noir-themed browser interface, no desktop app needed
- 📊 **Capacity checker** — shows max payload size for the selected image in real time
- 📥 **Download** — stego output served directly as a downloadable PNG
- 🔌 **REST API** — clean JSON endpoints, easy to integrate or test with curl/Postman
- 📱 **Responsive** — works on desktop and mobile

---

## 🔬 How It Works

### Step 1 — Caesar Cipher Encryption

Each alphabetic character in the message is shifted forward by `N` positions in the alphabet (where N is your chosen shift key, 1–25). Non-alphabetic characters like spaces, numbers, and punctuation pass through unchanged.

```
Plaintext:  "Hello World"   (shift = 3)
Ciphertext: "Khoor Zruog"
```

Decryption simply applies the inverse shift (`-N`).

### Step 2 — LSB Steganography

The encrypted message is converted to binary (UTF-8, 8 bits per character), then an end marker `<<<END>>>` is appended so the decoder knows where the payload stops.

Each bit is written into the **least significant bit** of each colour channel (R, G, B) of every pixel, in row-major order:

```
Original pixel:  R=11001010  G=10110101  B=01110010
Message bits:           [1]         [0]         [1]
Stego pixel:     R=11001011  G=10110100  B=01110011
```

Flipping only the LSB causes a maximum brightness change of ±1 out of 255 — completely imperceptible to the human eye.

### Capacity Formula

```
Max characters = (width × height × 3) ÷ 8 − 9
```

A standard 1920×1080 image can hold approximately **776,151 characters**.

### Why PNG?

PNG uses lossless compression — every pixel value is preserved exactly. JPEG uses lossy compression which destroys the LSB data during compression. Always output and share stego images as PNG.

---

## 📁 File Structure

```
noir_stego/
├── app.py            ← Flask backend — cipher logic, stego core, API routes
├── index.html        ← Single-page frontend — noir UI (HTML/CSS/JS)
├── requirements.txt  ← Python dependencies
└── README.md         ← This file
```

---

## ⚙️ Setup & Run

### Prerequisites

- Python 3.8 or higher
- pip

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/Radhesh-Mutreja/noir-stego-tool.git
cd noir-stego-tool

# 2. Install dependencies
pip install -r requirements.txt

# 3. Start the server
python app.py

# 4. Open in your browser
#    → http://localhost:5050
```

### Dependencies

```
flask>=3.0.0
Pillow>=10.0.0
numpy>=1.24.0
```

---

## 🌐 API Reference

All endpoints accept `multipart/form-data`. All responses are JSON.

### `GET /`
Serves the frontend interface.

---

### `POST /api/image-info`

Returns metadata and payload capacity for an uploaded image.

**Request**
| Field | Type | Description |
|-------|------|-------------|
| `image` | file | PNG or JPEG image |

**Response**
```json
{
  "filename": "cover.png",
  "width": 1920,
  "height": 1080,
  "capacity": 776151
}
```

---

### `POST /api/encode`

Encrypts a message with Caesar cipher and embeds it into the image via LSB steganography. Returns the stego image as base64.

**Request**
| Field | Type | Description |
|-------|------|-------------|
| `image` | file | PNG or JPEG cover image |
| `message` | string | Plaintext message to hide |
| `shift` | integer | Caesar shift key (1–25) |

**Response**
```json
{
  "image_b64": "<base64 encoded PNG>",
  "width": 1920,
  "height": 1080
}
```

---

### `POST /api/decode`

Extracts and decrypts a hidden message from a stego image.

**Request**
| Field | Type | Description |
|-------|------|-------------|
| `image` | file | Stego PNG image |
| `shift` | integer | Caesar shift key used during encoding (1–25) |

**Response**
```json
{
  "found": true,
  "message": "Hello World",
  "length": 11
}
```

If no hidden message is detected:
```json
{
  "found": false,
  "message": null,
  "length": 0
}
```

---

## 🧪 Testing with curl

```bash
# Encode a message
curl -X POST http://localhost:5050/api/encode \
  -F "image=@cover.png" \
  -F "message=secret message here" \
  -F "shift=7"

# Decode a message
curl -X POST http://localhost:5050/api/decode \
  -F "image=@stego_output.png" \
  -F "shift=7"
```

---

## ⚠️ Limitations & Notes

| Limitation | Detail |
|------------|--------|
| **Shift key** | Both encoder and decoder must use the same shift key — there is no key recovery |
| **Image format** | Output is always PNG. Never re-save a stego image as JPEG |
| **Caesar cipher** | Only alphabetic characters are shifted. Numbers, spaces, and symbols are passed through unchanged |
| **Capacity** | Message size is limited by image dimensions. The UI warns you if the message exceeds capacity |
| **Security** | Caesar cipher is not cryptographically secure. This tool is for educational demonstration only |

---

## 🔐 Security Disclaimer

This tool is built for **educational purposes** as part of DFIS coursework. Caesar cipher is a classical substitution cipher and provides no real cryptographic security — it can be broken trivially with frequency analysis or brute force (only 25 possible keys). Do not use this tool to hide genuinely sensitive information. For real-world steganography research, consider AES encryption combined with steganographic embedding.

---

## 👤 Author

**Radhesh Mutreja**
MSc Digital Forensics & Information Security — NFSU Delhi

[![GitHub](https://img.shields.io/badge/GitHub-Radhesh--Mutreja-181717?style=flat&logo=github)](https://github.com/Radhesh-Mutreja)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-radhesh--mutreja-0A66C2?style=flat&logo=linkedin)](https://www.linkedin.com/in/radhesh-mutreja-210714271/)
[![TryHackMe](https://img.shields.io/badge/TryHackMe-nullRdx-212C42?style=flat&logo=tryhackme)](https://tryhackme.com/p/nullRdx)

---

<div align="center">
<sub>Built with Python, Flask & too much coffee ☕ · NFSU Delhi · 2026</sub>
</div>
