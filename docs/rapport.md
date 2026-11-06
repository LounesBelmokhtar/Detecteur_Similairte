# Rapport de projet — Détecteur de similarité entre codes sources

## 1. Contexte et objectifs

Ce projet porte sur la conception et l'implémentation d'un outil d'aide à la
détection de ressemblances entre codes sources, destiné à un usage pédagogique
(accompagnement à la détection de plagiat dans un cadre universitaire). L'outil
reçoit un fichier de référence et un ou plusieurs candidats, et produit pour
chacun un score de similarité entre 0 et 100 %, des fragments surlignés et une
analyse détaillée par composant.

**Objectifs fonctionnels :**

- comparer des fichiers de même langage (Python, Java, C, JavaScript) à trois
  niveaux de profondeur croissante ;
- comparer des algorithmes **équivalents dans des langages différents** ;
- être robuste aux transformations courantes : renommage d'identifiants,
  déplacement de fonctions, reformatage, ajout de code mort ;
- rester discriminant sur des codes sans relation ;
- proposer une interface graphique (Tkinter) et une ligne de commande ;
- exporter les résultats en CSV et HTML.

**Objectifs techniques :** code commenté en français, typage statique
(*type hints*), architecture en couches (le cœur n'importe jamais Tkinter),
algorithmes implémentés explicitement plutôt que délégués, tests automatisés.

## 2. Architecture générale

Le projet suit une architecture **MVC** (Modèle–Vue–Contrôleur) :

| Couche | Rôle | Paquets |
|--------|------|---------|
| Modèle (M) | Chargement, lexage, normalisation, AST unifié, comparaison, classement, exports | `models/`, `models/methods/`, `models/report/` |
| Vue (V) | Fenêtre Tkinter et rendu console, sans logique métier | `views/`, `cli.py` |
| Contrôleur (C) | Orchestration modèle ↔ vue, threading, sélection de niveau, exports | `controllers/` |
| Évaluation | Scénarios étiquetés, métriques, graphiques | `evaluation/`, `tests/` |

La règle de dépendance est unidirectionnelle : les vues dépendent du modèle
pour ses types de données, le modèle n'importe jamais les vues ni Tkinter, et
les contrôleurs sont les seuls à coordonner les deux. Les points d'entrée
`main.py` (GUI) et `cli.py` (console) instancient la vue puis le contrôleur.

Toutes les constantes (seuils, poids d'agrégation, listes de bibliothèque
standard, couleurs) sont centralisées dans `models/config.py`. Le protocole
`SimilarityMethod` (`models/methods/base.py`) uniformise l'interface des trois
niveaux : chaque méthode expose `compare(reference, candidate) → SimilarityResult`.

### 2.1 Chargement multi-encodages

`models/loader.py` détecte les fichiers binaires (octet nul dans les 1024
premiers octets), tente successivement UTF-8, UTF-8-SIG, Latin-1 puis CP1252,
normalise les fins de ligne et détecte le langage par extension puis par
heuristiques de contenu.

### 2.2 Lexage et normalisation

Le lexage s'appuie sur **tree-sitter** quand la grammaire du langage est
disponible, avec un repli par expressions régulières. Les littéraux de chaîne
et les commentaires sont émis comme des tokens *atomiques* (les enfants
anonymes de ces nœuds ne doivent pas être tokenisés séparément, sous peine de
perdre la valeur du littéral).

Deux niveaux de normalisation sont fournis :

- **Niveau 1** : suppression des commentaires, réduction des espacements,
  comparaison ligne à ligne ;
- **Niveau 2** : chaque identifiant hors bibliothèque standard devient `ID`,
  chaque nombre `NUM`, chaque chaîne `STR` ; les identifiants de la
  bibliothèque standard (whitelists par langage) sont conservés car ils
  participent au style de l'algorithme.

La détection de **renommage bijectif** (`detect_bijective_renaming`) travaille
sur les identifiants *bruts* (avant normalisation, qui effacerait justement
les noms à comparer) et recalcule une cohérence positionnelle.

### 2.3 AST unifié inter-langages

`models/canonical.py` définit un ensemble de **catégories canoniques**
(`FUNCTION_DEF`, `PARAM`, `LOOP`, `IF`, `ELSE`, `SWITCH`, `RETURN`, `ASSIGN`,
`CALL`, `BINARY_OP`, `UNARY_OP`, `INDEX`, `DECLARE`, `LITERAL`, `BLOCK`, …)
et un mappage par langage depuis les types de nœuds tree-sitter. Des
heuristiques génériques « sûr-mots » complètent le mappage (comparaison par
égalité exacte ou préfixe, jamais par simple sous-chaîne, afin d'éviter le
faux positif historique `identifier` contient `if`).

`models/ast_parser.py` construit des `UniformASTNode` (type, langage, lignes,
texte, catégorie canonique, enfants), **aplatit les enveloppes non
canoniques** (un nœud sans catégorie dont un enfant en porte une est remplacé
par cet enfant), et fournit l'extraction des unités fonctionnelles, la
complexité cyclomatique approximative et la profondeur d'imbrication.

## 3. Les trois niveaux de comparaison

### 3.1 Niveau 1 — textuel

Agrégation pondérée (`models.config.WEIGHTS_LEVEL1`) de quatre mesures :

1. **Ratio SequenceMatcher** sur les lignes normalisées (difflib) ;
2. **Similarité de Levenshtein** normalisée, implémentée avec une mémoire
   optimisée en deux lignes (O(min(m, n)) espaces) ;
3. **Jaccard sur n-grammes** de tokens (n = 3) ;
4. **LCS** (plus longue sous-séquence commune) au niveau des lignes.

Les fragments de correspondance sont extraits des run communs du
SequenceMatcher, fusionnés s'ils sont adjacents. Ce niveau est volontairement
sensible au formatage : c'est le détecteur de copies brutes.

### 3.2 Niveau 2 — tokens et transformations

Quatre composantes (`models.config.WEIGHTS_LEVEL2`) :

1. **Winnowing** — k-grammes de tokens normalisés (k = 5) hachés, fenêtre
   glissante de taille w = 4, sélection du minimum de chaque fenêtre ; la
   similarité est le *containment* symétrique
   `(|A ∩ B| / min(|A|, |B|)) × 100`, adapté au cas où un fichier est
   inclus dans un plus grand (code mort ajouté) ;
2. **Greedy String Tiling (GST)** — tuiles maximales de longueur ≥ 4, couvrant
   greedy ; robuste par nature aux déplacements de blocs ;
3. **Appariement de fonctions** — extraction des unités fonctionnelles des
   deux côtés, appariement par score GST inter-fonction, agrégation
   pondérée par la taille ;
4. **Sous-arbres AST** — comparaison des sous-arbres canoniques appariés.

Un diagnostic de renommage bijectif est ajouté dans les notes quand la
cohérence dépasse 70 % et qu'au moins un identifiant réellement renommé est
présent (ex. `arr→tab`, `n→len`).

### 3.3 Niveau 3 — structure inter-langages

Ce niveau compare des représentations **indépendantes du langage**
(`models.config.WEIGHTS_LEVEL3`) :

1. **Séquence canonique** — parcours en profondeur des seuls nœuds
   canoniques, k-grammes (k = 3) avec Jaccard + LCS normalisé ; mesure la
   *séquence* des concepts (LOOP→LOOP→IF vs LOOP→IF distingue un tri
   imbriqué d'une recherche) ;
2. **Descripteur structurel** — vecteur creux : histogramme des catégories,
   profil d'imbrication, complexité, ratios de contrôle, **transitions**
   (bigrammes de catégories de contrôle de flux) ; comparable par la
   **distance de variation totale** (L1 normalisée), plus discriminante que
   le cosinus sur de petits programmes où les dimensions courantes dominent ;
3. **Édition d'arbre** — les arbres sont d'abord **réduits aux nœuds
   canoniques** (`reduce_to_canonical`) : les enveloppes spécifiques au
   langage disparaissent et `method_declaration` (Java) s'aligne sur
   `function_definition` (C/Python) ; la comparaison recurse avec appariement
   *glouton par catégorie* des enfants (et non par position), pondéré par la
   taille des sous-arbres ;
4. **Motifs algorithmiques** — heuristiques regex (commentaires préalablement
   supprimés) reconnaissant tri à bulles, recherche binaire, fibonacci,
   PGCD, factorielle, primalité, tri par insertion/sélection.

Pour les comparaisons cross-langages, un facteur d'échelle configurable
(`LEVEL3_SCALE_FACTOR = 1.15`) compense la pénalité structurelle propre aux
différences de grammaire, dans la limite de 100 %.

## 4. Jeu d'essai

`samples/` est organisé en cinq catégories :

- **identical/** — copie byte-à-byte et reformatage du tri à bulles Python ;
- **modified/** — renommage, réordonnancement, conversion for→while, code
  mort, cas combiné ;
- **unrelated/** — recherche binaire, factorielle, PGCD (Python) ;
- **cross_language/** — bubble sort, fibonacci, PGCD, recherche binaire,
  factorielle, primalité dans jusqu'à quatre langages, plus une paire
  négative explicite ;
- **edge_cases/** — fichier vide, commentaires seuls, binaire, gros fichier
  (~1 350 lignes).

`evaluation/scenarios.py` étiquette 24 paires avec leur vérité terrain
(`expected_alert`) dans quatre catégories : *identique*, *modifie*,
*sans_relation*, *cross_langue*.

## 5. Résultats d'évaluation

Évaluation complète : `python -m evaluation.run_evaluation`
(détail par scénario, métriques de classification, scores moyens ;
graphiques avec `--plots`).

### 5.1 Scores moyens par catégorie (%)

| Catégorie      | Niveau 1 | Niveau 2 | Niveau 3 |
|----------------|---------:|---------:|---------:|
| identique      |     77.8 |    100.0 |     99.9 |
| modifie        |     24.6 |     74.4 |     67.0 |
| sans relation  |      3.9 |     18.2 |     35.7 |
| cross-langue   |      0.0 |     18.6 |     57.2 |

### 5.2 Métriques de classification (seuil d'alerte = 30 %)

| Niveau | Accuracy | Précision | Rappel | F1   |
|-------:|---------:|----------:|-------:|-----:|
| 1      |    62.5% |    100.0% |  35.7% | 52.6% |
| 2      |    66.7% |     87.5% |  50.0% | 63.6% |
| 3      |    58.3% |     58.3% | 100.0% | 73.7% |

**Lecture.** Le rappel croît avec le niveau (35.7 → 50 → 100 %) et la
précision décroît (100 → 87.5 → 58.3 %) : chaque niveau élargit le champ des
transformations détectées au prix de quelques faux positifs. Le niveau 3,
pensé pour le cross-langages, détecte **toutes** les paires d'algorithme
équivalent (rappel 100 %) mais signale aussi des paires de même langage sans
relation — d'où la recommandation d'utiliser les niveaux 1–2 pour les
comparaisons de même langage (le mode « auto » de la CLI **et** de la GUI
applique automatiquement cette règle, par couple référence/candidat).

### 5.3 Conformité aux exigences de la spécification

| Exigence | Résultat |
|----------|----------|
| Copies identiques ≥ 95 % | 100 % (tous niveaux) ✓ |
| Renommage seul ≥ 80 % (niveau 2) | 100 % ✓ |
| Fonctions déplacées : niveau 2 ≫ niveau 1 | 85.8 % vs 35.2 % ✓ |
| Sans relation < 30 % (niveaux 1–2) | max 25.6 % au niveau 2 ✓ |
| Cross-langage : même algorithme > algorithmes différents | min 60.8 % vs max 40.5 % (marge 20 pts) ✓ |

### 5.4 Exemples représentatifs (niveau 3)

| Paire | Score | Commentaire |
|-------|------:|-------------|
| bubble_sort Python ↔ Java | 64.6 | même algorithme, langages différents |
| fibonacci Python ↔ C | 72.1 | récursion structurellement alignée |
| primality Python ↔ Java | 84.1 | structure quasi isomorphe |
| fibonacci Python ↔ bubble sort C | 30.6 | algorithmes différents |
| bubble sort Python ↔ PGCD C | 33.3 | algorithme différent |

## 6. Limites et pistes d'amélioration

- **Faux positifs du niveau 3 sur petit fichier** : des programmes courts de
  même langage partagent des proportions structurelles proches (vecteurs
  dominés par `IF`/`LOOP`). Les transitions et la variation totale atténuent
  le phénomène sans l'éliminer ; un seuillage spécifique au niveau 3 ou un
  mélange niveau 2/3 pour les paires de même langage serait une piste.
- **Motifs algorithmiques heuristiques** : limités à une liste fermée de
  motifs et sensibles aux styles d'écriture ; une généralisation par
  apprentissage supervisé serait possible avec un corpus annoté.
- **Édition d'arbre simplifiée** : l'appariement glouton par catégorie n'est
  pas optimal (Zhang-Shasha exact coûteux) ; acceptable sur les tailles
  observées grâce à la borne de profondeur.
- **Bibliothèques standard** : les whitelists sont fixes ; une extraction
  dynamique des imports améliorerait la normalisation.
- **Scalabilité** : le winnowing et le GST sont linéaires, mais la charge de
  tree-sitter croît avec la taille des fichiers ; le mode répertoire compare
  chaque candidat indépendamment (pas de matrice complète optimisée).

## 7. Considérations éthiques

L'outil est un **aide à la décision**, jamais un jugement. Chaque écran et
chaque export rappellent que :

> Un score de similarité ne constitue pas, à lui seul, une preuve de plagiat.
> Il signale des ressemblances statistiques et structurelles devant
> impérativement faire l'objet d'un examen critique par un humain qualifié.

Les seuils d'alerte (30 % / 70 %) sont des repères indicatifs, ajustables
dans `models/config.py`, et ne valent que dans le contexte d'un cours, d'un couple
de consignes et d'un corpus donné. L'usage de l'outil doit être déclaré aux
étudiants et encadré par le règlement de l'établissement.

## 8. Conclusion

Le projet atteint les objectifs fixés : trois niveaux de comparaison
complémentaires, robustesse démontrée au renommage (100 % au niveau 2) et au
reformatage, détection des copies brutes (100 % au niveau 1), et discrimination
inter-langages (mêmes algorithmes 60–84 % contre 30–41 % pour des algorithmes
différents). La couverture de tests (80 tests), le jeu d'étiqueté de 24
scénarios et les exports CSV/HTML/figures facilitent la reproductibilité et
l'exploitation pédagogique. Les limites identifiées (faux positifs du niveau 3
sur petits fichiers, motifs heuristiques) ouvrent des pistes d'amélioration
naturelles sans remettre en cause l'architecture.
