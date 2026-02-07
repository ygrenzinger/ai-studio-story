# Le Petit Explorateur des Croyances

> Pack d'histoires audio interactif pour enfants de 6-8 ans  
> Voyage à travers le temps pour découvrir les mythes et légendes des cultures du monde

## 📖 Description

Léo, un petit garçon curieux de 7 ans, découvre dans le grenier de sa grand-mère une horloge magique qui peut le transporter dans le passé. À chaque voyage, il rencontre des personnages qui lui racontent les belles histoires de leur culture : des dieux puissants, des héros courageux, et des sages merveilleux.

## 🎭 Les 7 Histoires

| # | Titre | Tradition | Durée | Thèmes |
|---|-------|-----------|-------|--------|
| 1 | **Les Dieux de l'Olympe** | Mythologie grecque | ~10 min | Courage, sagesse |
| 2 | **Les Mystères du Nil** | Mythologie égyptienne | ~10 min | Cycle de vie, espoir |
| 3 | **Les Guerriers du Nord** | Mythologie nordique | ~10 min | Courage, sacrifice |
| 4 | **Le Prince qui Devint Sage** | Bouddhisme | ~10 min | Compassion, paix |
| 5 | **Les Histoires du Peuple Voyageur** | Judaïsme | ~10 min | Liberté, justice |
| 6 | **L'Enfant de Bethléem** | Christianisme | ~10 min | Amour, pardon |
| 7 | **Le Messager du Désert** | Islam | ~10 min | Générosité, honnêteté |

**Durée totale** : ~60-70 minutes

## 🎯 Objectifs Pédagogiques

- Découvrir la diversité des croyances et cultures à travers l'histoire
- Comprendre que toutes les cultures ont de belles histoires à raconter
- Identifier les valeurs universelles : courage, sagesse, compassion, partage
- Développer la curiosité et le respect des différentes traditions

## 👥 Personnages

### Personnages Principaux
- **Léo** (7 ans, voix Puck) - Le petit explorateur curieux
- **Grand-Mère Céleste** (voix Sulafat) - La narratrice bienveillante

### Personnages Secondaires
- **Alexios** - Berger grec (Histoire 1)
- **Néféret** - Prêtresse égyptienne (Histoire 2)
- **Freya** - Jeune fille viking (Histoire 3)
- **Moine Dharma** - Moine bouddhiste (Histoire 4)
- **Rabbi Éliézer** - Sage juif (Histoire 5)
- **Berger Samuel** - Berger de Bethléem (Histoire 6)
- **Marchand Rashid** - Marchand arabe (Histoire 7)

## 🎵 Production Audio

### Voix TTS (Gemini 2.5)

| Personnage | Voix | Caractéristique |
|------------|------|-----------------|
| Grand-Mère Céleste | Sulafat | Warm |
| Léo | Puck | Upbeat |
| Alexios | Achird | Friendly |
| Néféret | Kore | Firm |
| Freya | Laomedeia | Upbeat |
| Moine Dharma | Charon | Informative |
| Rabbi Éliézer | Sadaltager | Knowledgeable |
| Berger Samuel | Umbriel | Easy-going |
| Marchand Rashid | Algieba | Smooth |

### Générer les Audios

```bash
# Hub
uv run python generate_audio.py stories/explorateur-croyances/hub/menu.md \
  -o stories/explorateur-croyances/assets/audio/hub-menu.mp3

# Histoire 1
uv run python generate_audio.py stories/explorateur-croyances/stories/01-dieux-olympe/audio-script.md \
  -o stories/explorateur-croyances/assets/audio/story-01-olympe.mp3

# Histoire 2
uv run python generate_audio.py stories/explorateur-croyances/stories/02-mysteres-nil/audio-script.md \
  -o stories/explorateur-croyances/assets/audio/story-02-nil.mp3

# Et ainsi de suite pour les histoires 3-7...
```

