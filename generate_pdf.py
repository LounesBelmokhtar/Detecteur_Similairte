# -*- coding: utf-8 -*-
"""Génère un rapport PDF détaillé du projet Détecteur de similarité."""

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak,
    ListFlowable, ListItem, KeepTogether,
)
from reportlab.pdfgen import canvas

OUT = r"C:\Projet-PA\docs\rapport_projet.pdf"

# ---------- styles ----------
styles = getSampleStyleSheet()
NAVY = colors.HexColor("#1f2937")
INDIGO = colors.HexColor("#4f46e5")
GREY = colors.HexColor("#6b7280")
LIGHT = colors.HexColor("#eef2ff")

title_style = ParagraphStyle("Title", parent=styles["Title"], fontName="Helvetica-Bold",
                            fontSize=26, leading=32, textColor=NAVY, alignment=TA_CENTER,
                            spaceAfter=6)
subtitle_style = ParagraphStyle("Subtitle", parent=styles["Normal"], fontName="Helvetica",
                               fontSize=12, leading=16, textColor=GREY, alignment=TA_CENTER,
                               spaceAfter=4)
h1_style = ParagraphStyle("H1", parent=styles["Heading1"], fontName="Helvetica-Bold",
                          fontSize=17, leading=22, textColor=NAVY, spaceBefore=16,
                          spaceAfter=8, borderPadding=(0, 0, 4, 0))
h2_style = ParagraphStyle("H2", parent=styles["Heading2"], fontName="Helvetica-Bold",
                          fontSize=13, leading=17, textColor=INDIGO, spaceBefore=12,
                          spaceAfter=6)
h3_style = ParagraphStyle("H3", parent=styles["Heading3"], fontName="Helvetica-Bold",
                          fontSize=11, leading=14, textColor=NAVY, spaceBefore=8,
                          spaceAfter=4)
body_style = ParagraphStyle("Body", parent=styles["Normal"], fontName="Helvetica",
                            fontSize=10.5, leading=14.5, alignment=TA_JUSTIFY,
                            spaceAfter=6)
bullet_style = ParagraphStyle("Bullet", parent=body_style, leftIndent=16, bulletIndent=6,
                             spaceAfter=3)
small_style = ParagraphStyle("Small", parent=body_style, fontSize=9, leading=12,
                            textColor=GREY)
code_style = ParagraphStyle("Code", parent=styles["Code"], fontName="Courier",
                           fontSize=9, leading=12, backColor=colors.HexColor("#f3f4f6"),
                           borderPadding=6, leftIndent=8, rightIndent=8, spaceAfter=8)

def P(text, style=body_style):
    return Paragraph(text, style)

def H1(t): return Paragraph(t, h1_style)
def H2(t): return Paragraph(t, h2_style)
def H3(t): return Paragraph(t, h3_style)

def bullet(items, style=bullet_style):
    return ListFlowable(
        [ListItem(Paragraph(i, style), bulletColor=INDIGO) for i in items],
        bulletType="bullet", start="•", leftIndent=18, bulletFontName="Helvetica",
    )

def numbered(items):
    return ListFlowable(
        [ListItem(Paragraph(i, bullet_style), bulletColor=INDIGO) for i in items],
        bulletType="1", leftIndent=18,
    )

def make_table(header, rows, widths=None, font_size=9):
    data = [header] + rows
    t = Table(data, colWidths=widths, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), INDIGO),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), font_size),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#d1d5db")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f9fafb")]),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return t

# ---------- document ----------
doc = SimpleDocTemplate(OUT, pagesize=A4,
                        leftMargin=2*cm, rightMargin=2*cm,
                        topMargin=2*cm, bottomMargin=2*cm,
                        title="Détecteur de similarité entre codes sources",
                        author="Projet universitaire")

story = []

