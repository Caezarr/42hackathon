# Moment 5 — Intégration comme fonctionnalité Codex

Date : 18 juillet 2026

## Décision

Le système d’appel n’est pas une application séparée pilotée occasionnellement par Codex. Il doit être construit et distribué comme une **fonctionnalité installable dans Codex**.

La surface retenue est un plugin Codex local composé d’une skill et d’un serveur MCP local.

## Pourquoi un plugin

Le plugin regroupe dans une seule unité installable :

- les instructions de l’agent ;
- les outils d’appel ;
- les règles de sécurité ;
- les scripts locaux ;
- la configuration du serveur MCP ;
- les prompts et modèles de mandat ;
- la documentation utilisateur.

L’utilisateur reste dans une tâche Codex du début à la fin. Il n’a pas besoin d’ouvrir un dashboard séparé.

## Structure cible

```text
codex-admin-caller/
├── .codex-plugin/
│   └── plugin.json
├── skills/
│   └── administrative-calls/
│       ├── SKILL.md
│       └── references/
│           ├── mandate-schema.md
│           └── safety-policy.md
├── mcp-server/
│   ├── src/
│   │   ├── server.py
│   │   ├── tools.py
│   │   └── policy.py
│   └── pyproject.toml
├── voice-runtime/
│   ├── pipeline.py
│   ├── stt.py
│   ├── dialogue.py
│   ├── tts.py
│   └── telephony.py
├── prompts/
│   └── administrative-agent.md
├── models/
│   └── README.md
├── call-data/
│   ├── cases/
│   └── results/
├── AGENTS.md
├── LICENSE
└── README.md
```

Les poids de modèles ne sont pas commités dans Git. Le plugin vérifie leur présence locale et indique comment les installer.

## Outils MCP exposés à Codex

```text
prepare_call
preview_call
confirm_call
start_call
get_call_status
get_call_result
stop_call
```

### Séparation des responsabilités

`prepare_call`

- transforme la demande en mandat structuré ;
- ne déclenche aucun appel.

`preview_call`

- affiche le destinataire, l’objectif et les données autorisées ;
- affiche les actions interdites et les conditions d’escalade.

`confirm_call`

- exige une validation explicite de l’utilisateur ;
- génère un jeton local à durée de vie courte, lié au numéro et au mandat.

`start_call`

- refuse l’appel sans jeton valide ;
- refuse un numéro ou un mandat différent de ceux confirmés ;
- lance le pipeline vocal local.

`get_call_result`

- renvoie le résumé, les faits obtenus et les prochaines étapes ;
- lit uniquement les résultats stockés localement.

## Architecture d’exécution

```text
Conversation dans Codex
        │
        ▼
Skill administrative-calls
        │
        ▼
Outils du serveur MCP local
        │
        ▼
Moteur vocal open source local
 Pipecat + STT + LLM + TTS
        │
        ▼
Asterisk local
        │
        ├── Démo : client SIP local
        └── Réel : trunk SIP ou passerelle GSM
```

## Exécution locale de Codex

Pour que la contrainte « tout local » englobe aussi le raisonnement principal, la démonstration doit utiliser Codex CLI avec un fournisseur local et un modèle open-weight.

Chemin recommandé :

```text
Codex CLI
  → profil local
  → serveur compatible OpenAI sur localhost
  → gpt-oss-20b ou modèle Apache-2.0 plus petit
```

Le dépôt officiel `openai/gpt-oss` documente un profil Codex utilisant un serveur local. Le manuel Codex indique aussi que les serveurs MCP et les réglages durables appartiennent à la configuration Codex partagée.

L’intégration dans l’application desktop Codex pourra utiliser le même plugin. Cependant, l’affirmation « aucune inférence cloud » devra être validée dans cette surface avant la démo ; le chemin garanti pour le MVP reste Codex CLI avec le profil local.

## Règles de sécurité imposées par le plugin

- `start_call` est une action soumise à confirmation.
- Le numéro confirmé est immuable.
- Le mandat confirmé est immuable.
- Aucun appel en masse.
- Aucun numéro d’urgence.
- Aucun clonage de voix tierce.
- Annonce obligatoire du caractère automatisé et synthétique.
- Aucun mot de passe, OTP, paiement ou changement bancaire.
- Données et transcriptions stockées uniquement dans `call-data/`.
- Enregistrement audio désactivé par défaut.
- Bouton logique d’arrêt disponible via `stop_call`.

Ces règles doivent être codées dans `policy.py`, pas uniquement écrites dans le prompt.

## Critère produit

La feature est considérée comme intégrée à Codex si l’utilisateur peut accomplir ce parcours sans quitter sa tâche :

```text
« Prépare l’appel »
→ aperçu du mandat
→ confirmation
→ appel
→ statut
→ compte rendu
```

Une commande terminal lancée manuellement ou une interface web externe ne suffit pas à remplir ce critère.

## Priorité d’implémentation

1. Créer le squelette du plugin Codex.
2. Exposer un serveur MCP factice avec les sept outils.
3. Vérifier que Codex découvre et appelle ces outils.
4. Implémenter la confirmation locale.
5. Raccorder le pipeline vocal local.
6. Raccorder Asterisk et le client SIP.
7. Remplacer les réponses factices par les résultats réels.

## Sources

- [OpenAI gpt-oss — utilisation locale avec Codex](https://github.com/openai/gpt-oss)
- [OpenAI Developers — cas d’usage « Create a CLI Codex can use »](https://developers.openai.com/codex/use-cases)
- Manuel Codex local actualisé le 18 juillet 2026 : configuration durable, serveurs MCP et plugins.

