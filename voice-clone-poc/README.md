# POC de clonage vocal local

Ce projet test accepte un échantillon vocal WAV, puis synthétise en français une phrase écrite par l'utilisateur avec la voix de référence. L'interface et l'inférence tournent localement.

## Moteur choisi

- Chatterbox Multilingual V3 de Resemble AI ;
- licence MIT pour le code et les poids ;
- clonage zero-shot, sans entraînement ;
- français natif ;
- watermark PerTh intégré aux fichiers générés.

Le code Chatterbox est épinglé au commit `65b18437192794391a0308a8f705b1e33e633948`. Les poids `ResembleAI/chatterbox` sont épinglés à la révision `5bb1f6ee58e50c3b8d408bc82a6d3740c2db6e18`.

## Démarrage sous Windows, sans Winget

Prérequis : [`uv`](https://docs.astral.sh/uv/), déjà présent sur la machine de démonstration.

```powershell
cd voice-clone-poc
.\setup.ps1
.\run.ps1
```

Ouvre ensuite <http://127.0.0.1:7860>. La première génération télécharge les poids dans `.local-state/voice-clone/models`. Les générations sont écrites dans `.local-state/voice-clone/outputs`. Aucun service de synthèse hébergé n'est utilisé.

Sur une machine sans GPU NVIDIA, le POC sélectionne le CPU automatiquement. Cela fonctionne mais la génération sera nettement plus lente. Pour imposer un périphérique :

```powershell
$env:VOICE_CLONE_DEVICE = "cpu" # ou cuda / mps
.\run.ps1
```

Après le premier téléchargement réussi :

```powershell
$env:VOICE_CLONE_OFFLINE = "1"
.\run.ps1
```

## Échantillon recommandé

Enregistre un WAV propre, mono ou stéréo, d'au moins 16 kHz, entre 8 et 45 secondes. Parle naturellement à volume constant, à environ 15–20 cm du micro, dans une pièce sans musique, ventilateur ni réverbération.

Chatterbox utilise au maximum environ dix secondes pour son conditionnement. Un fichier de trente secondes est accepté, mais les dix premières secondes doivent donc être les meilleures. Lis ce texte sans jouer un personnage :

> Bonjour, je parle ici avec ma voix naturelle, sans forcer le rythme ni changer mon accent. Ce matin, j'ai pris un café chaud près de la grande fenêtre, puis j'ai vérifié quelques chiffres précis : douze, vingt-trois, quarante-huit et soixante-dix. Pourquoi cette petite phrase paraît-elle si simple ? Parce qu'elle mélange des sons clairs, graves, doux et rapides. Je peux poser une question, marquer une pause, puis terminer tranquillement. Voilà, cet échantillon représente ma manière habituelle de parler.

Conseils importants :

- évite les silences au début et les bruits de bouche ;
- ne chuchote pas et ne surarticule pas ;
- garde ton accent et ton rythme habituels ;
- utilise la même langue dans la référence et la phrase générée pour préserver l'accent ;
- recommence l'enregistrement si le niveau sature ou si un bruit couvre une syllabe.

## Vérification rapide

Les tests de validation ne chargent pas le modèle :

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

## Limites connues

- Le premier lancement nécessite Internet pour télécharger les poids épinglés.
- Le CPU est adapté à une preuve de concept, pas encore à une conversation temps réel.
- La ressemblance dépend fortement de la propreté et du naturel de la référence.
- Le POC exige une confirmation que la voix appartient à l'utilisateur ou qu'il dispose d'une autorisation explicite.