# ========== PAGE DE GARDE ==========
story.append(Spacer(1, 4*cm))
story.append(Paragraph("Détecteur de similarité", title_style))
story.append(Paragraph("entre codes sources", title_style))
story.append(Spacer(1, 0.6*cm))
story.append(Paragraph("Rapport détaillé du projet", subtitle_style))
story.append(Spacer(1, 0.4*cm))
story.append(Paragraph("Comparaison textuelle, lexicale et structurelle", subtitle_style))
story.append(Paragraph("Python · Java · C · C++ · JavaScript", subtitle_style))
story.append(Spacer(1, 2*cm))

meta = [
    ["Langage principal", "Python ≥ 3.10 (développé sous 3.14)"],
    ["Architecture", "MVC (Modèle / Vue / Contrôleur)"],
    ["Interface graphique", "Tkinter + matplotlib"],
    ["Interface CLI", "argparse (cli.py)"],
    ["Moteur d'analyse", "tree-sitter + algorithmes MOSS/JPlag"],
    ["Tests", "84 tests pytest (100 % réussite)"],
    ["Licence / usage", "Pédagogique (projet universitaire)"],
]
story.append(make_table(["Élément", "Détail"], meta, widths=[5*cm, 11*cm]))
story.append(Spacer(1, 1.5*cm))
story.append(Paragraph("Avertissement éthique : un score de similarité ne constitue pas, à lui seul, "
                      "une preuve de plagiat. Il signale des ressemblances statistiques et structurelles "
                      "devant impérativement faire l'objet d'un examen critique par un humain qualifié.",
                      small_style))
story.append(PageBreak())

# ========== TABLE DES MATIÈRES ==========
story.append(H1("Table des matières"))
toc = [
    "1. Présentation du projet",
    "2. Fonctionnalités",
    "3. Architecture MVC",
    "4. Installation",
    "5. Utilisation de l'interface graphique",
    "6. Utilisation de la ligne de commande (CLI)",
    "7. Les trois niveaux de comparaison",
    "   7.1 Niveau 1 — Comparaison textuelle",
    "   7.2 Niveau 2 — Tokens et transformations",
    "   7.3 Niveau 3 — Structure inter-langages",
    "8. Paramètres de configuration",
    "9. Seuils et interprétation des scores",
    "10. Structure des fichiers du projet",
    "11. Tests automatisés",
    "12. Évaluation des performances",
    "13. Exécutables autonomes (Windows)",
    "14. Exports CSV et HTML",
    "15. Avertissement éthique",
    "16. Auteur",
]
for line in toc:
    story.append(Paragraph(line, body_style))
story.append(PageBreak())

# ========== 1. PRÉSENTATION ==========
story.append(H1("1. Présentation du projet"))
story.append(P("Le <b>Détecteur de similarité entre codes sources</b> est un outil d'aide à la détection "
              "de ressemblances entre fichiers de code source, développé dans le cadre d'un projet "
              "universitaire. Il compare un fichier de référence à un ou plusieurs candidats et produit "
              "un score de similarité entre 0 et 100 %, accompagné de fragments surlignés, d'une "
              "analyse détaillée et d'exports CSV / HTML."))
story.append(P("L'outil est conçu pour assister (et non remplacer) l'examen humain : il signale des "
              "ressemblances statistiques et structurelles que l'enseignant doit ensuite interpréter "
              "critiquement."))
story.append(P("Trois niveaux de comparaison complémentaires sont proposés, allant de la copie brute "
              "à la reconnaissance de structures algorithmiques identiques dans des langages différents "
              "(Python, Java, C, C++, JavaScript)."))

# ========== 2. FONCTIONNALITÉS ==========
story.append(H1("2. Fonctionnalités"))
story.append(bullet([
    "<b>Trois niveaux de comparaison</b> complémentaires : textuel, tokens/transformations, "
    "structure inter-langages.",
    "<b>Interface graphique (Tkinter)</b> : sélection des fichiers, choix du niveau, tableau de "
    "résultats triable, visualisation matplotlib, vue de diff avec surlignage des fragments.",
    "<b>Interface en ligne de commande (cli.py)</b> : comparaison fichier par fichier ou par "
    "répertoire, niveau « auto » (niveau 2 pour un même langage, niveau 3 dès que les langages "
    "diffèrent — choix fait par couple référence/candidat), exports CSV et HTML.",
    "<b>Jeu d'essai (samples/)</b> : copies, reformatages, renommages, réordonnancements, "
    "cas limites et paires cross-langages.",
    "<b>Évaluation (evaluation/)</b> : scénarios étiquetés, métriques de classification "
    "(précision, rappel, F1), graphiques matplotlib.",
    "<b>Tests (tests/)</b> : 84 tests pytest couvrant le cœur, les trois niveaux et les "
    "exigences de la spécification.",
    "<b>Exécutables autonomes Windows</b> dans dist/ (PyInstaller).",
]))

