# Le Grand Voyage des Continents - Plan Complet

## Vue d'ensemble

**Concept** : Noë, un enfant explorateur de 8 ans, trouve une boussole magique. Elle ne montre pas seulement le nord : chaque direction ouvre une porte vers un continent. L'introduction est très courte pour laisser rapidement l'enfant choisir son continent sur la Lunii.

**Structure interactive** : hub court -> choix du continent -> enchaînement ou sélection des histoires pays de ce continent -> retour au menu.

**Public cible** : 7-8 ans.

**Durée cible** : environ 3h10 à 3h25 au total.

**Approche** : chaque continent est guidé par un personnage différent, mais chaque pays est une histoire séparée. Chaque pays dure environ 8 minutes. Il n'y a pas de mission par pays : le récit privilégie l'observation, les sons, les images mentales, les questions de Noë et les explications simples.

## Hub principal

**Durée** : 30 à 45 secondes.

Noë trouve une boussole magique. Une voix douce explique que chaque direction mène vers un continent. L'enfant choisit ensuite : Afrique, Europe, Asie, Amérique ou Océanie.

## Guides

- **Afrique - Amara** : guide naturaliste chaleureuse, vive et protectrice.
- **Europe - Luca** : petit cartographe joyeux, passionné de villes, langues et monuments.
- **Asie - Mei** : guide inventive, attentive aux traditions, paysages et découvertes.
- **Amérique - Sami** : condor voyageur, calme et enthousiaste, qui survole montagnes, forêts, lacs et grandes villes.
- **Océanie - Tala** : tortue marine sage, douce et patiente, liée aux récifs et aux îles.

## Structure interactive d'un continent

1. L'enfant choisit un continent dans le hub principal.
2. Le guide du continent accueille Noë en quelques phrases.
3. Les histoires pays du continent sont proposées ou jouées dans l'ordre.
4. Chaque pays correspond à un dossier `src/stories/{id-pays}/` avec `chapter.md` et `audio-script.md`.
5. Après une histoire pays, retour au menu du continent ou au menu principal selon le graphe Lunii final.

## Structure d'un pays

- Arrivée sensorielle dans le pays.
- Paysage ou lieu emblématique.
- Vie quotidienne, ville, langue ou coutume.
- Nature, animaux ou environnement.
- Histoire, monument, art, invention ou savoir-faire.
- Petite scène calme et concrète.
- Récapitulatif très court.

## Histoires pays par continent

### Afrique - Les Lumières d'Afrique

**Durée estimée** : 34-36 minutes, 4 histoires pays.

- `01-01-egypte` - **L'Égypte et le Fleuve Roi** : le Nil, les pyramides, le désert et les oasis, Le Caire moderne.
- `01-02-maroc` - **Le Maroc aux Mille Couleurs** : le Sahara, les souks et l'artisanat, l'Atlas, la diversité mer-montagne-désert.
- `01-03-nigeria` - **Le Nigeria qui Danse** : Lagos, musique et danse, marchés et créativité, diversité des langues et cultures.
- `01-04-afrique-du-sud` - **L'Afrique du Sud Arc-en-Ciel** : Le Cap et la montagne de la Table, savane et animaux, deux océans, diversité culturelle.

### Europe - Les Chemins d'Europe

**Durée estimée** : 42-44 minutes, 5 histoires pays.

- `02-01-espagne` - **L'Espagne en Musique** : Madrid et Barcelone, flamenco et fêtes, Méditerranée, plages, villes et montagnes.
- `02-02-italie` - **L'Italie des Pierres et des Canaux** : Rome antique, Venise et ses canaux, cuisine familiale, volcans comme l'Etna ou le Vésuve.
- `02-03-allemagne` - **L'Allemagne des Forêts et des Idées** : Berlin, forêts et châteaux, inventions et savoir-faire, traditions locales.
- `02-04-royaume-uni` - **Le Royaume-Uni des Îles et des Histoires** : Londres, Big Ben, bus rouges, langue anglaise, îles, jardins, contes et bibliothèques.
- `02-05-russie` - **La Russie aux Grands Espaces** : Moscou et Saint-Pétersbourg, pays entre Europe et Asie, forêts, neige, grands espaces, Transsibérien.

### Asie - Les Jardins d'Asie

**Durée estimée** : 34-36 minutes, 4 histoires pays.

- `03-01-chine` - **La Chine et le Long Mur** : Grande Muraille, Pékin, inventions anciennes, pandas et montagnes.
- `03-02-inde` - **L'Inde aux Mille Couleurs** : Taj Mahal, couleurs, tissus, musique et fêtes, diversité des langues, tigres et éléphants.
- `03-03-japon` - **Le Japon entre Cerisiers et Trains Rapides** : Tokyo, cerisiers en fleurs, temples, jardins, respect de la nature, trains rapides et technologie.
- `03-04-indonesie` - **L'Indonésie des Îles et des Volcans** : îles et volcans, forêts tropicales, orangs-outans, vie près de la mer.

### Amérique - Les Horizons d'Amérique

**Durée estimée** : 34-36 minutes, 4 histoires pays.

- `04-01-canada` - **Le Canada des Lacs et des Forêts** : forêts, lacs et grands espaces, français et anglais, castor, élan, ours, saisons marquées.
- `04-02-etats-unis` - **Les États-Unis des Villes et des Canyons** : New York et gratte-ciel, Grand Canyon et parcs naturels, diversité des paysages et cultures, cinéma, musique et inventions.
- `04-03-mexique` - **Le Mexique des Couleurs et des Histoires** : civilisations anciennes comme les Mayas, couleurs, marchés et musiques, cactus, déserts et jungles, fêtes familiales et traditions.
- `04-04-bresil` - **Le Brésil de la Forêt et de la Musique** : Amazonie, Rio de Janeiro, musique, carnaval et football, biodiversité et protection de la nature.

### Océanie - Les Îles d'Océanie

**Durée estimée** : 34-36 minutes, 4 histoires pays.

- `05-01-australie` - **L'Australie du Désert Rouge et du Récif** : kangourous et koalas, désert rouge et Outback, Grande Barrière de corail, Sydney et villes côtières.
- `05-02-nouvelle-zelande` - **La Nouvelle-Zélande des Montagnes et du Kiwi** : montagnes, volcans et lacs, kiwi, culture maorie présentée avec respect, nature protégée.
- `05-03-fidji` - **Les Fidji des Lagons Bleus** : îles du Pacifique, récifs, lagons, poissons colorés, accueil, chants, vie de village, protection de l'océan.
- `05-04-papouasie-nouvelle-guinee` - **La Papouasie-Nouvelle-Guinée aux Oiseaux de Paradis** : grande île au nord de l'Australie, montagnes, forêts tropicales, rivières, grande diversité de langues et cultures, oiseaux de paradis, artisanat et respect des communautés.

## Contenu en cours

Les quatre histoires pays de l'**Amérique** sont rédigées en premier pour validation du ton, de la durée et du niveau pédagogique avant de continuer les autres continents.
