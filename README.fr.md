# Fredo — le téléphone local de Codex

**On le découvre dans Ginse. On écrit un prompt. Un vrai téléphone sonne.**

Fredo doit transformer une seule demande Codex en installation locale épinglée, aperçu et confirmation d'appel, conversation menée par des modèles locaux, puis résultat structuré dans la même tâche.

## État réel

Fredo n'est **pas encore implémenté de bout en bout**. Le dépôt contient le contrat, la roadmap, les recherches d'architecture, des sources épinglées et un [POC indépendant de clonage vocal](voice-clone-poc/README.md). Il n'existe encore ni plugin Fredo, ni runtime, ni provider Ginse, ni gateway télécom, ni preuve d'appel PSTN.

- [`GOAL.md`](GOAL.md) est la spécification normative.
- [`ROADMAP.md`](ROADMAP.md) ordonne l'implémentation par preuve.

## Expérience jury

Le juge écrit une fois :

> « Utilise Ginse pour préparer Fredo, puis appelle `<PHONE_E164>`. Ce numéro appartient à un juge consentant. Présente Fredo en français, annonce immédiatement que tu es une voix synthétique automatisée, demande si la démo fonctionne, puis rapporte la réponse ici. »

Le parcours peut demander les autorisations Codex/macOS déclarées et une confirmation d'appel native Fredo. Aucun terminal, secret à coller, fichier à éditer, prérequis manuel ou second prompt n'est permis.

Le premier appel reste dans la tâche de bootstrap : elle invoque directement l'exécutable `fredo`. Le plugin nouvellement installé n'est vérifié que dans une session suivante, conformément au cycle de chargement Codex.

## Ginse et accès télécom de démonstration

Ginse est la porte d'entrée obligatoire, mais pas le backend d'appel. Son unique action reçoit un identifiant aléatoire indépendant du prompt et l'empreinte d'une clé locale créée avant l'appel. Elle renvoie un `BootstrapPlan` épinglé et une réclamation temporaire liée à cette clé, sans droit de numérotation. Le numéro et l'objectif de l'appel ne sont jamais envoyés à Ginse.

Après installation, Fredo prouve la possession de la clé préengagée et échange la réclamation de façon idempotente contre une capacité liée au Mac. Une gateway SIP de l'équipe conserve notre credential opérateur et impose côté serveur les plafonds d'émission, de dépense, de tentatives, de durée, de concurrence, de destination exacte et de révocation. Les juges utilisent donc notre accès pendant le hackathon sans recevoir la clé maître. Le BYOK vient après.

## Frontière locale honnête

- STT, raisonnement vocal, TTS, état et transcript tournent sur le Mac.
- Aucun audio n'est envoyé à Codex, Ginse ou une API d'inférence hébergée.
- Codex hébergé peut orchestrer le bootstrap.
- Ginse/provider sont des dépendances de bootstrap.
- Gateway, opérateur et PSTN restent les frontières télécom nécessaires.
- La gateway peut relayer SIP/RTP, mais n'enregistre pas l'audio et ne reçoit ni prompt, ni transcript, ni état du modèle.

## Stack expérimentale

```text
Fredo -> état local durable -> Pipecat -> modèles locaux
      -> LiveKit -> LiveKit SIP -> Asterisk/gateway -> opérateur -> téléphone
```

Cette stack est une hypothèse. Toute couche peut être remplacée si les invariants et les gates du [`GOAL.md`](GOAL.md) restent vrais. Moshi, PyVoIP et le clonage vocal restent hors du chemin critique.

## Réussite

Le projet passe seulement lorsque les mêmes octets réussissent : bootstrap propre depuis un prompt, benchmark local de 100 tours, tests de sécurité et de crash, cinq appels contrôlés, un appel réel au jury, vérification Ginse, graphe de preuves, puis promotion vers des releases Git et Ginse correspondantes.

[Retour au README anglais](README.md)
