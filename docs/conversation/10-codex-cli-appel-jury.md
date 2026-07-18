+# Moment 10 — Codex CLI local et appel réel du jury

Date : 18 juillet 2026

## Décisions prises

### Surface Codex

Le choix 1 est retenu : la démonstration utilise **Codex CLI avec un modèle local**.

Cette surface permet de garantir que le raisonnement principal de Codex ne dépend pas d’une API d’inférence cloud.

### Téléphonie

Le scénario d’appel SIP limité au réseau local est abandonné.

Pendant la démonstration, le système doit appeler le vrai numéro mobile d’un membre du jury. Le critère de succès est que son téléphone sonne et qu’il puisse converser avec l’agent.

## Architecture révisée

```text
Jury et équipe
     │
     ▼
Codex CLI + modèle local
     │
     ▼
Plugin / skill + serveur MCP local
     │
     ▼
Pipeline vocal open source local
Pipecat + STT + LLM + TTS/clonage
     │
     ▼
Asterisk local
     │
     ▼
Trunk SIP d’un opérateur
     │
     ▼
Réseau téléphonique public
     │
     ▼
Téléphone mobile du jury
```

## Frontière locale

Restent intégralement sur la machine :

- le raisonnement Codex ;
- la préparation et la validation du mandat ;
- la transcription ;
- le modèle conversationnel ;
- le clonage et la synthèse vocale ;
- les règles de sécurité ;
- les journaux et le compte rendu.

Sort de la machine :

- uniquement l’audio nécessaire à l’appel ;
- le numéro de destination transmis à l’opérateur ;
- les métadonnées téléphoniques techniquement nécessaires à l’acheminement.

L’opérateur télécom est un transport externe incontournable pour joindre un numéro public. Il ne fournit aucune fonction d’intelligence artificielle.

## Contraintes techniques

- Asterisk reste le logiciel de téléphonie local et open source.
- Un trunk SIP autorisant les appels sortants vers les mobiles français est nécessaire.
- Le numéro d’appelant doit être vérifié et autorisé par l’opérateur.
- Le compte doit disposer de crédit avant la démonstration.
- Le numéro du jury est saisi au moment de la démo et n’est pas conservé après le compte rendu.
- Aucun appel en masse n’est permis.
- Un seul appel explicitement confirmé peut être actif.

## Parcours de démonstration

1. Un membre du jury communique un numéro qu’il accepte de faire appeler.
2. L’équipe demande à Codex de préparer l’appel.
3. Codex affiche le numéro, l’objectif, le message initial et les données autorisées.
4. L’équipe confirme explicitement.
5. Asterisk initie l’appel via le trunk opérateur.
6. Le téléphone du jury sonne.
7. L’agent annonce qu’il est automatisé et que sa voix est synthétique.
8. Le jury joue le rôle de l’administration.
9. Codex restitue le résultat dans le terminal.

## Definition of done révisée

- Codex CLI fonctionne avec un modèle local.
- Les outils MCP sont visibles et appelables dans Codex.
- Le numéro du jury est validé avant l’appel.
- Le téléphone réel du jury sonne.
- La conversation bidirectionnelle est intelligible.
- L’agent révèle sa nature artificielle.
- Le compte rendu revient dans Codex.
- Aucun fournisseur d’IA cloud n’est utilisé.

## Dépendance critique

L’obtention et la validation du trunk SIP deviennent une tâche de la première heure. Sans identifiants opérateur fonctionnels, aucune architecture logicielle locale ne peut atteindre le téléphone public du jury.

