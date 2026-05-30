import os
import whisper


_model_cache = {}


def _get_model(model_name: str):
    if model_name not in _model_cache:
        _model_cache[model_name] = whisper.load_model(model_name)
    return _model_cache[model_name]


def transcribe(audio_path: str, model_name: str, output_path: str) -> None:
    """Transcribe audio file and write plain text transcript to output_path."""
    model = _get_model(model_name)
    result = model.transcribe(audio_path)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(result["text"].strip())
