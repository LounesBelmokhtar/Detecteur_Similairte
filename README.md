# Détecteur de similarité entre codes sources

Outil d'aide à la détection de ressemblances entre fichiers de code source,
développé dans le cadre d'un projet universitaire. L'outil compare un fichier
de référence à un ou plusieurs candidats et produit un score de similarité
entre 0 et 100 %, accompagné de fragments surlignés, d'une analyse détaillée
et d'exports CSV / HTML.

> **Avertissement éthique** — Un score de similarité ne constitue pas, à lui
> seul, une preuve de plagiat. Il signale des ressemblances statistiques et
> structurelles devant impérativement faire l'objet d'un examen critique par
> un humain qualifié.

## Fonctionnalités

- **Trois niveaux de comparaison** complémentaires :
  1. **Textuel** — normalisation basique, ratio de lignes, Levenshtein,
     n-grammes, LCS ; sensible au formatage (repère les copies brutes) ;
  2. **Tokens & transformations** — lexage via *tree-sitter*, normalisation
     des identifiants / nombres / chaînes, *winnowing* (fenêtre glissante),
     *Greedy String Tiling* (GST), appariement de fonctions, détection de
     renommage bijectif ; robuste au renommage, au déplacement de fonctions
     et au reformatage ;
  3. **Structure inter-langages** — AST unifié via *tree-sitter*, réduction
     aux nœuds canoniques (`LOOP`, `IF`, `FUNCTION_DEF`, …), séquences de
     k-grammes + LCS, distance de variation totale des descripteurs
     structurels, édition d'arbre simplifiée avec appariement glouton par
     catégorie, reconnaissance heuristique de motifs algorithmiques
     (tri à bulles, recherche binaire, fibonacci, PGCD, factorielle, primalité) ;
     fonctionne entre Python, Java, C et JavaScript.
- **Interface graphique** (Tkinter) : sélection des fichiers, choix du niveau,
  tableau de résultats triable, visualisation matplotlib, vue de diff avec
  surlignage des fragments.
- **Interface en ligne de commande** (`cli.py`) : comparaison fichier par
  fichier ou par répertoire, niveau « auto » (niveau 2 pour un même langage,
  niveau 3 dès que les langages diffèrent — choix fait **par couple**
  référence/candidat), exports CSV et HTML.
- **Jeu d'essai** (`samples/`) : copies, reformatages, renommages,
  réordonnancements, cas limites et paires cross-langages.
- **Évaluation** (`evaluation/`) : scénarios étiquetés, métriques de
  classification (précision, rappel, F1), graphiques matplotlib.
- **Tests** (`tests/`) : 80 tests pytest couvrant le cœur, les trois niveaux
  et les exigences de la spécification.

## Installation

Prérequis : Python ≥ 3.10 (développé sous 3.14), accès réseau pour pip.

```bash
pip install -r requirements.txt
```

Dépendances : `tree-sitter`, `tree-sitter-python`, `tree-sitter-java`,
`tree-sitter-c`, `tree-sitter-cpp`, `tree-sitter-javascript`,
`matplotlib`, `numpy`, `pytest`.

## Utilisation

### Interface graphique

```bash
python main.py
```

1. Charger un fichier de référence ;
2. Ajouter un ou plusieurs candidats (fichier ou répertoire) ;
3. Choisir le niveau (1, 2, 3 ou auto) ;
4. Lancer la comparaison ;
5. Consulter le tableau, la visualisation et le diff ; exporter en CSV/HTML.

### Ligne de commande

```bash
# Niveau 2 sur plusieurs candidats
python cli.py --ref samples/identical/bubble_sort_ref.py \
     --cands samples/modified/bubble_sort_renamed.py samples/unrelated/gcd.py \
     --level 2

# Parcours d'un répertoire + exports
python cli.py --ref samples/identical/bubble_sort_ref.py \
     --cands-dir samples/cross_language --level auto \
     --csv rapport.csv --html rapport.html
```

Options principales : `--level {1,2,3,auto}`, `--kgram N`,
`--gst-min N`, `--min-frag N`, `--keep-comments`, `--csv PATH`,
`--html PATH`.

### Exécution sans Python (exécutable Windows)

