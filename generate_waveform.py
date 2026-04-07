"""
generate_waveform.py
────────────────────
Pre-computes waveform thumbnail CSVs from WAV files so the browser can load
them directly instead of decoding audio with the Web Audio API.

Output format (one file per audio file, e.g. audio.wav → audio_waveform.csv):

    # sr=500,duration=185.237
    -0.012345,0.023456
    -0.034567,0.045678
    ...

  • First line: metadata comment (sample-rate of the thumbnail, total duration)
  • Remaining lines: min,max amplitude per thumbnail chunk
  • Thumbnail SR matches the browser's buildWaveformThumbnail constant (500 chunks/sec)

Usage:
    python generate_waveform.py                 # processes all *.wav in current dir
    python generate_waveform.py audio.wav       # process specific file(s)
    python generate_waveform.py audio.wav practice.wav
"""

import sys
import os
import wave
import struct
import math

THUMBNAIL_SR = 500   # must match the JS constant (500 chunks/sec)


def read_wav_mono(path: str):
    """Return (samples: list[float], native_sr: int, duration: float)."""
    with wave.open(path, 'rb') as wf:
        n_channels   = wf.getnchannels()
        sample_width = wf.getsampwidth()   # bytes per sample per channel
        native_sr    = wf.getframerate()
        n_frames     = wf.getnframes()
        duration     = n_frames / native_sr
        raw          = wf.readframes(n_frames)

    # Decode raw bytes to floats in [-1, 1]
    if sample_width == 1:
        # 8-bit WAV is unsigned (0–255), centre at 128
        fmt    = f'<{n_frames * n_channels}B'
        vals   = struct.unpack(fmt, raw)
        mono   = [(v - 128) / 128.0 for v in vals[::n_channels]]
        return mono, native_sr, duration

    if sample_width == 2:
        fmt, scale = f'<{n_frames * n_channels}h', 32768.0
    elif sample_width == 4:
        fmt, scale = f'<{n_frames * n_channels}i', 2147483648.0
    else:
        raise ValueError(f'Unsupported sample width: {sample_width} bytes')

    vals = struct.unpack(fmt, raw)

    # Mix down to mono by averaging channels
    if n_channels == 1:
        mono = [v / scale for v in vals]
    else:
        mono = [
            sum(vals[i * n_channels + ch] for ch in range(n_channels))
            / (n_channels * scale)
            for i in range(n_frames)
        ]

    return mono, native_sr, duration


def build_thumbnail(samples: list, native_sr: int):
    """
    Downsample to THUMBNAIL_SR chunks/sec, each chunk holding (min, max).
    Matches the browser's buildWaveformThumbnail logic exactly.
    """
    chunk_size = max(1, math.floor(native_sr / THUMBNAIL_SR))
    n_chunks   = math.ceil(len(samples) / chunk_size)

    mins, maxs = [], []
    for i in range(n_chunks):
        start = i * chunk_size
        end   = min(start + chunk_size, len(samples))
        chunk = samples[start:end]
        mins.append(min(chunk))
        maxs.append(max(chunk))

    return mins, maxs


def write_csv(path: str, mins, maxs, duration: float):
    with open(path, 'w', encoding='utf-8') as f:
        f.write(f'# sr={THUMBNAIL_SR},duration={duration:.6f}\n')
        for mn, mx in zip(mins, maxs):
            f.write(f'{mn:.6f},{mx:.6f}\n')
    print(f'  → wrote {len(mins)} chunks to {path}')


def process(wav_path: str):
    base     = os.path.splitext(wav_path)[0]
    out_path = base + '_waveform.csv'

    print(f'Processing {wav_path} ...')
    samples, native_sr, duration = read_wav_mono(wav_path)
    print(f'  native SR={native_sr} Hz, duration={duration:.3f}s, '
          f'{len(samples)} samples')

    mins, maxs = build_thumbnail(samples, native_sr)
    print(f'  thumbnail: {len(mins)} chunks at {THUMBNAIL_SR} chunks/sec')

    write_csv(out_path, mins, maxs, duration)


def main():
    targets = sys.argv[1:]
    if not targets:
        # Default: all *.wav files in the same directory as this script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        targets = [
            os.path.join(script_dir, f)
            for f in sorted(os.listdir(script_dir))
            if f.lower().endswith('.wav')
        ]

    if not targets:
        print('No WAV files found.')
        return

    for t in targets:
        process(t)

    print('Done.')


if __name__ == '__main__':
    main()