# ========== 3. ARCHITECTURE ==========
story.append(H1("3. Architecture MVC"))
story.append(P("Le projet suit une architecture <b>MVC (Modèle / Vue / Contrôleur)</b> stricte :"))
story.append(bullet([
    "<b>Modèle (models/)</b> — logique métier pure, sans aucune dépendance Tkinter.",
    "<b>Vue (views/)</b> — interface Tkinter et rendu console ; aucune logique métier.",
    "<b>Contrôleur (controllers/)</b> — orchestration modèle ↔ vue, threads, exports.",
]))
story.append(P("Arborescence principale :"))
tree_rows = [
    ["main.py", "Point d'entrée de l'interface graphique"],
    ["cli.py", "Point d'entrée de la ligne de commande"],
    ["controllers/app_controller.py", "Comparaison GUI, exports, ouverture du diff"],
    ["controllers/cli_controller.py", "Parcours complet de la CLI"],
    ["models/config.py", "Constantes, seuils, poids, couleurs"],
    ["models/loader.py", "Chargement multi-encodages, détection binaire/langage"],
    ["models/lexer.py", "Lexage tree-sitter + repli regex"],
    ["models/normalizer.py", "Normalisation textuelle et token, renommage"],
    ["models/canonical.py", "Catégories canoniques inter-langages"],
    ["models/ast_parser.py", "AST unifié, extraction de fonctions, complexité"],
    ["models/fragments.py", "Fragments de correspondance"],
    ["models/ranking.py", "Classement et niveaux d'alerte"],
    ["models/methods/base.py", "Protocole SimilarityMethod, SimilarityResult"],
    ["models/methods/level1_text.py", "Textuel (SequenceMatcher, Levenshtein, LCS…)"],
    ["models/methods/level2_tokens.py", "Winnowing, GST, appariement de fonctions"],
    ["models/methods/level3_structure.py", "AST unifié, édition d'arbre, motifs"],
    ["models/report/export_csv.py", "Export CSV"],
    ["models/report/export_html.py", "Export HTML"],
    ["views/main_window.py", "Fenêtre principale (en-tête, corps, statut)"],
    ["views/control_panel.py", "Barre latérale de configuration"],
    ["views/results_view.py", "Tableau classé + graphique"],
    ["views/diff_view.py", "Vue côte à côte surlignée"],
    ["views/theme.py", "Palette et styles ttk"],
    ["views/console.py", "Rendu texte de la CLI"],
    ["evaluation/", "Scénarios étiquetés, métriques, graphiques"],
    ["tests/", "Tests pytest (cœur, niveaux 1/2/3, GUI)"],
    ["samples/", "Jeu d'essai organisé par catégorie"],
    ["docs/rapport.md", "Rapport de projet"],
]
story.append(make_table(["Fichier / dossier", "Rôle"], tree_rows, widths=[6.5*cm, 9.5*cm], font_size=8.5))

# ========== 4. INSTALLATION ==========
story.append(H1("4. Installation"))
story.append(P("Prérequis : Python ≥ 3.10 (développé sous 3.14), accès réseau pour pip."))
story.append(P("Dépendances : tree-sitter, tree-sitter-python, tree-sitter-java, tree-sitter-c, "
              "tree-sitter-cpp, tree-sitter-javascript, matplotlib, numpy, pytest."))
story.append(H3("Installation des dépendances"))
story.append(Paragraph("pip install -r requirements.txt", code_style))
story.append(H3("Lancement de l'interface graphique"))
story.append(Paragraph("python main.py", code_style))
story.append(H3("Lancement des tests"))
story.append(Paragraph("python -m pytest tests -q", code_style))

