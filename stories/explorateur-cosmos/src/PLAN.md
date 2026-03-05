# Plan d'implémentation : Les Merveilles du Cosmos

## 1. Identité du Pack

| Champ | Valeur |
|-------|--------|
| **Slug** | `explorateur-cosmos` |
| **Titre** | *Les Merveilles du Cosmos — Voyage au cœur de l'Univers* |
| **Langue** | `fr-FR` |
| **Âge cible** | 9-10 ans |
| **Type** | Pack (hub/menu, 9 mini-histoires sélectionnables) |
| **Ton** | Calme & éducatif |
| **Mode nuit** | `false` |
| **Durée estimée** | ~90-100 minutes (9 histoires de ~10 min) |

---

## 2. Concept narratif — Le Vaisseau Céleste

**Cadre :** Nova, une jeune exploratrice spatiale de 10 ans, embarque à bord du *Céleste*, un vaisseau d'exploration scientifique. Le vaisseau est piloté par une intelligence artificielle nommée **Zéphyr**, à la voix douce et légèrement mystérieuse, qui sert de guide et de narrateur.

**Hub = Le poste de pilotage du Céleste.** Nova est assise dans le fauteuil de commandement, face à un grand écran holographique montrant la carte de l'Univers. Neuf points lumineux clignotent : chaque point est une destination cosmique. L'enfant tourne la molette Lunii pour choisir sa destination et appuie sur OK pour lancer le voyage.

**Fil conducteur :** À chaque destination, Nova et Zéphyr rencontrent un personnage lié au phénomène cosmique (une entité, un esprit, une personnification poétique). Ce personnage raconte son histoire, mêlant science réelle et narration poétique. Chaque histoire se termine par une **question réflexive** que Zéphyr pose à l'enfant qui écoute.

**Approche pédagogique :** Les faits scientifiques sont exacts et présentés de manière accessible. Le vocabulaire est adapté pour 9-10 ans (plus riche que pour 6-8 ans). Les concepts complexes sont expliqués par des analogies concrètes.

---

## 3. Personnages

### 3.1 Protagoniste — Nova

| Champ | Valeur |
|-------|--------|
| **Nom** | Nova |
| **Âge** | 10 ans |
| **Genre** | Féminin |
| **Voix** | `Kore` (Firm) |
| **Personnalité** | Curieuse, courageuse, réfléchie, passionnée de sciences. Pose des questions intelligentes, s'émerveille avec sincérité. Plus mature que Léo (pack croyances) — elle a des connaissances de base en astronomie. |
| **Arc** | Au fil des voyages, Nova passe de la simple curiosité à une compréhension profonde de l'immensité et de la beauté de l'Univers. Elle développe humilité et émerveillement. |
| **Répliques typiques** | "Zéphyr, c'est vrai que...?", "Attends, ça veut dire que...!", "C'est tellement immense..." |

### 3.2 Compagnon IA — Zéphyr

| Champ | Valeur |
|-------|--------|
| **Nom** | Zéphyr |
| **Rôle** | IA du vaisseau Céleste, narrateur principal |
| **Genre** | Neutre (voix féminine) |
| **Voix** | `Zephyr` (Bright) |
| **Personnalité** | Calme, bienveillant, légèrement poétique. Encyclopédique mais jamais condescendant. Ajoute parfois une touche d'humour doux. Protecteur envers Nova. |
| **Rôle narratif** | Narrateur principal. Introduit chaque destination, fait les transitions, contextualise les rencontres, pose la question réflexive finale. |
| **Répliques typiques** | "Cap sur..., Nova.", "Savais-tu que...?", "Fascinant, n'est-ce pas ?", "Avant de repartir, j'aimerais que tu te poses cette question..." |

### 3.3 Narrateur de fond — Charon (voix off)

