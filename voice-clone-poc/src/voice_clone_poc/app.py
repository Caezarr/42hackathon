from __future__ import annotations

import os

os.environ.setdefault("GRADIO_ANALYTICS_ENABLED", "False")

import gradio as gr

from .engine import VoiceCloneEngine
from .validation import InputError, require_consent, validate_reference, validate_text


REFERENCE_SCRIPT = """Bonjour, je parle ici avec ma voix naturelle, sans forcer le rythme ni changer mon accent. Ce matin, j'ai pris un café chaud près de la grande fenêtre, puis j'ai vérifié quelques chiffres précis : douze, vingt-trois, quarante-huit et soixante-dix. Pourquoi cette petite phrase paraît-elle si simple ? Parce qu'elle mélange des sons clairs, graves, doux et rapides. Je peux poser une question, marquer une pause, puis terminer tranquillement. Voilà, cet échantillon représente ma manière habituelle de parler."""


def build_demo(engine: VoiceCloneEngine | None = None) -> gr.Blocks:
    clone_engine = engine or VoiceCloneEngine()

    def synthesize(reference: str | None, text: str, consent: bool, progress=gr.Progress()):
        try:
            require_consent(consent)
            reference_path = validate_reference(reference)
            normalized_text = validate_text(text)
            progress(0.1, desc="Chargement local du modèle…")
            destination = clone_engine.generate(reference_path, normalized_text)
            return str(destination), f"Terminé localement sur `{clone_engine.device}`. Audio synthétique watermarké."
        except InputError as exc:
            raise gr.Error(str(exc)) from exc
        except Exception as exc:
            raise gr.Error(f"La génération a échoué : {exc}") from exc

    with gr.Blocks(title="Clone vocal local") as demo:
        gr.Markdown(
            "# Clone vocal local\n"
            "Enregistre ou charge ta propre voix, écris une phrase, puis génère-la localement avec Chatterbox Multilingual V3."
        )
        with gr.Row():
            with gr.Column():
                reference = gr.Audio(
                    label="Échantillon WAV (idéalement 10 à 30 secondes)",
                    sources=["microphone", "upload"],
                    type="filepath",
                    format="wav",
                )
                gr.Markdown(
                    "**Texte conseillé à lire :**\n\n"
                    f"> {REFERENCE_SCRIPT}\n\n"
                    "Parle naturellement, dans une pièce calme, sans musique ni réverbération. "
                    "Le modèle utilise surtout les dix premières secondes."
                )
            with gr.Column():
                text = gr.Textbox(
                    label="Phrase à prononcer avec la voix clonée",
                    placeholder="Bonjour, ceci est une démonstration locale de ma voix.",
                    lines=4,
                    max_length=400,
                )
                consent = gr.Checkbox(
                    label="Je confirme que cette voix est la mienne ou que j'ai son autorisation explicite."
                )
                generate_button = gr.Button("Générer", variant="primary")
                output = gr.Audio(label="Résultat", type="filepath")
                status = gr.Markdown()

        generate_button.click(
            synthesize,
            inputs=[reference, text, consent],
            outputs=[output, status],
            concurrency_limit=1,
        )
        gr.Markdown(
            "La première génération télécharge les poids épinglés du modèle. "
            "Les suivantes peuvent fonctionner sans réseau avec `VOICE_CLONE_OFFLINE=1`. "
            "Aucun échantillon ni texte n'est envoyé à une API de synthèse vocale."
        )
    return demo


def main() -> None:
    port = int(os.getenv("VOICE_CLONE_PORT", "7860"))
    build_demo().launch(server_name="127.0.0.1", server_port=port, share=False, inbrowser=True)


if __name__ == "__main__":
    main()