# ========== 5. GUI ==========
story.append(H1("5. Utilisation de l'interface graphique"))
story.append(numbered([
    "Charger un fichier de référence (bouton « Parcourir » dans la section ①).",
    "Ajouter un ou plusieurs candidats (fichier ou répertoire) dans la section ②.",
    "Choisir le niveau (1, 2, 3 ou auto) dans la section ③.",
    "Ajuster les paramètres avancés si besoin (section ④).",
    "Lancer la comparaison (bouton bleu « ▶ Comparer »).",
    "Consulter le tableau de classement, la visualisation et le diff.",
    "Exporter en CSV ou HTML via les boutons du bas.",
]))
story.append(P("La fenêtre principale présente :"))
story.append(bullet([
    "<b>En-tête</b> : titre, sous-titre, pastilles de seuils (faible / modéré / élevé).",
    "<b>Barre latérale gauche</b> : configuration (référence, candidats, niveau, paramètres), "
    "bouton Comparer, progression, exports.",
    "<b>Zone principale droite</b> : bandeau éthique, cartes de synthèse (candidats analysés, "
    "alertes élevées, score moyen, meilleur score), tableau classé, détail du candidat "
    "sélectionné, graphique à barres.",
]))
story.append(P("Un <b>double-clic</b> sur une ligne du tableau ouvre la vue côte à côte (diff) "
              "avec surlignage des fragments correspondants."))

# ========== 6. CLI ==========
story.append(H1("6. Utilisation de la ligne de commande (CLI)"))
story.append(P("Exemples d'utilisation :"))
story.append(Paragraph("python cli.py --ref samples/identical/bubble_sort_ref.py \\\n"
                      "     --cands samples/modified/bubble_sort_renamed.py samples/unrelated/gcd.py \\\n"
                      "     --level 2", code_style))
story.append(Paragraph("python cli.py --ref samples/identical/bubble_sort_ref.py \\\n"
                      "     --cands-dir samples/cross_language --level auto \\\n"
                      "     --csv rapport.csv --html rapport.html", code_style))
story.append(P("Options principales :"))
story.append(bullet([
    "<b>--level {1,2,3,auto}</b> : niveau de comparaison.",
    "<b>--kgram N</b> : taille des k-grammes (niveau 2).",
    "<b>--gst-min N</b> : longueur minimale d'une tuile GST.",
    "<b>--min-frag N</b> : longueur minimale d'un bloc commun (lignes).",
    "<b>--keep-comments</b> : conserver les commentaires.",
    "<b>--csv PATH</b> / <b>--html PATH</b> : exports.",
]))

# ========== 7. NIVEAUX ==========
story.append(H1("7. Les trois niveaux de comparaison"))
story.append(P("L'outil propose trois niveaux complémentaires, du plus sensible au plus "
              "structurel, ainsi qu'un mode « auto » qui choisit le niveau par couple "
              "référence/candidat (niveau 2 si même langage, niveau 3 si langages différents)."))

story.append(H2("7.1 Niveau 1 — Comparaison textuelle"))
story.append(P("Normalisation basique, ratio de lignes, Levenshtein, n-grammes, LCS. Sensible au "
              "formatage : repère les copies brutes."))
story.append(P("Combinaison pondérée (total = 1,0) :"))
story.append(make_table(["Composante", "Poids", "Description"],
    [["sequence_matcher", "0,35", "Ratio difflib SequenceMatcher"],
     ["levenshtein", "0,25", "Similarité de Levenshtein normalisée"],
     ["jaccard_ngrams", "0,25", "Jaccard sur n-grammes de tokens textuels"],
     ["lcs_lines", "0,15", "Plus longue sous-séquence commune (lignes)"]],
    widths=[4.5*cm, 2*cm, 9.5*cm]))
story.append(P("Paramètres : n-grammes de taille 4, bloc commun minimum de 3 lignes."))