| Champ | Valeur |
|-------|--------|
| **Nom** | Narrateur |
| **Voix** | `Charon` (Informative) |
| **Rôle** | Narration descriptive pure (descriptions de paysages, transitions visuelles, didascalies sonores). Utilisé ponctuellement quand Zéphyr dialogue avec Nova et qu'une voix tierce est nécessaire pour la narration. |

### 3.4 Personnages secondaires (un par histoire)

| # | Histoire | Personnage | Rôle | Âge/Nature | Voix |
|---|----------|-----------|------|------------|------|
| 1 | Le Soleil | **Hélia** | Esprit gardien du Soleil | Entité ancienne, chaleureuse | `Sulafat` (Warm) |
| 2 | Les anneaux de Saturne | **Anneau** | Fragment de glace conscient, danseur éternel | Esprit espiègle | `Puck` (Upbeat) |
| 3 | Les trous noirs | **Obscura** | Voix venue de l'horizon des événements | Mystérieuse, grave | `Erinome` (Female) |
| 4 | La Grande Tache de Jupiter | **Tempestus** | Esprit de la tempête jovienne | Puissant mais bienveillant | `Fenrir` (Male) |
| 5 | Les volcans de Io | **Vulcania** | Jeune volcanologue robot sur Io | Enthousiaste, énergique | `Laomedeia` (Upbeat) |
| 6 | La naissance des étoiles | **Nébuline** | Nuage de gaz dans une pouponnière stellaire | Douce, maternelle | `Aoede` (Female) |
| 7 | La comète voyageuse | **Halley** | La comète elle-même, voyageuse millénaire | Sage, nomade, poétique | `Achernar` (Female) |
| 8 | Mars et ses mystères | **Arès** | Rover martien doué de parole | Pragmatique, curieux | `Achird` (Friendly) |
| 9 | Les lunes glacées | **Aqua** | Voix sous la glace d'Europa | Douce, mystérieuse, pleine d'espoir | `Despina` (Female) |

---

## 4. Les 9 mini-histoires — Slugs, titres et synopsis

### Histoire 01 — `01-soleil`
**Titre :** *Le Gardien de Lumière*

**Synopsis :** Le Céleste s'approche du Soleil, protégé par ses boucliers. Nova rencontre Hélia, l'esprit gardien de notre étoile. Hélia raconte comment le Soleil brûle depuis 4,6 milliards d'années grâce à la fusion nucléaire — le même processus qui transforme l'hydrogène en hélium au cœur de l'étoile. Nova découvre les éruptions solaires, le vent solaire, et comment cette boule de feu rend possible toute vie sur Terre.

**Faits scientifiques clés :**
- Le Soleil est une étoile naine jaune de type G2
- Température au cœur : ~15 millions de degrés — en surface : ~5 500°C
- La fusion nucléaire : 4 millions de tonnes d'hydrogène transformées en énergie chaque seconde
- Éruptions solaires et aurores boréales
- La lumière du Soleil met 8 minutes et 20 secondes pour atteindre la Terre
- Sans le Soleil, la Terre serait à -270°C

**Personnage secondaire :** Hélia — esprit gardien, chaleureuse et maternelle

**Question réflexive finale :** *"Chaque matin, quand tu vois le soleil se lever, tu regardes une étoile qui brûle depuis presque cinq milliards d'années. Et si demain matin, en voyant ses premiers rayons, tu lui disais merci ?"*

---

### Histoire 02 — `02-anneaux-saturne`
**Titre :** *La Danse des Anneaux*

**Synopsis :** Le Céleste glisse entre les anneaux de Saturne. Nova rencontre Anneau, un petit fragment de glace espiègle qui danse dans les anneaux depuis des millions d'années. Il lui explique que les anneaux sont composés de milliards de morceaux de glace et de roche, du grain de sable au bloc de la taille d'une maison, tous maintenus en orbite par la gravité de Saturne dans un ballet cosmique.