Des exécutables autonomes sont fournis dans `dist\` :

- **`dist\DetecteurDeSimilarite\`** — version graphique ; lancer
  `DetecteurDeSimilarite.exe` (dossier `samples\` joint pour démonstration).
- **`dist\CLI-Similarite\`** — version console ; même usage que `cli.py` :

```bash
dist\CLI-Similarite\CLI-Similarite.exe --ref samples\identical\bubble_sort_ref.py \
     --cands samples\modified\bubble_sort_renamed.py --level auto
```

Pour **reconstruire** les exécutables (après modification du code) :

```bash
pip install pyinstaller
py -m PyInstaller detecteur_similarite.spec --noconfirm   # version graphique
py -m PyInstaller cli_similarite.spec --noconfirm         # version console
```

Les spécifications `*.spec` déclarent les grammaires *tree-sitter* comme
imports cachés (elles sont chargées dynamiquement et sinon absentes du
paquet). Chaque dossier `dist\...` contient déjà une copie de `samples\`.

### Évaluation

```bash
python -m evaluation.run_evaluation                    # rapport texte
python -m evaluation.run_evaluation --csv resultats.csv --plots
```

### Tests

```bash
python -m pytest tests -q
```

## Architecture

Le projet suit une architecture **MVC** :

- **Modèle (`models/`)** — logique métier pure, sans aucune dépendance Tkinter.
- **Vue (`views/`)** — interface Tkinter et rendu console ; aucune logique métier.
- **Contrôleur (`controllers/`)** — orchestration modèle ↔ vue, threads, exports.

```
projet/
├── main.py                    # Point d'entrée de l'interface graphique
├── cli.py                     # Point d'entrée de la ligne de commande
├── controllers/               # C — orchestration
│   ├── app_controller.py      #   Comparaison GUI, exports, ouverture du diff
│   └── cli_controller.py      #   Parcours complet de la CLI
├── models/                    # M — logique métier (sans Tkinter)
│   ├── config.py              #   Constantes, seuils, poids, couleurs
│   ├── loader.py              #   Chargement multi-encodages, détection binaire/langage
│   ├── lexer.py               #   Lexage tree-sitter + repli regex
│   ├── normalizer.py          #   Normalisation textuelle et token, renommage
│   ├── canonical.py           #   Catégories canoniques inter-langages
│   ├── ast_parser.py          #   AST unifié, extraction de fonctions, complexité
│   ├── fragments.py           #   Fragments de correspondance
│   ├── ranking.py             #   Classement et niveaux d'alerte
│   ├── methods/               #   Les trois niveaux de comparaison
│   │   ├── base.py            #     Protocole SimilarityMethod, SimilarityResult
│   │   ├── level1_text.py     #     Textuel (SequenceMatcher, Levenshtein, LCS…)
│   │   ├── level2_tokens.py   #     Winnowing, GST, appariement de fonctions
│   │   └── level3_structure.py#     AST unifié, édition d'arbre, motifs
│   └── report/                #   Exports CSV et HTML
├── views/                     # V — présentation
│   ├── main_window.py         #   Fenêtre principale (en-tête, corps, statut)
│   ├── control_panel.py       #   Barre latérale de configuration
│   ├── results_view.py        #   Tableau classé + graphique
│   ├── diff_view.py           #   Vue côte à côte surlignée
│   ├── theme.py               #   Palette et styles ttk
│   └── console.py             #   Rendu texte de la CLI
├── evaluation/                # Scénarios étiquetés, métriques, graphiques
├── tests/                     # Tests pytest (cœur, niveaux 1/2/3, GUI)
├── samples/                   # Jeu d'essai organisé par catégorie
└── docs/rapport.md            # Rapport de projet
```

## Seuils et interprétation

| Score    | Niveau d'alerte | Signification indicative        |
|----------|-----------------|---------------------------------|
| < 30 %   | 🟢 Faible       | Peu de ressemblances détectées  |
| 30–70 %  | 🟠 Modéré       | Ressemblances notables          |
| > 70 %   | 🔴 Élevé        | Fortes ressemblances            |

Le niveau 3 est conçu pour la comparaison **inter-langages** : sur des
fichiers de même langage, préférer les niveaux 1 et 2, plus discriminants
(voir `docs/rapport.md` pour la discussion détaillée).

## Auteur

Projet réalisé dans le cadre d'un cours de programmation avancée —
utilisation pédagogique.