story.append(H2("7.2 Niveau 2 — Tokens et transformations"))
story.append(P("Lexage via tree-sitter, normalisation des identifiants / nombres / chaînes, "
              "winnowing (fenêtre glissante), Greedy String Tiling (GST), appariement de "
              "fonctions, détection de renommage bijectif. Robuste au renommage, au déplacement "
              "de fonctions et au reformatage."))
story.append(make_table(["Composante", "Poids", "Description"],
    [["winnowing", "0,30", "Empreintes Winnowing (algorithme MOSS)"],
     ["gst", "0,35", "Greedy String Tiling (algorithme JPlag)"],
     ["function_matching", "0,20", "Appariement glouton des fonctions/méthodes"],
     ["ast_subtrees", "0,15", "Hash des sous-arbres normalisés"]],
    widths=[4.5*cm, 2*cm, 9.5*cm]))
story.append(P("Paramètres : k-grammes de taille 5, fenêtre de winnowing de 4, tuile GST "
              "minimale de 4 tokens."))
story.append(P("Les identifiants des bibliothèques standards (print, len, System.out, printf, "
              "console.log, std::cout, …) ne sont pas renommés en « ID » afin de conserver "
              "l'information discriminante."))

story.append(H2("7.3 Niveau 3 — Structure inter-langages"))
story.append(P("AST unifié via tree-sitter, réduction aux nœuds canoniques (LOOP, IF, "
              "FUNCTION_DEF, …), séquences de k-grammes + LCS, distance de variation totale "
              "des descripteurs structurels, édition d'arbre simplifiée avec appariement "
              "glouton par catégorie, reconnaissance heuristique de motifs algorithmiques "
              "(tri à bulles, recherche binaire, fibonacci, PGCD, factorielle, primalité). "
              "Fonctionne entre Python, Java, C et JavaScript."))
story.append(make_table(["Composante", "Poids", "Description"],
    [["canonical_sequence", "0,50", "K-grammes + LCS sur séquence de nœuds canoniques"],
     ["structural_vector", "0,20", "Distance de variation totale des descripteurs"],
     ["tree_similarity", "0,15", "Édition d'arbre réduit, appariement par catégorie"],
     ["pattern_heuristics", "0,15", "Reconnaissance heuristique de motifs algorithmiques"]],
    widths=[4.5*cm, 2*cm, 9.5*cm]))
story.append(P("La séquence canonique pèse le plus (mesure la plus discriminante entre "
              "algorithmes). Un facteur d'échelle multiplicatif doux de 1,15 compense la baisse "
              "mécanique des scores due aux particularités de syntaxe de chaque langage."))

# ========== 8. PARAMÈTRES ==========
story.append(H1("8. Paramètres de configuration"))
story.append(make_table(["Paramètre", "Défaut", "Plage", "Rôle"],
    [["k-grammes (niv. 2)", "5", "2–12", "Taille des k-grammes de tokens"],
     ["Tuile min. (GST)", "4", "2–20", "Longueur minimale d'une tuile GST"],
     ["Bloc min. (lignes)", "3", "1–20", "Longueur min d'un bloc commun"],
     ["Seuil d'alerte (%)", "70", "0–100", "Seuil au-dessus duquel l'alerte est élevée"],
     ["Ignorer les commentaires", "oui", "—", "Retire les commentaires avant analyse"],
     ["Ignorer les imports", "oui", "—", "Retire les lignes d'import/include"]],
    widths=[4.5*cm, 2*cm, 2.5*cm, 7*cm]))

# ========== 9. SEUILS ==========
story.append(H1("9. Seuils et interprétation des scores"))
story.append(make_table(["Score", "Niveau d'alerte", "Signification indicative"],
    [["< 30 %", "Faible (vert)", "Peu de ressemblances détectées"],
     ["30–70 %", "Modéré (orange)", "Ressemblances notables"],
     ["> 70 %", "Élevé (rouge)", "Fortes ressemblances"]],
    widths=[3*cm, 4*cm, 9*cm]))
story.append(P("Le niveau 3 est conçu pour la comparaison inter-langages : sur des fichiers de "
              "même langage, préférer les niveaux 1 et 2, plus discriminants."))