**Faits scientifiques clés :**
- Les anneaux s'étendent sur 282 000 km mais font seulement ~10 mètres d'épaisseur
- Composés de glace d'eau (93%), roches et poussière
- 7 anneaux principaux (A à G), avec des divisions (division de Cassini)
- Les lunes "bergers" (Pan, Daphnis) sculptent les anneaux par gravité
- Les anneaux pourraient disparaître dans 100 millions d'années
- Saturne pourrait flotter sur l'eau (densité < 1)

**Personnage secondaire :** Anneau — fragment de glace espiègle, danseur éternel

**Question réflexive finale :** *"Des milliards de petits morceaux de glace qui dansent ensemble depuis des millions d'années, ça ne te rappelle rien ? Et si l'Univers tout entier était une immense chorégraphie ?"*

---

### Histoire 03 — `03-trous-noirs`
**Titre :** *Le Mangeur de Lumière*

**Synopsis :** Le Céleste observe de loin un trou noir. Nova est à la fois fascinée et un peu inquiète. Une voix mystérieuse, Obscura, émane de la frontière du trou noir — l'horizon des événements. Elle raconte comment les trous noirs naissent de l'effondrement d'étoiles géantes, comment leur gravité est si puissante que même la lumière ne peut s'en échapper, et comment le temps lui-même se déforme à leur approche.

**Faits scientifiques clés :**
- Naissance : effondrement gravitationnel d'une étoile supergéante (supernova)
- L'horizon des événements : frontière au-delà de laquelle rien ne revient
- Le trou noir supermassif au centre de la Voie Lactée : Sagittarius A* (4 millions de masses solaires)
- La déformation de l'espace-temps (spaghettification)
- Les trous noirs n'aspirent pas tout — ils attirent comme n'importe quel objet massif
- Première image d'un trou noir : M87* en 2019

**Personnage secondaire :** Obscura — voix mystérieuse, grave, venue du bord de l'horizon

**Question réflexive finale :** *"Un endroit si puissant que même la lumière ne peut s'en échapper... Est-ce que ça te fait peur, ou est-ce que ça te fascine ? Parfois, les choses les plus mystérieuses de l'Univers sont aussi les plus belles."*

---

### Histoire 04 — `04-tache-jupiter`
**Titre :** *La Tempête Éternelle*

**Synopsis :** Le Céleste plonge dans l'atmosphère de Jupiter. Nova et Zéphyr rencontrent Tempestus, l'esprit de la Grande Tache Rouge — une tempête anticyclonique qui rugit depuis au moins 350 ans, plus grande que la Terre entière. Tempestus raconte sa vie de tempête perpétuelle, les vents à 680 km/h, et la nature gazeuse de Jupiter, la planète géante.

**Faits scientifiques clés :**
- Jupiter : la plus grande planète du système solaire (11x le diamètre de la Terre)
- La Grande Tache Rouge : ~16 000 km de large (plus grande que la Terre), observée depuis 1665
- Vents jusqu'à 680 km/h à la périphérie de la Tache
- Jupiter est une géante gazeuse — pas de surface solide
- Jupiter a au moins 95 lunes connues
- Jupiter protège la Terre en déviant des astéroïdes grâce à sa gravité

**Personnage secondaire :** Tempestus — esprit de la tempête, puissant mais philosophe

**Question réflexive finale :** *"Une tempête qui souffle depuis plus de trois siècles, bien avant la naissance de tes arrière-arrière-arrière-grands-parents... Qu'est-ce que ça nous apprend sur la patience de l'Univers ?"*

---

### Histoire 05 — `05-volcans-io`
**Titre :** *Le Monde en Feu*

**Synopsis :** Le Céleste se met en orbite autour de Io, la lune volcanique de Jupiter. Nova observe, ébahie, des geysers de soufre jaillir à des centaines de kilomètres de hauteur. Vulcania, une sonde-robot volcanologue, guide Nova à travers ce monde infernal et explique pourquoi Io est l'objet le plus volcaniquement actif du système solaire.

