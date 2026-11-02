# Error-Resilient Image Transmission using Reed-Solomon Codes

A Python demo that sends an image through a noisy channel and recovers it using Reed-Solomon error-correcting codes.

## Overview

Real communication channels corrupt data. This project shows the problem and the fix in two stages:

1. **Without correction:** the image passes through a noisy channel and arrives visibly damaged.
2. **With Reed-Solomon:** the image is encoded with parity bytes before transmission, and the receiver uses them to detect and repair the corrupted bytes.

A Reed-Solomon block with `n` parity bytes can correct up to `n/2` corrupted bytes. If a block has more errors than that, it cannot be fully recovered.

## How it works

- **Sender** reads the image, applies Reed-Solomon encoding, and transmits the data.
- **Channel** simulates a noisy link by corrupting bytes in transit.
- **Receiver** collects the data, decodes it with Reed-Solomon, and reconstructs the image.
- The **codec** (`rs_codec.py`) holds the encode and decode logic shared by the other components.

## Project structure

```
.
├── rs_codec.py       # Reed-Solomon encode/decode logic
├── sender.py         # Encodes the image and transmits it
├── channel.py        # Simulates the noisy channel
├── receiver.py       # Receives, decodes and reconstructs the image
├── test_codec.py     # Tests for the codec
├── assets/           # Sample input images
├── output/           # Generated results
└── requirements.txt  # Python dependencies
```

## Requirements

- Python 3
- [reedsolo](https://pypi.org/project/reedsolo/)
- [Pillow](https://pypi.org/project/pillow/)

Install the dependencies:

```bash
python3 -m pip install -r requirements.txt
```

## Usage

Open three terminal windows in the project folder and start the components in this order:

```bash
# Terminal 1
python3 receiver.py

# Terminal 2
python3 channel.py

# Terminal 3
python3 sender.py
```

The recovered image is saved in the `output/` folder.

## Running the tests

```bash
python3 test_codec.py
```

## Tech stack

Python, reedsolo, Pillow, socket programming

## Limitations

- Reed-Solomon corrects a limited number of byte errors per block. Heavier corruption than the code can handle will leave visible damage.
- This is an educational demo and is not optimised for production use.