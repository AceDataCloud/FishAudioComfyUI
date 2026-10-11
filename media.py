"""Bounded Ace CDN media decoding for ComfyUI native types."""

from __future__ import annotations

from io import BytesIO
import time
from urllib.parse import urlparse

import requests

MEDIA_HOSTS = {"cdn.acedata.cloud", "cdn.acedata2.cloud", "platform.cdn.acedata.cloud",
               "platform2.cdn.acedata.cloud"}
MAX_MEDIA_BYTES = 128 * 1024 * 1024


class MediaError(RuntimeError):
    """A media error without response bodies or URL details."""


def download_media(url: str) -> bytes:
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname not in MEDIA_HOSTS or parsed.username or parsed.password:
        raise MediaError("Media URL must be an Ace Data Cloud HTTPS CDN link.")
    for attempt in range(3):
        try:
            with requests.get(url, stream=True, timeout=(10, 90), allow_redirects=False) as response:
                if response.status_code != 200:
                    raise MediaError(f"Media download returned HTTP {response.status_code}.")
                claimed = int(response.headers.get("Content-Length", "0"))
                if claimed > MAX_MEDIA_BYTES:
                    raise MediaError("Media exceeds the 128 MiB limit.")
                chunks = []
                size = 0
                for chunk in response.iter_content(1024 * 1024):
                    size += len(chunk)
                    if size > MAX_MEDIA_BYTES:
                        raise MediaError("Media exceeds the 128 MiB limit.")
                    chunks.append(chunk)
            break
        except requests.RequestException as exc:
            if attempt < 2:
                time.sleep(0.5 * (attempt + 1))
                continue
            raise MediaError(f"Media download failed ({type(exc).__name__}).") from None
    if not size:
        raise MediaError("Media download was empty.")
    return b"".join(chunks)


def as_image(raw: bytes):
    import numpy as np
    import torch
    from PIL import Image, UnidentifiedImageError

    try:
        with Image.open(BytesIO(raw)) as image:
            image.load()
            array = np.asarray(image.convert("RGB"), dtype=np.float32).copy() / 255.0
    except (UnidentifiedImageError, OSError, ValueError):
        raise MediaError("The media link does not contain a valid image.") from None
    return torch.from_numpy(array).unsqueeze(0)


def as_video(raw: bytes):
    from comfy_api.latest import VideoFromFile
    return VideoFromFile(BytesIO(raw))


def as_audio(raw: bytes):
    import av
    import torch

    try:
        with av.open(BytesIO(raw)) as container:
            if not container.streams.audio:
                raise MediaError("The media link contains no audio stream.")
            stream = container.streams.audio[0]
            sample_rate = stream.codec_context.sample_rate
            channels = stream.channels
            frames = []
            for frame in container.decode(streams=stream.index):
                samples = torch.from_numpy(frame.to_ndarray())
                if samples.shape[0] != channels:
                    samples = samples.view(-1, channels).t()
                if samples.dtype == torch.int16:
                    samples = samples.float() / (2 ** 15)
                elif samples.dtype == torch.int32:
                    samples = samples.float() / (2 ** 31)
                elif not samples.is_floating_point():
                    raise MediaError("Unsupported audio sample format.")
                frames.append(samples)
            if not frames:
                raise MediaError("The media link contains no audio frames.")
            return {"waveform": torch.cat(frames, dim=1).unsqueeze(0), "sample_rate": sample_rate}
    except (av.error.FFmpegError, OSError, ValueError):
        raise MediaError("The media link does not contain valid audio.") from None