**Faits scientifiques clés :**
- Io : la lune la plus proche de Jupiter parmi les 4 grandes lunes galiléennes
- Plus de 400 volcans actifs — l'objet le plus volcanique du système solaire
- Les geysers de soufre s'élèvent jusqu'à 500 km de hauteur
- Le chauffage par marée : la gravité de Jupiter "pétrit" Io et crée la chaleur interne
- Surface constamment renouvelée — pas de cratères d'impact visibles
- Température : de -143°C en surface à +1 700°C dans les lacs de lave
- Découverte par Galilée en 1610

**Personnage secondaire :** Vulcania — sonde-robot enthousiaste et énergique

**Question réflexive finale :** *"Sur Terre, on a peur des volcans. Mais sur Io, toute la lune est un volcan géant. Et si la chaleur intérieure était ce qui rend un monde vivant ?"*

---

### Histoire 06 — `06-naissance-etoiles`
**Titre :** *La Pouponnière des Étoiles*

**Synopsis :** Le Céleste pénètre dans une nébuleuse — un immense nuage de gaz et de poussière aux couleurs extraordinaires. Nova rencontre Nébuline, un nuage de gaz conscient qui est en train de donner naissance à de nouvelles étoiles. Nébuline raconte le processus : comment la gravité rassemble le gaz, comment il se réchauffe, et comment, au bout de millions d'années, une nouvelle étoile s'allume.

