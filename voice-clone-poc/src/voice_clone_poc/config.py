from __future__ import annotations

import os
from pathlib import Path


CHATTERBOX_SOURCE_REVISION = "65b18437192794391a0308a8f705b1e33e633948"
CHATTERBOX_MODEL_ID = "ResembleAI/chatterbox"
CHATTERBOX_MODEL_REVISION = "5bb1f6ee58e50c3b8d408bc82a6d3740c2db6e18"
CHATTERBOX_MODEL_FILES = (
    "ve.pt",
    "t3_mtl23ls_v3.safetensors",
    "s3gen.pt",
    "grapheme_mtl_merged_expanded_v1.json",
    "conds.pt",
    "Cangjie5_TC.json",
)


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def state_dir() -> Path:
    configured = os.getenv("VOICE_CLONE_STATE_DIR")
    if configured:
        return Path(configured).expanduser().resolve()
    return project_root().parent / ".local-state" / "voice-clone"


def model_dir() -> Path:
    return state_dir() / "models" / "chatterbox-v3"


def output_dir() -> Path:
    return state_dir() / "outputs"
