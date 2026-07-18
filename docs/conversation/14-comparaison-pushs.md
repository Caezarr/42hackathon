# Moment 14 — Comparaison du push du coéquipier et de notre push

Date : 18 juillet 2026

## Lots comparés

### Push du coéquipier

Référence principale :

- merge `9d9eea3` ;
- commits `7cec4f9`, `6f207f3` et `9074864`.

Volume :

- 16 fichiers ;
- 1 309 insertions ;
- 1 suppression.

### Notre push

Référence finale avant ce comparatif :

- `974ef8e`.

Volume ajouté après le merge du coéquipier :

- 14 fichiers ;
- 1 038 insertions ;
- uniquement `docs/conversation/*.md`.

## Nature des contributions

| Aspect | Push du coéquipier | Notre push |
|---|---|---|
| Nature | Squelette de dépôt produit | Journal de décisions et roadmap |
| Code exécutable | Script de clonage des upstreams uniquement | Aucun code exécutable |
| Architecture | Appliance auto-hébergée détaillée | Plugin Codex + MCP + pipeline local |
| Téléphonie | LiveKit SIP, trunk, GSM, Android Bluetooth | Asterisk/SIP vers le vrai téléphone du jury |
| IA locale | LocalAI, puis vLLM/Speaches/Kokoro | gpt-oss ou Qwen, STT local, Chatterbox/OpenVoice |
| Codex | MCP local, mais interface Codex décrite comme hébergée | Codex CLI avec fournisseur local |
| Distribution | Bootstrap reproductible multi-profils | MVP vertical de six heures |
| Marketplace | Ginse obligatoire pour la démo | Hors du chemin critique |
| Clonage vocal | Non spécifié comme exigence implémentée | Fonction centrale avec consentement |
| Sécurité | Politiques détaillées, identité vérifiée, quotas | Mandat, confirmation, interdictions et disclosure |

## Points parfaitement alignés

Les deux travaux partagent les décisions fondamentales suivantes :

- fonctionnalité commandée depuis Codex ;
- serveur MCP local ;
- Pipecat pour le pipeline vocal ;
- STT, LLM et TTS locaux ;
- transport téléphonique possédé par l’utilisateur ;
- trunk SIP ou SIM pour atteindre le réseau public ;
- aucune usurpation de caller ID ;
- confirmation obligatoire avant l’appel ;
- stockage local ;
- absence de backend central d’appels ;
- appel réel vers un numéro contrôlé pendant la démonstration.

## Apports solides du coéquipier

### Structure du dépôt

Le push apporte les documents canoniques qui manquaient :

- `README.md` et `README.fr.md` ;
- `AGENTS.md` ;
- `SECURITY.md` ;
- `CONTRIBUTING.md` ;
- architecture, téléphonie, bootstrap et plan du hackathon ;
- décisions d’architecture ;
- registre de dépendances et licences.

### Sécurité téléphonique

La politique est plus complète que notre première roadmap :

- identité d’appelant vérifiée ;
- blocage des urgences, numéros premium et short codes ;
- limites de durée, concurrence et dépenses ;
- audit local ;
- idempotence des appels ;
- enregistrement désactivé par défaut.

### Reproductibilité

Le fichier `deploy/upstreams.lock.json` fixe les repos, commits et licences de LiveKit, Pipecat, LocalAI et des composants optionnels.

### Vrai réseau téléphonique

Le plan reconnaît correctement qu’un laptop derrière NAT ou CGNAT peut nécessiter un edge Linux public relié par WireGuard.

## Écarts importants avec nos décisions

### 1. Codex hébergé contre Codex local

Le push du coéquipier indique que Codex reste une interface hébergée.

Notre décision actuelle impose Codex CLI avec un fournisseur local afin que le raisonnement principal reste local.

Décision à appliquer : remplacer dans les documents canoniques la frontière « Codex hébergé » par le profil Codex CLI local retenu pour la démonstration.

### 2. Ginse obligatoire

Le push rend Ginse obligatoire pour la démonstration.

Cette dépendance :

- ajoute une URL publique et une publication marketplace ;
- n’est pas nécessaire pour prouver la feature Codex ;
- ajoute du risque et du travail hors du chemin critique ;
- n’a pas été demandée dans notre périmètre.

Décision recommandée : garder Ginse strictement optionnel et le sortir de la definition of done du hackathon.

### 3. Clonage vocal absent

Le produit initial repose sur une voix clonée à partir d’un échantillon consenti.

Le push du coéquipier prévoit du TTS local avec LocalAI ou Kokoro, mais ne définit ni moteur de clonage, ni onboarding vocal, ni critère de similarité.

Décision à appliquer : ajouter un composant de clonage local et un test de consentement. Une voix générique reste le fallback.

### 4. Topologie trop lourde pour six heures

Le chemin de référence demande :

- un Mac Apple Silicon avec 24 Go ;
- Docker Desktop ;
- un serveur Linux public ;
- TLS ;
- WireGuard ;
- LiveKit ;
- LiveKit SIP ;
- Postgres ;
- Valkey ;
- un trunk SIP ;
- Ginse.

Cette architecture est crédible pour un produit, mais trop ambitieuse pour un MVP de six heures.

Décision recommandée : construire d’abord un seul chemin vertical Codex → MCP → voix locale → trunk SIP → téléphone du jury. Ajouter le control plane durable, le bootstrap multi-profils et Ginse après le premier appel réussi.

## État réel d’implémentation

Malgré le volume documentaire, le README indique explicitement que le dialer de bout en bout n’est pas encore implémenté.

À ce stade :

- le coéquipier a défini une architecture et un plan de build ;
- nous avons défini les décisions produit et contraintes ;
- aucun des deux lots ne fournit encore l’appel fonctionnel ;
- le prochain travail doit être du code exécutable, pas une nouvelle couche de documentation.

## Synthèse

Le push du coéquipier doit devenir la base canonique du dépôt parce qu’il structure correctement le produit, la sécurité, la téléphonie et les dépendances.

Notre travail doit servir à le corriger et le focaliser :

1. Codex CLI local ;
2. Ginse optionnel ;
3. clonage vocal explicite ;
4. vrai appel du jury comme critère principal ;
5. réduction drastique du chemin de démo ;
6. passage immédiat à l’implémentation.
