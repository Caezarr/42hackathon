# 42hackathon — appels locaux depuis Codex

**Une appliance téléphonique locale pour Codex.**

Ce projet de hackathon vise à permettre à Codex de passer des appels via l'infrastructure de chaque utilisateur. Les modèles utilisés pendant l'appel, l'audio, les identifiants, les transcriptions et les coûts téléphoniques restent chez lui. Le nom produit reste à choisir : `42hackathon` est le nom du dépôt, pas une marque reprise d'un autre projet.

Il n'existe ni backend d'appels partagé, ni facture téléphonique centrale.

> On prépare une version épinglée. On connecte son compte SIP ou un bridge pour sa SIM. Les appels suivants ne téléchargent rien implicitement.

## État actuel

Le dépôt contient aujourd'hui le contrat produit, l'architecture, les sources épinglées et le plan du hackathon. Les images runtime et les modèles ne sont pas encore verrouillés par digest. Le dialer de bout en bout et les commandes décrites ci-dessous ne sont pas encore implémentés.

## Ce que nous construisons

```text
Codex
  -> MCP téléphonique local
  -> Pipecat + LiveKit
  -> STT + LLM + TTS locaux
  -> transport appartenant à l'utilisateur
     -> navigateur WebRTC
     -> trunk SIP personnel
     -> boîtier GSM/LTE avec sa SIM
     -> Android appairé en Bluetooth via Asterisk
```

Le premier lancement cible télécharge et vérifie toutes les dépendances du profil choisi. Une fois cette version active, un appel ne déclenche aucun téléchargement implicite. Les mises à jour restent explicites. Le réseau SIP ou cellulaire demeure nécessaire pour joindre le téléphone public.

## Principes

- calcul, données, secrets et historique chez l'utilisateur ;
- aucun service STT, LLM d'appel ou TTS hébergé obligatoire ;
- véritable numéro de SIM ou numéro SIP vérifié, jamais de spoofing ;
- confirmation humaine et politique de destinations ;
- enregistrement désactivé par défaut ;
- Ginse optionnel et publié séparément par chaque installation.

Codex reste une interface hébergée : l'instruction de l'utilisateur et le résultat structuré suivent les règles de service et de confidentialité propres à Codex. Ginse, lorsqu'il est activé, exige aussi que l'opérateur expose un endpoint HTTPS sécurisé ; il ne peut pas appeler `localhost`.

## Démo cible

1. Installer la stack sur un laptop ou serveur personnel.
2. Télécharger les modèles locaux.
3. Connecter un transport appartenant à l'utilisateur.
4. Ajouter le MCP local à Codex.
5. Demander un appel, confirmer, puis recevoir le résultat structuré.

Le [`README principal`](README.md) contient l'architecture, la stack, les objectifs du hackathon et les instructions contributeurs.