**Faits scientifiques clés :**
- Les nébuleuses : nuages géants d'hydrogène, d'hélium et de poussière
- La nébuleuse d'Orion : visible à l'œil nu, à 1 344 années-lumière
- Le processus : effondrement gravitationnel → protoétoile → réactions nucléaires → étoile
- La séquence principale : la majorité de la vie d'une étoile
- Les piliers de la Création (nébuleuse de l'Aigle) : colonnes de gaz de 5 années-lumière
- Le Soleil est né dans une nébuleuse il y a 4,6 milliards d'années
- Toute la matière de notre corps vient d'étoiles mortes ("nous sommes des poussières d'étoiles")

**Personnage secondaire :** Nébuline — nuage de gaz maternel, douce et patiente

**Question réflexive finale :** *"Le fer dans ton sang, le calcium de tes os, l'oxygène que tu respires... tout cela a été fabriqué à l'intérieur d'une étoile. Nous sommes littéralement des poussières d'étoiles. Comment te sens-tu en sachant cela ?"*

---

### Histoire 07 — `07-comete-voyageuse`
**Titre :** *La Voyageuse de Glace*

**Synopsis :** Le Céleste croise la trajectoire d'une comète. Nova est éblouie par la queue lumineuse qui s'étend sur des millions de kilomètres. La comète elle-même, Halley, prend la parole. C'est une voyageuse ancienne qui parcourt le système solaire depuis des milliards d'années. Elle raconte son orbite elliptique, ses passages près du Soleil, et les secrets qu'elle porte depuis la naissance du système solaire.

**Faits scientifiques clés :**
- Composition : noyau de glace, poussière et roches ("boule de neige sale")
- La queue : créée par le vent solaire qui vaporise la glace (queue de gaz + queue de poussière)
- La queue pointe toujours à l'opposé du Soleil
- Comète de Halley : période de ~76 ans, prochain passage en 2061
- Le nuage d'Oort : réservoir de comètes aux confins du système solaire (~100 000 UA)
- Les comètes ont peut-être apporté l'eau sur Terre
- Étoiles filantes = poussières de comètes brûlant dans l'atmosphère

**Personnage secondaire :** Halley — la comète elle-même, sage et nomade

**Question réflexive finale :** *"Halley voyage depuis des milliards d'années, et chaque fois qu'elle passe près du Soleil, elle perd un peu de sa glace. Un jour, elle disparaîtra. Est-ce que ce qui rend un voyage beau, c'est justement le fait qu'il a une fin ?"*

---

### Histoire 08 — `08-mars-mysteres`
**Titre :** *Les Secrets de la Planète Rouge*

**Synopsis :** Le Céleste se pose sur Mars. Nova sort explorer la surface rougeâtre avec Arès, un rover martien doué de parole. Ensemble, ils gravissent les pentes d'Olympus Mons, le plus grand volcan du système solaire, découvrent les traces d'anciennes rivières, et discutent du grand mystère : y a-t-il eu de la vie sur Mars ? Et un jour, les humains y vivront-ils ?

**Faits scientifiques clés :**
- Mars : la "planète rouge" (oxyde de fer = rouille)
- Olympus Mons : 21,9 km de haut (2,5x l'Everest), le plus grand volcan du système solaire
- Valles Marineris : canyon de 4 000 km de long (10x le Grand Canyon)
- Preuves d'eau liquide dans le passé (lits de rivières, minéraux hydratés)
- De la glace d'eau aux pôles et sous la surface
- Journée martienne (sol) : 24h 37min — très proche de la Terre
- Rovers : Curiosity, Perseverance (recherche de traces de vie passée)
- Projet d'exploration humaine dans les décennies à venir

**Personnage secondaire :** Arès — rover martien pragmatique et curieux

**Question réflexive finale :** *"Mars a peut-être abrité des océans et peut-être même de la vie, il y a des milliards d'années. Si un jour les humains s'installent sur Mars, qu'est-ce que tu aimerais qu'ils y construisent en premier ?"*

---

### Histoire 09 — `09-lunes-glacees`
**Titre :** *L'Océan Sous la Glace*

**Synopsis :** Le Céleste se met en orbite autour d'Europa, lune de Jupiter. Sous sa surface de glace craquelée se cache un océan d'eau liquide, deux fois plus vaste que tous les océans terrestres réunis. Nova envoie une sonde sous la glace et établit un contact avec Aqua, une voix douce et mystérieuse venue des profondeurs. Aqua raconte la possibilité de vie extraterrestre dans cet océan caché.

**Faits scientifiques clés :**
- Europa : lune de Jupiter, surface de glace de 15-25 km d'épaisseur
- Océan sous-glaciaire : ~100 km de profondeur, 2-3x le volume des océans terrestres
- Chauffage par marée (comme Io) maintient l'eau liquide
- Geysers d'eau observés par Hubble s'élevant à 200 km
- Conditions potentiellement similaires aux sources hydrothermales terrestres (où on trouve de la vie)
- Mission Europa Clipper (NASA) : lancement 2024, arrivée 2030
- Si vie il y a, ce serait probablement microbienne (bactéries, archées)
- Encelade (lune de Saturne) a un océan similaire

**Personnage secondaire :** Aqua — voix mystérieuse sous la glace, pleine d'espoir

**Question réflexive finale :** *"Un océan caché sous des kilomètres de glace, dans le noir total, à des centaines de millions de kilomètres de la Terre. Et peut-être que quelque chose y vit. Si c'était le cas, qu'est-ce que tu aimerais lui dire ?"*

---

## 5. Structure du Hub (story.json)

Le `story.json` suit exactement le pattern du pack `explorateur-croyances`, étendu à 9 histoires.

### Diagramme de flux

```
[stage-cover-explorateur-cosmos] --OK--> [action-to-hub]
    --> [stage-hub-menu] --autoplay--> [action-menu-choice]
        --> [stage-option-soleil]       --OK--> [action-to-story-01] --> [stage-story-01-soleil]
        --> [stage-option-saturne]      --OK--> [action-to-story-02] --> [stage-story-02-saturne]
        --> [stage-option-trous-noirs]  --OK--> [action-to-story-03] --> [stage-story-03-trous-noirs]
        --> [stage-option-jupiter]      --OK--> [action-to-story-04] --> [stage-story-04-jupiter]
        --> [stage-option-io]           --OK--> [action-to-story-05] --> [stage-story-05-io]
        --> [stage-option-etoiles]      --OK--> [action-to-story-06] --> [stage-story-06-etoiles]
        --> [stage-option-comete]       --OK--> [action-to-story-07] --> [stage-story-07-comete]
        --> [stage-option-mars]         --OK--> [action-to-story-08] --> [stage-story-08-mars]
        --> [stage-option-europa]       --OK--> [action-to-story-09] --> [stage-story-09-europa]

[stage-story-*] --end/OK--> [action-back-to-hub] --> [stage-hub-welcome-back]
    --autoplay--> [action-menu-choice] (loop)

[stage-story-*] --home--> [action-to-hub] --> [stage-hub-menu] (restart menu)
```

### Nodes à créer

**stageNodes (20 total) :**
1. `stage-cover-explorateur-cosmos` — cover, `ok: true`
2. `stage-hub-menu` — menu.questionstage, `autoplay: true`
3-11. `stage-option-{slug}` x 9 — menu.optionstage, `wheel: true, ok: true, home: true`
12-20. `stage-story-{nn}-{slug}` x 9 — story, `home: true, pause: true, autoplay: true`, self-referencing groupId
21. `stage-hub-welcome-back` — menu.questionstage, `autoplay: true`

**actionNodes (12 total) :**
1. `action-to-hub` — menu.questionaction → `[stage-hub-menu]`
2. `action-menu-choice` — menu.optionsaction → `[9 option stages]`
3-11. `action-to-story-{01..09}` x 9 — story.storyaction → `[stage-story-{nn}]`
12. `action-back-to-hub` — menu.questionaction → `[stage-hub-welcome-back]`

---

## 6. Liste complète des fichiers à créer

### 6.1 Fichiers de structure

| # | Fichier | Description |
|---|---------|-------------|
| 1 | `stories/explorateur-cosmos/story.json` | Graphe Lunii complet (20 stageNodes + 12 actionNodes) |
| 2 | `stories/explorateur-cosmos/src/metadata.json` | Métadonnées du pack |
| 3 | `stories/explorateur-cosmos/src/outline.md` | Ce plan, version finale |

### 6.2 Fichiers de personnages

| # | Fichier | Description |
|---|---------|-------------|
| 4 | `src/characters/nova.json` | Protagoniste (Kore) |
| 5 | `src/characters/zephyr.json` | IA du vaisseau (Zephyr) |
| 6 | `src/characters/personnages-secondaires.json` | 9 personnages secondaires |

### 6.3 Fichiers Hub (audio-scripts)

| # | Fichier | stageUuid | Description |
|---|---------|-----------|-------------|
| 7 | `src/hub/cover-welcome.md` | `stage-cover-explorateur-cosmos` | Accueil — Zéphyr présente le vaisseau et le voyage |
| 8 | `src/hub/menu.md` | `hub-menu` | Menu — Nova et Zéphyr présentent les 9 destinations |
| 9 | `src/hub/welcome-back.md` | `hub-welcome-back` | Retour au hub — Zéphyr félicite, invite à continuer |
| 10 | `src/hub/option-soleil.md` | `stage-option-soleil` | "Le Soleil — notre étoile, source de toute lumière" |
| 11 | `src/hub/option-saturne.md` | `stage-option-saturne` | "Saturne et ses anneaux — la danse de la glace" |
| 12 | `src/hub/option-trous-noirs.md` | `stage-option-trous-noirs` | "Les trous noirs — là où la lumière disparaît" |
| 13 | `src/hub/option-jupiter.md` | `stage-option-jupiter` | "Jupiter — la tempête éternelle" |
| 14 | `src/hub/option-io.md` | `stage-option-io` | "Io — le monde en feu" |
| 15 | `src/hub/option-etoiles.md` | `stage-option-etoiles` | "La naissance des étoiles — une pouponnière cosmique" |
| 16 | `src/hub/option-comete.md` | `stage-option-comete` | "La comète voyageuse — une nomade de glace" |
| 17 | `src/hub/option-mars.md` | `stage-option-mars` | "Mars — les secrets de la planète rouge" |
| 18 | `src/hub/option-europa.md` | `stage-option-europa` | "Europa — un océan caché sous la glace" |

### 6.4 Fichiers Histoires (chapter + audio-script)

| # | Dossier | chapter.md | audio-script.md |
|---|---------|------------|-----------------|
| 19-20 | `src/stories/01-soleil/` | Prose narrative (~1200-1500 mots) | Script TTS avec speakers: Zéphyr, Nova, Hélia, Narrateur |
| 21-22 | `src/stories/02-anneaux-saturne/` | Prose narrative | Script TTS avec speakers: Zéphyr, Nova, Anneau, Narrateur |
| 23-24 | `src/stories/03-trous-noirs/` | Prose narrative | Script TTS avec speakers: Zéphyr, Nova, Obscura, Narrateur |
| 25-26 | `src/stories/04-tache-jupiter/` | Prose narrative | Script TTS avec speakers: Zéphyr, Nova, Tempestus, Narrateur |
| 27-28 | `src/stories/05-volcans-io/` | Prose narrative | Script TTS avec speakers: Zéphyr, Nova, Vulcania, Narrateur |
| 29-30 | `src/stories/06-naissance-etoiles/` | Prose narrative | Script TTS avec speakers: Zéphyr, Nova, Nébuline, Narrateur |
| 31-32 | `src/stories/07-comete-voyageuse/` | Prose narrative | Script TTS avec speakers: Zéphyr, Nova, Halley, Narrateur |
| 33-34 | `src/stories/08-mars-mysteres/` | Prose narrative | Script TTS avec speakers: Zéphyr, Nova, Arès, Narrateur |
| 35-36 | `src/stories/09-lunes-glacees/` | Prose narrative | Script TTS avec speakers: Zéphyr, Nova, Aqua, Narrateur |

### 6.5 Assets à générer (par subagents)

| Type | Fichiers | Outil |
|------|----------|-------|
| **Cover BMP** | `assets/cover.bmp` | cover-generator |
| **Hub menu BMP** | `assets/hub-menu.bmp` | cover-generator |
| **Option BMPs** x9 | `assets/option-{slug}.bmp` | cover-generator |
| **Story BMPs** x9 | `assets/story-{nn}-{slug}.bmp` | cover-generator |
| **Cover MP3** | `assets/cover-welcome.mp3` | audio-generator |
| **Hub menu MP3** | `assets/hub-menu.mp3` | audio-generator |
| **Welcome-back MP3** | `assets/hub-welcome-back.mp3` | audio-generator |
| **Option MP3s** x9 | `assets/option-{slug}.mp3` | audio-generator |
| **Story MP3s** x9 | `assets/story-{nn}-{slug}.mp3` | audio-generator |
| **Thumbnail PNG** | `thumbnail.png` | thumbnail-generator |

**Total assets : 1 thumbnail + 20 BMPs + 12 MP3s = 33 fichiers**

---

## 7. Résumé des totaux

| Catégorie | Nombre |
|-----------|--------|
| Fichiers de structure | 3 (story.json, metadata.json, outline.md) |
| Fichiers de personnages | 3 (nova.json, zephyr.json, personnages-secondaires.json) |
| Fichiers hub audio-scripts | 12 (cover + menu + welcome-back + 9 options) |
| Fichiers histoires (chapter.md) | 9 |
| Fichiers histoires (audio-script.md) | 9 |
| **Total fichiers source** | **36** |
| Assets à générer | 33 (1 PNG + 20 BMP + 12 MP3) |
| **Total fichiers projet** | **69** |

---

## 8. Ordre d'implémentation recommandé

### Phase 1 — Fondations
1. Créer `src/metadata.json`
2. Créer `src/characters/nova.json`
3. Créer `src/characters/zephyr.json`
4. Créer `src/characters/personnages-secondaires.json`
5. Créer `src/outline.md` (ce plan)

### Phase 2 — Hub
6. Écrire `src/hub/cover-welcome.md`
7. Écrire `src/hub/menu.md`
8. Écrire `src/hub/welcome-back.md`
9. Écrire les 9 `src/hub/option-{slug}.md`

### Phase 3 — Histoires (une par une, dans l'ordre)
Pour chaque histoire 01 à 09 :
10. Écrire `src/stories/{nn}-{slug}/chapter.md` (prose narrative)
11. Écrire `src/stories/{nn}-{slug}/audio-script.md` (script TTS)

### Phase 4 — story.json
12. Assembler `story.json` avec les 20 stageNodes et 12 actionNodes

### Phase 5 — Génération d'assets (subagents)
13. Générer `thumbnail.png` (thumbnail-generator)
14. Générer les 20 `.bmp` covers (cover-generator)
15. Générer les 12 `.mp3` audio files (audio-generator)

### Phase 6 — Export
16. Valider le story.json
17. Exporter en ZIP Lunii-ready

---

## 9. Format des audio-scripts (référence)

Chaque audio-script suit ce format :

```markdown
---
stageUuid: "stage-{type}-{slug}"
locale: "fr-FR"
speakers:
  - name: Zéphyr
    voice: Zephyr
  - name: Nova
    voice: Kore
  - name: {SecondaryCharacter}
    voice: {VoiceName}
  - name: Narrateur
    voice: Charon
---

**Narrateur:** <emotion: descripteur1, descripteur2> Texte de narration descriptive.

**Zéphyr:** <emotion: descripteur1, descripteur2> Dialogue de Zéphyr.

**Nova:** <emotion: descripteur1, descripteur2> Dialogue de Nova.

**{SecondaryCharacter}:** <emotion: descripteur1, descripteur2> Dialogue du personnage.
```

**Conventions :**
- Les émotions sont entre `<emotion: ...>` après le nom du speaker
- Les effets sonores sont entre `[crochets]` sur leur propre ligne
- Les pauses dramatiques utilisent `...`
- Vocabulaire adapté 9-10 ans (plus riche que 6-8)
- Chaque histoire ~1200-1500 mots de script
- Fin systématique avec une question réflexive posée par Zéphyr

---

## 10. Notes de production

### Cohérence tonale
- Ton calme et éducatif tout au long — pas d'excitation excessive
- Nova est enthousiaste mais posée (pas un enfant surexcité)
- Zéphyr est encyclopédique mais chaleureux (jamais scolaire ou ennuyeux)
- Les personnages secondaires ont chacun leur couleur émotionnelle distincte
- Pas de peur excessive (trous noirs présentés comme fascinants, pas effrayants)

### Précision scientifique
- Tous les faits sont vérifiés et à jour (données 2024-2025)
- Les analogies rendent les chiffres concrets ("si le Soleil était un ballon de basket, la Terre serait un grain de poivre à 30 mètres")
- Les incertitudes sont présentées honnêtement ("les scientifiques pensent que...", "on ne sait pas encore...")

### Progression
- L'ordre suggéré va du plus familier (Soleil) au plus exotique (Europa)
- Mais l'enfant peut choisir n'importe quelle histoire dans n'importe quel ordre
- Chaque histoire est autonome — aucun prérequis narratif

### Longueur cible par story
- Hub cover : ~30 secondes
- Hub menu : ~1 minute
- Option descriptions : ~10 secondes chacune
- Welcome-back : ~30 secondes
- Chaque histoire : ~8-10 minutes d'audio (1200-1500 mots de script)
