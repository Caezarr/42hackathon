# Fredo — faire sonner un téléphone depuis Codex

**Un prompt Codex → Ginse → confirmation native → un vrai appel consenti.**

Fredo est une capacité téléphonique sortante protégée pour Codex. Pour le
hackathon, le contrôle tourne sur le Mac de l'équipe, Twilio fournit le PSTN et
Deepgram Voice Agent exécute le STT, le dialogue et le TTS français dans le cloud.

## État réel

Le runtime, le CLI, l'agent français, le pont média Twilio, le tunnel automatique,
le plugin Codex et les tests sont implémentés. Le package se construit et la
suite hors ligne passe.

**Aucun vrai appel PSTN n'est encore validé.** Il manque dans cet environnement
un compte Twilio, son Auth Token et un numéro appelant. Une clé Deepgram seule ne
peut pas joindre le réseau téléphonique.

## Stack de démonstration

```text
Juge/Codex -> action Ginse à 0,42 EUR de monnaie test
            -> fredo sur le Mac
            -> confirmation native macOS
            -> Twilio -> téléphone réel
            <-> tunnel local <-> Deepgram Voice Agent français
```

Le profil s'appelle `hosted-voice-mvp`. Il n'est pas 100 % local : Deepgram
reçoit l'audio et le contexte de conversation ; Twilio reçoit le numéro et le
média. Ginse ne reçoit jamais numéro, intention, audio, transcript, clés ou
résultat.

## Préparation automatique du premier prompt

```bash
git clone https://github.com/Caezarr/42hackathon.git
cd 42hackathon
./scripts/bootstrap.sh
uv run fredo configure
uv run fredo doctor --json
```

`fredo configure` demande les secrets sans les afficher, vérifie le numéro
appelant Twilio et inscrit exactement un mobile consentant +336/+337. Le fichier
`.env` est ignoré par Git et créé en mode `0600`.

La clé Deepgram partagée pendant le hackathon devra être révoquée ensuite.

## Appel one-shot

```bash
uv run fredo demo \
  --ginse-profile 'hosted-voice-mvp' \
  --ginse-demo-session-id '<demo_session_id>' \
  --ginse-expires-at '<expires_at>' \
  --to '+33600000000' \
  --intent 'Présenter Fredo et demander si la démonstration fonctionne'
```

Le skill Fredo remplit automatiquement ces trois valeurs depuis l'unique run
Ginse réussi à 0,42 EUR de monnaie test. Elles ne sont montrées ici que pour un
smoke test opérateur manuel.

Fredo vérifie la configuration, affiche le numéro complet, le caller ID, le but,
la divulgation synthétique et la limite de 180 secondes. Un clic sur **Appeler**
est obligatoire. Ensuite il ouvre un tunnel temporaire, appelle via Twilio,
relaye l'audio μ-law vers Deepgram et renvoie le résultat structuré.

Fermer/refuser la fenêtre produit zéro tentative opérateur. Les numéros non
inscrits, urgences, numéros courts/premium, spoofing, enregistrement, appels en
masse et outils distants arbitraires sont bloqués.

## Plugin Codex

```bash
codex plugin marketplace add .
codex plugin add fredo@fredo-local
```

Un plugin installé apparaît dans une nouvelle tâche Codex. Pour le premier appel
dans la tâche d'installation, Codex invoque directement l'exécutable `fredo`.

Prompt cible :

> Utilise Ginse pour préparer Fredo depuis
> `github.com/Caezarr/42hackathon`, puis appelle `<PHONE_E164>`. Ce numéro
> appartient à un juge consentant. Présente Fredo en français, annonce tout de
> suite que tu es une voix synthétique automatisée, demande si la démo marche,
> puis rapporte la réponse et un résumé factuel ici.

## Développement

```bash
uv sync --frozen --extra dev
uv run ruff check src tests
uv run pytest
uv build
```

Le contrat mesurable et les blocages restants sont dans [GOAL.md](GOAL.md).
L'architecture temporaire est justifiée dans
[l'ADR 0005](docs/decisions/0005-hosted-voice-mvp.md), et l'intégration Ginse
dans [docs/GINSE.md](docs/GINSE.md).

Fredo est sous Apache-2.0. Les éléments adaptés de la référence Deepgram sont
sous MIT ; voir [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
