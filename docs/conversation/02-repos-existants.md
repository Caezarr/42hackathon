# Moment 2 — Repos existants et choix technique

Date : 18 juillet 2026

> Décision remplacée : ElevenLabs et Twilio ne font plus partie du cœur du MVP depuis l’adoption de l’architecture entièrement locale et open source au [moment 4](./04-architecture-locale-open-source.md). Cette note reste conservée comme historique de décision.

## Repos identifiés

### ElevenLabs CLI

- Repo : [elevenlabs/cli](https://github.com/elevenlabs/cli)
- Rôle : créer, configurer et versionner les agents vocaux.
- Atouts : officiel, licence MIT, templates `minimal`, `voice-only` et `customer-service`.
- Décision : l’utiliser pour gérer la configuration de l’agent.

### ElevenLabs outbound calls

- Référence : [elevenlabs/skills — outbound calls](https://github.com/elevenlabs/skills/blob/main/agents/references/outbound-calls.md)
- Rôle : déclencher un appel Twilio avec un agent ElevenLabs.
- Atouts : variables dynamiques, surcharge du prompt, choix du `voice_id`, retour du `conversation_id` et du `callSid`.
- Décision : utiliser cet appel API dans le CLI local.

### OpenAI Realtime Twilio Demo

- Repo : [openai/openai-realtime-twilio-demo](https://github.com/openai/openai-realtime-twilio-demo)
- Rôle : interface Next.js, affichage des événements et des transcriptions.
- Atouts : officiel, licence MIT, frontend déjà construit.
- Limite : pas de clonage personnalisé natif et parcours principalement entrant.
- Décision : reprendre éventuellement des idées d’interface, sans en faire le cœur du MVP.

### Twilio Call GPT

- Repo : [twilio-labs/call-gpt](https://github.com/twilio-labs/call-gpt)
- Rôle : toolkit complet autour de Twilio Media Streams.
- Atouts : appel sortant, fonctions, tests et intégration ElevenLabs documentée.
- Limite : architecture plus complexe que l’intégration native ElevenLabs.
- Décision : garder comme référence et solution de repli.

### CallAgent

- Repo : [programmerraja/CallAgent](https://github.com/programmerraja/CallAgent)
- Rôle : raccorder un appel Twilio sortant à un agent ElevenLabs.
- Atouts : WebSockets et interruptions déjà traités.
- Limite : repo communautaire et licence à vérifier.
- Décision : référence technique uniquement.

### Bolna

- Repo : [bolna-ai/bolna](https://github.com/bolna-ai/bolna)
- Rôle : plateforme complète d’agents vocaux.
- Limite : plusieurs services, Docker et Redis.
- Décision : hors périmètre des six heures.

## Choix retenu

```text
elevenlabs/cli
        +
API officielle ElevenLabs outbound-call
        +
petit CLI admin-call appelé par Codex
        +
frontend minimal facultatif
```

Le projet ne forkera pas une grosse plateforme. Il utilisera les composants officiels les plus courts afin de maximiser les chances d’obtenir un appel fonctionnel dans les deux premières heures.

