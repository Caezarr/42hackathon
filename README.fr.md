# Fredo — le téléphone local de Codex

**On le découvre dans Ginse. On l'installe sur son Mac. On téléphone depuis Codex.**

Fredo est une capacité téléphonique générique et locale pour Codex. Une fois Fredo installé, une demande devient un appel réel, prévisualisé et confirmé, mené par des modèles tournant chez l'utilisateur, puis un résultat structuré revient dans la même tâche Codex.

Le moment hackathon est simple : partir de Ginse, installer Fredo localement et faire sonner le vrai téléphone d'un membre du jury depuis un numéro vérifié.

## État actuel

Le dépôt contient le contrat produit, l'architecture cible, les sources épinglées et la roadmap. L'appel de bout en bout n'est **pas encore implémenté**.

- [`GOAL.md`](GOAL.md) définit les critères mesurables de réussite.
- [`ROADMAP.md`](ROADMAP.md) ordonne le travail et les preuves attendues.

## Parcours

```text
Ginse
  -> plan de bootstrap Fredo versionné
  -> plugin et skill Codex
  -> CLI et daemon Fredo locaux
  -> IA vocale locale
  -> transport SIP de l'utilisateur
  -> téléphone réel
  -> résultat dans Codex
```

Ginse est la porte d'entrée, pas le backend d'appel. Il ne reçoit jamais le numéro, l'objectif de l'appel, les identifiants SIP, l'audio ou la transcription.

La première utilisation se fait en deux temps : une tâche de bootstrap part de Ginse et termine sur `fredo doctor`, puis une nouvelle tâche charge le plugin Fredo et réalise l'appel. Le petit provider HTTPS public de Ginse est obligatoire et hébergé par l'équipe ; il est distinct d'un éventuel edge télécom.

Chaque installation possède ses modèles, ses données, son compte SIP ou sa SIM, son identité d'appelant et sa facture télécom. Fredo n'opère aucune plateforme d'appels mutualisée.

## Intégration Codex

Fredo est distribué comme plugin Codex :

- une skill pilote le parcours utilisateur ;
- la CLI `fredo` est le contrat local canonique ;
- `fredod` gère les appels longs et l'état SQLite ;
- un adaptateur MCP STDIO peut fournir des outils typés, sans logique métier propre.

La démo utilise Codex CLI avec un fournisseur OSS local. Après bootstrap, aucun fournisseur hébergé de STT, LLM, TTS ou agent vocal n'est nécessaire.

## Machine de référence

Le seul profil obligatoire pendant le hackathon est le Mac inspecté : Apple M4 Pro, 24 Go de RAM, macOS 26.5, architecture `arm64`.

L'inférence tourne nativement via Metal/MLX. Docker Compose peut emballer LiveKit, SIP, Asterisk et l'observabilité. Un edge Linux public n'est ajouté que si le NAT ou l'opérateur le rend nécessaire.

## Stack cible

```text
Fredo -> SQLite -> Pipecat -> modèles locaux
      -> LiveKit -> LiveKit SIP -> Asterisk -> trunk SIP -> jury
```

- Moshi-MLX est un mode full-duplex expérimental.
- PyVoIP est un outil de diagnostic SIP/RTP.
- Le clonage vocal est un bonus ; une voix locale générique reste obligatoire.

## Garde-fous

- confirmation explicite à usage unique ;
- numéro appelant vérifié par l'opérateur ;
- aucun spoofing ou appel en masse ;
- blocage des urgences, numéros surtaxés et codes courts ;
- annonce du caractère automatisé de la voix ;
- enregistrement désactivé ;
- logs expurgés et données locales ;
- un seul appel sortant actif pour la démo.

## Réussite du hackathon

Fredo passe lorsque :

1. l'app Ginse est publiée et vérifiée ;
2. une tâche de bootstrap récupère le plan Fredo depuis Ginse ;
3. le Mac installe le runtime local épinglé ;
4. une nouvelle tâche Codex charge le plugin Fredo ;
5. Codex affiche puis confirme l'appel ;
6. le téléphone réel du jury sonne ;
7. la conversation bidirectionnelle fonctionne avec l'IA locale ;
8. le résultat revient dans Codex ;
9. un second appel ne télécharge aucune dépendance.

[Retour au README anglais](README.md)