## 🖼️ Production Images

Toutes les images doivent être en format **BMP 4-bit, 320x240 pixels, RLE compressé**.

### Prompts de Génération

```bash
# Cover
uv run python generate_cover.py \
  "Une horloge magique dorée ornée de symboles mystérieux dans un grenier chaleureux avec des rayons de lumière dorée" \
  -o stories/explorateur-croyances/assets/images/cover.bmp

# Hub menu
uv run python generate_cover.py \
  "Grenier accueillant avec une grande horloge dorée au centre, malles anciennes, style illustration enfantine chaleureuse" \
  -o stories/explorateur-croyances/assets/images/hub-menu.bmp

# Option 1 - Olympe
uv run python generate_cover.py \
  "Temple grec antique avec colonnes blanches au pied du mont Olympe, ciel bleu, style illustration pour enfants" \
  -o stories/explorateur-croyances/assets/images/option-olympe.bmp

# ... etc.
```

## 📁 Structure du Projet

```
explorateur-croyances/
├── metadata.json           # Métadonnées du pack
├── outline.md             # Outline détaillé complet
├── story.json             # Format Lunii (navigation)
├── validation-report.md   # Rapport de validation
├── README.md             # Ce fichier
│
├── hub/
│   ├── menu.md           # Script du menu principal
│   └── welcome-back.md   # Script de retour
│
├── characters/
│   ├── leo.json
│   ├── grand-mere-celeste.json
│   └── personnages-secondaires.json
│
├── stories/
│   ├── 01-dieux-olympe/
│   │   ├── chapter.md
│   │   └── audio-script.md
│   ├── 02-mysteres-nil/
│   ├── 03-guerriers-nord/
│   ├── 04-prince-sage/
│   ├── 05-peuple-voyageur/
│   ├── 06-enfant-bethlehem/
│   └── 07-messager-desert/
│
└── assets/
    ├── images/          # À générer (16 images BMP)
    └── audio/           # À générer (17 fichiers MP3)
```

## ✅ Validation

Le pack a été validé selon les critères suivants :

- ✅ **Contenu adapté 6-8 ans** : Vocabulaire simple, histoires bienveillantes
- ✅ **Sensibilité culturelle** : Approche respectueuse, pas de hiérarchisation
- ✅ **Structure Lunii valide** : JSON conforme, navigation fonctionnelle
- ✅ **Valeurs éducatives** : Courage, sagesse, compassion, partage présents
- ✅ **Pas de contenu effrayant** : Ton chaleureux et rassurant

## 🚀 Prochaines Étapes

1. **Générer les 17 fichiers audio MP3**
2. **Générer les 16 fichiers images BMP**
3. **Créer l'archive Lunii** (.zip avec story.json + assets/)
4. **Tester sur dispositif Lunii**

## 📄 Licence & Crédits

**Créé le** : 5 février 2026  
**Version** : 1.0  
**Langue** : Français (fr-FR)  
**Auteur** : [Votre nom]  
**TTS** : Google Gemini 2.5  
**Format** : Lunii STUdio v1

---

## 🌟 Valeurs Universelles

Ce pack met en lumière les valeurs partagées par toutes les cultures :

- 💪 **Courage** - Hercule, Thor, Moïse
- 🧠 **Sagesse** - Athéna, Odin, Bouddha
- ❤️ **Compassion** - Isis, Bouddha, Jésus, Mohammed
- 🤝 **Partage** - Enseignements de toutes les traditions
- 🌳 **Respect de la nature** - Noé, Bouddhisme, Islam
- ⚖️ **Justice** - Les 10 commandements, enseignements moraux
- 🕊️ **Paix** - Bouddha, Jésus
- ✨ **Honnêteté** - Mohammed

**"Toutes les cultures ont de belles histoires. Elles sont différentes, mais elles parlent toutes de courage, de gentillesse, et d'amour."** - Grand-Mère Céleste