# ========== 10. STRUCTURE ==========
story.append(H1("10. Structure des fichiers du projet"))
story.append(P("Voir la section 3 (tableau de l'architecture). Le projet contient également :"))
story.append(bullet([
    "<b>evaluation/</b> : scénarios étiquetés, métriques de classification "
    "(précision, rappel, F1), graphiques matplotlib.",
    "<b>samples/</b> : copies, reformatages, renommages, réordonnancements, "
    "cas limites et paires cross-langages.",
    "<b>dist/</b> : exécutables autonomes Windows (DetecteurDeSimilarite.exe, "
    "CLI-Similarite.exe).",
    "<b>docs/rapport.md</b> : rapport de projet détaillé.",
]))

# ========== 11. TESTS ==========
story.append(H1("11. Tests automatisés"))
story.append(P("84 tests pytest couvrant le cœur, les trois niveaux et les exigences de la "
              "spécification. Répartition :"))
story.append(make_table(["Fichier", "Contenu"],
    [["test_core.py", "Chargement, normalisation, classement, fragments"],
     ["test_level1.py", "Comparaison textuelle"],
     ["test_level2.py", "Tokens, winnowing, GST, fonctions"],
     ["test_level3.py", "Structure inter-langages, motifs"],
     ["test_gui.py", "Interface graphique (Tkinter)"]],
    widths=[4*cm, 12*cm]))
story.append(Paragraph("python -m pytest tests -q", code_style))
story.append(P("Résultat : 84 passed.", small_style))

# ========== 12. ÉVALUATION ==========
story.append(H1("12. Évaluation des performances"))
story.append(Paragraph("python -m evaluation.run_evaluation                    # rapport texte\n"
                      "python -m evaluation.run_evaluation --csv resultats.csv --plots", code_style))
story.append(P("Produit des métriques de classification (précision, rappel, F1) sur des "
              "scénarios étiquetés, avec graphiques matplotlib."))

# ========== 13. EXÉCUTABLES ==========
story.append(H1("13. Exécutables autonomes (Windows)"))
story.append(P("Des exécutables autonomes sont fournis dans dist/ :"))
story.append(bullet([
    "<b>dist\\DetecteurDeSimilarite\\</b> — version graphique ; lancer "
    "DetecteurDeSimilarite.exe (dossier samples/ joint pour démonstration).",
    "<b>dist\\CLI-Similarite\\</b> — version console ; même usage que cli.py.",
]))
story.append(P("Pour reconstruire les exécutables après modification du code :"))
story.append(Paragraph("pip install pyinstaller\n"
                      "py -m PyInstaller detecteur_similarite.spec --noconfirm   # version graphique\n"
                      "py -m PyInstaller cli_similarite.spec --noconfirm         # version console", code_style))
story.append(P("Les spécifications *.spec déclarent les grammaires tree-sitter comme imports "
              "cachés (chargées dynamiquement, sinon absentes du paquet)."))

# ========== 14. EXPORTS ==========
story.append(H1("14. Exports CSV et HTML"))
story.append(P("L'interface graphique et la CLI permettent d'exporter les résultats :"))
story.append(bullet([
    "<b>CSV</b> : tableau des candidats classés (rang, fichier, langage, score, alerte, "
    "fragments, temps).",
    "<b>HTML</b> : rapport complet avec tableau, détail des sous-scores, notes et "
    "visualisation.",
]))

# ========== 15. ÉTHIQUE ==========
story.append(H1("15. Avertissement éthique"))
story.append(P("Un score de similarité ne constitue pas, à lui seul, une preuve de plagiat. "
              "Il signale des ressemblances statistiques et structurelles devant impérativement "
              "faire l'objet d'un examen critique par un humain qualifié."))

# ========== 16. AUTEUR ==========
story.append(H1("16. Auteur"))
story.append(P("Projet réalisé dans le cadre d'un cours de programmation avancée — "
              "utilisation pédagogique."))

doc.build(story)
print("PDF généré :", OUT)
