from __future__ import annotations

import os
import threading
from pathlib import Path
from uuid import uuid4

from .config import (
    CHATTERBOX_MODEL_FILES,
    CHATTERBOX_MODEL_ID,
    CHATTERBOX_MODEL_REVISION,
    model_dir,
    output_dir,
    state_dir,
)

os.environ.setdefault("HF_HOME", str(state_dir() / "huggingface"))
os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")


class VoiceCloneEngine:
    def __init__(self) -> None:
        self._model = None
        self._device: str | None = None
        self._lock = threading.Lock()

    @property
    def device(self) -> str:
        if self._device is None:
            self._device = self._select_device()
        return self._device

    @staticmethod
    def _select_device() -> str:
        requested = os.getenv("VOICE_CLONE_DEVICE", "auto").lower()
        allowed = {"auto", "cpu", "cuda", "mps"}
        if requested not in allowed:
            raise ValueError(f"VOICE_CLONE_DEVICE doit être l'une de ces valeurs : {sorted(allowed)}")

        import torch

        if requested != "auto":
            if requested == "cuda" and not torch.cuda.is_available():
                raise RuntimeError("CUDA a été demandé mais aucun GPU CUDA n'est disponible.")
            if requested == "mps" and not torch.backends.mps.is_available():
                raise RuntimeError("MPS a été demandé mais n'est pas disponible.")
            return requested
        if torch.cuda.is_available():
            return "cuda"
        if torch.backends.mps.is_available():
            return "mps"
        return "cpu"

    def _load_model(self):
        if self._model is not None:
            return self._model

        from chatterbox.mtl_tts import ChatterboxMultilingualTTS
        from huggingface_hub import snapshot_download

        destination = model_dir()
        destination.mkdir(parents=True, exist_ok=True)
        snapshot_download(
            repo_id=CHATTERBOX_MODEL_ID,
            repo_type="model",
            revision=CHATTERBOX_MODEL_REVISION,
            allow_patterns=list(CHATTERBOX_MODEL_FILES),
            local_dir=destination,
            local_files_only=os.getenv("VOICE_CLONE_OFFLINE", "0") == "1",
        )
        self._model = ChatterboxMultilingualTTS.from_local(
            destination,
            device=self.device,
            t3_model="v3",
        )
        return self._model

    def generate(self, reference_path: Path, text: str) -> Path:
        with self._lock:
            model = self._load_model()
            waveform = model.generate(
                text,
                language_id="fr",
                audio_prompt_path=str(reference_path),
                exaggeration=0.5,
                cfg_weight=0.5,
            )

            import soundfile as sf

            destination_dir = output_dir()
            destination_dir.mkdir(parents=True, exist_ok=True)
            destination = destination_dir / f"phrase-{uuid4().hex[:12]}.wav"
            sf.write(
                destination,
                waveform.squeeze().detach().cpu().numpy(),
                model.sr,
                subtype="PCM_16",
            )
            return destination
