# Moment 4 — Architecture entièrement locale et open source

Date : 18 juillet 2026

## Nouvelle contrainte

Tous les composants applicatifs doivent :

- tourner sur la machine locale ;
- utiliser du code open source ;
- fonctionner sans API d’IA propriétaire ;
- conserver les échantillons de voix, transcriptions et dossiers localement ;
- rester utilisables sans connexion Internet après le téléchargement initial des dépendances et des modèles.

Cette décision remplace l’architecture ElevenLabs + Twilio proposée précédemment.

## Architecture retenue

```text
Codex CLI --oss
        │
        ▼
Ollama ou llama.cpp + Qwen3 8B
        │
        ▼
CLI admin-call + mandat confirmé
        │
        ▼
Pipecat — pipeline vocal local
   ├── Silero VAD
   ├── whisper.cpp — transcription
   ├── Qwen3 8B — dialogue et outils
   └── Chatterbox Multilingual — voix clonée française
        │
        ▼
Asterisk — PBX SIP local
        │
        ▼
Linphone — téléphone logiciel de démonstration
```

## Composants

| Besoin | Composant | Licence | Motif |
|---|---|---|---|
| Orchestration Codex | [OpenAI Codex CLI](https://github.com/openai/codex) | Apache-2.0 | Le CLI est open source et accepte des fournisseurs locaux en mode `--oss` |
| Serveur LLM | [Ollama](https://github.com/ollama/ollama) ou [llama.cpp](https://github.com/ggml-org/llama.cpp) | MIT | Inférence locale et API compatible OpenAI |
| Modèle conversationnel | [Qwen3 8B](https://github.com/QwenLM/Qwen3) | Apache-2.0 | Bon compromis entre français, outils, vitesse et mémoire |
| Pipeline temps réel | [Pipecat](https://github.com/pipecat-ai/pipecat) | BSD-2-Clause | Pipeline vocal modulaire avec transports et services locaux |
| Reconnaissance vocale | [whisper.cpp](https://github.com/ggml-org/whisper.cpp) | MIT | STT multilingue local, CPU ou GPU |
| Synthèse et clonage | [Chatterbox](https://github.com/resemble-ai/chatterbox) | MIT | Clonage vocal local et support du français |
| PBX SIP | [Asterisk](https://github.com/asterisk/asterisk) | GPL-2.0 | Téléphonie SIP locale et appels sortants vers un trunk facultatif |
| Téléphone de démo | [Linphone](https://github.com/BelledonneCommunications/linphone-desktop) | GPL-3.0 | Softphone SIP local et open source |

## Codex réellement local

Codex CLI est publié sous licence Apache-2.0. Son mode `--oss` permet de choisir Ollama ou LM Studio comme fournisseur local. Pour respecter strictement la contrainte, il ne faut pas se connecter avec ChatGPT ni utiliser une clé API OpenAI pendant la démonstration.

Configuration logique :

```toml
oss_provider = "ollama"
model = "qwen3:8b"
```

Lancement :

```text
codex --oss --local-provider ollama
```

## Deux modes téléphoniques

### Mode hackathon — 100 % local

- Asterisk tourne localement.
- Deux comptes SIP locaux sont créés.
- L’agent appelle un Linphone installé sur un téléphone ou un ordinateur du réseau local.
- Aucun opérateur, cloud ou numéro public n’est utilisé.

Ce mode satisfait intégralement la contrainte et doit être utilisé pour la démonstration.

### Mode numéro réel — logiciel local, réseau externe

Pour joindre un numéro de téléphone public, Asterisk doit sortir par :

- un trunk SIP fourni par un opérateur ; ou
- un modem GSM local contenant une carte SIM.

Le traitement IA reste local, mais le réseau téléphonique ne peut pas être open source : un opérateur est nécessaire pour accéder au PSTN. Cette extension est hors périmètre du MVP de six heures.

## Roadmap révisée de six heures

| Temps | Travail | Critère de sortie |
|---|---|---|
| 0:00–0:40 | Vérifier GPU/RAM, installer Ollama, télécharger Qwen3 | Une réponse locale est produite hors API cloud |
| 0:40–1:20 | Installer Pipecat et brancher le micro local | Le pipeline reçoit et rejoue de l’audio |
| 1:20–2:10 | Brancher whisper.cpp et Silero VAD | La parole française est transcrite localement |
| 2:10–3:00 | Brancher Chatterbox avec un échantillon consenti | Une phrase française est produite dans la voix clonée |
| 3:00–4:00 | Connecter STT → LLM → TTS dans Pipecat | Conversation vocale locale bidirectionnelle |
| 4:00–4:50 | Configurer Asterisk et deux comptes SIP | L’agent fait sonner Linphone sur le LAN |
| 4:50–5:30 | Ajouter le CLI `admin-call`, le mandat et la confirmation | Codex CLI peut déclencher l’appel local |
| 5:30–6:00 | Tests, mesure de latence et démo de secours | Démonstration reproductible hors Internet |

## Règles de coupure

- Si Chatterbox ne tient pas la latence à H+3, utiliser Piper avec une voix standard locale pour sécuriser la boucle, puis montrer le clone hors temps réel.
- Si Asterisk n’est pas opérationnel à H+4:30, faire la démonstration via le transport audio local de Pipecat.
- Si Qwen3 8B est trop lent, descendre à Qwen3 4B.
- Ne pas ajouter LiveKit, Redis, Docker ou une interface web avant que l’appel SIP local fonctionne.

## Definition of done révisée

- Internet peut être coupé avant la démonstration.
- Aucun audio ou dossier n’est envoyé vers une API externe.
- Codex CLI utilise un modèle local.
- La transcription, le dialogue et la synthèse tournent localement.
- L’appel fait sonner un client SIP local.
- La voix clonée provient d’un échantillon consenti.
- Le système annonce explicitement qu’il s’agit d’un assistant automatisé à voix synthétique.
- Un résumé local est généré après l’appel.

## Sources

- [Codex CLI — dépôt Apache-2.0](https://github.com/openai/codex)
- [Codex — mode OSS et fournisseurs locaux](https://developers.openai.com/codex/config-advanced#oss-mode-local-providers)
- [Pipecat](https://github.com/pipecat-ai/pipecat)
- [whisper.cpp](https://github.com/ggml-org/whisper.cpp)
- [Chatterbox Multilingual](https://github.com/resemble-ai/chatterbox)
- [Qwen3](https://github.com/QwenLM/Qwen3)
- [llama.cpp](https://github.com/ggml-org/llama.cpp)
- [Asterisk](https://github.com/asterisk/asterisk)
- [Linphone](https://github.com/BelledonneCommunications/linphone-desktop)
