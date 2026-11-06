"""
Génération d'un rapport HTML autonome.

Le rapport contient :
  - L'avertissement éthique permanent ;
  - Un résumé des comparaisons (moyenne, extrêmes, répartition des alertes) ;
  - Un tableau classé et coloré des candidats ;
  - Les fragments surlignés côte à côte (référence ↔ candidat) avec une couleur par fragment.
"""

from __future__ import annotations

import html as html_mod
import os
from typing import Dict, List

from models.config import ALERT_COLORS, ETHICAL_WARNING, FRAGMENT_COLORS
from models.ranking import CandidateRank


def _esc(text: str) -> str:
    """Échappement HTML de base."""
    return html_mod.escape(str(text))


def _fragment_css_and_overlay(lines: List[str], fragments, side: str) -> str:
    """
    Produit le HTML d'un panneau de code avec surlignage des fragments.
    Chaque ligne reçoit un fond coloré selon le fragment qui la couvre.
    """
    # Carte ligne → couleur
    color_map: Dict[int, str] = {}
    for idx, frag in enumerate(fragments):
        color = FRAGMENT_COLORS[idx % len(FRAGMENT_COLORS)]
        start = frag.ref_start if side == "ref" else frag.cand_start
        end = frag.ref_end if side == "ref" else frag.cand_end
        for ln in range(start, end + 1):
            color_map[ln] = color

    parts: List[str] = []
    for line_no, line_text in enumerate(lines, start=1):
        color = color_map.get(line_no, "")
        style = f' style="background-color:{color};"' if color else ""
        parts.append(
            f'<div class="code-line"{style}>'
            f'<span class="line-no">{line_no}</span>'
            f'<span class="line-txt">{_esc(line_text)}</span>'
            f'</div>'
        )
    return "".join(parts)


def export_html(
    results: List[CandidateRank],
    output_path: str,
    reference_path: str,
    reference_lines: List[str],
    reference_filename: str = "",
    reference_language: str = "",
    candidate_sources: Dict[str, List[str]] | None = None,
    candidate_languages: Dict[str, str] | None = None,
) -> str:
    """
    Génère un rapport HTML autonome (aucune dépendance externe hors CSS inline).
    `candidate_sources` associe un chemin de candidat à ses lignes de code.
    """
    abs_path = os.path.abspath(output_path)
    os.makedirs(os.path.dirname(abs_path) or ".", exist_ok=True)

    candidate_sources = candidate_sources or {}
    candidate_languages = candidate_languages or {}

    # --- Résumé ---------------------------------------------------------------
    scores = [r.score for r in results] or [0.0]
    mean_score = sum(scores) / len(scores)
    max_score = max(scores)
    min_score = min(scores)
    count_high = sum(1 for r in results if r.alert == "high")
    count_medium = sum(1 for r in results if r.alert == "medium")
    count_low = sum(1 for r in results if r.alert == "low")

    # --- Construction des sections Candidat -------------------------------------
    detail_sections: List[str] = []
    for r in results:
        cand_lines = candidate_sources.get(r.path, [])
        cand_lang = candidate_languages.get(r.path, r.language)

        # Sous-scores
        subs_rows = "".join(
            f"<tr><td>{_esc(k)}</td><td><div class='bar'><span style='width:{min(100, v)}%;'></span></div></td><td>{v:.1f}%</td></tr>"
            for k, v in r.sub_scores.items()
        ) or "<tr><td colspan='3'>Aucun sous-score disponible.</td></tr>"

        # Notes
        notes_html = ""
        valid_notes = [n for n in r.notes if n]
        if valid_notes:
            notes_html = "<ul class='notes'>" + "".join(
                f"<li>{_esc(n)}</li>" for n in valid_notes
            ) + "</ul>"

        # Fragments
        frags_html = "<p class='no-frag'>Aucun fragment similaire suffisamment long détecté.</p>"
        if r.fragments:
            ref_panel = _fragment_css_and_overlay(reference_lines, r.fragments, "ref")
            cand_panel = _fragment_css_and_overlay(cand_lines, r.fragments, "cand")
            frag_list = "".join(
                f"<li>Réf. L{f.ref_start}–{f.ref_end} ↔ Cand. L{f.cand_start}–{f.cand_end}"
                f"{' — ' + _esc(f.label) if f.label else ''} "
                f"<span class='frag-score'>{f.score:.0%}</span></li>"
                for f in r.fragments
            )
            frags_html = f"""
            <div class='frag-list'><strong>Fragments correspondants :</strong><ul>{frag_list}</ul></div>
            <div class='diff-container'>
              <div class='diff-pane'>
                <div class='diff-title'>Référence — {_esc(reference_filename)} ({_esc(reference_language)})</div>
                <div class='code-block'>{ref_panel}</div>
              </div>
              <div class='diff-pane'>
                <div class='diff-title'>Candidat — {_esc(r.filename)} ({_esc(cand_lang)})</div>
                <div class='code-block'>{cand_panel}</div>
              </div>
            </div>"""

        color = ALERT_COLORS.get(r.alert, "#999")
        detail_sections.append(f"""
        <details class='candidate-details' style='border-left:5px solid {color};'>
          <summary>
            <span class='rank'>#{r.rank}</span>
            <span class='fname'>{_esc(r.filename)}</span>
            <span class='lang'>{_esc(r.language)}</span>
            <span class='score' style='color:{color}'>{r.score:.1f} %</span>
            <span class='alert-pill' style='background:{color}'>{_esc(r.alert_label)}</span>
          </summary>
          <div class='details-body'>
            <table class='subscore-table'><thead><tr><th>Sous-mesure</th><th></th><th>Score</th></tr></thead>
            <tbody>{subs_rows}</tbody></table>
            {notes_html}
            <p class='meta'>Temps de calcul : {r.time_ms:.1f} ms — Fragments : {len(r.fragments)}</p>
            {frags_html}
          </div>
        </details>""")

    # --- Tableau récapitulatif -------------------------------------------------
    table_rows = "".join(
        f"<tr>"
        f"<td>{r.rank}</td>"
        f"<td class='fname'>{_esc(r.filename)}</td>"
        f"<td>{_esc(r.language)}</td>"
        f"<td><div class='scorebar'><span style='width:{r.score}%;background:{ALERT_COLORS.get(r.alert, "#999")};'></span>"
        f"<em>{r.score:.1f} %</em></div></td>"
        f"<td><span class='alert-pill' style='background:{ALERT_COLORS.get(r.alert, "#999")}'>{_esc(r.alert_label)}</span></td>"
        f"<td>{len(r.fragments)}</td>"
        f"<td>{r.time_ms:.1f}</td>"
        f"</tr>"
        for r in results
    ) or "<tr><td colspan='7'>Aucun candidat évalué.</td></tr>"

    # --- Assemblage final ------------------------------------------------------
    doc = f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Rapport de similarité de code — {_esc(reference_filename)}</title>
<style>
  * {{ box-sizing: border-box; }}
  body {{ font-family: 'Segoe UI', system-ui, sans-serif; margin:0; background:#f4f6f8; color:#222; }}
  header {{ background: linear-gradient(135deg, #2c3e50, #3498db); color:#fff; padding:24px 32px; }}
  header h1 {{ margin:0 0 4px; font-size:1.5rem; }}
  header p {{ margin:0; opacity:.9; font-size:.95rem; }}
  .ethical {{ background:#fff3cd; border-left:6px solid #ffc107; padding:14px 20px; margin:20px 32px; font-weight:600; }}
  .summary {{ display:flex; flex-wrap:wrap; gap:14px; margin:20px 32px; }}
  .card {{ background:#fff; border-radius:10px; padding:16px 22px; box-shadow:0 2px 6px rgba(0,0,0,.08); min-width:150px; flex:1; }}
  .card .val {{ font-size:1.7rem; font-weight:700; }}
  .card .lbl {{ font-size:.82rem; color:#666; text-transform:uppercase; letter-spacing:.04em; }}
  section {{ margin:28px 32px; }}
  h2 {{ border-bottom:2px solid #3498db; padding-bottom:6px; }}
  table {{ width:100%; border-collapse:collapse; background:#fff; box-shadow:0 2px 6px rgba(0,0,0,.07); border-radius:8px; overflow:hidden; }}
  th, td {{ padding:10px 14px; text-align:left; border-bottom:1px solid #eee; }}
  th {{ background:#2c3e50; color:#fff; font-size:.85rem; }}
  .scorebar {{ background:#eee; border-radius:6px; height:22px; position:relative; min-width:160px; overflow:hidden; }}
  .scorebar span {{ display:block; height:100%; border-radius:6px 0 0 6px; }}
  .scorebar em {{ position:absolute; left:8px; top:2px; font-style:normal; font-size:.8rem; font-weight:700; }}
  .alert-pill {{ color:#fff; font-size:.75rem; font-weight:700; padding:3px 9px; border-radius:12px; }}
  details.candidate-details {{ background:#fff; margin:12px 0; border-radius:8px; box-shadow:0 1px 4px rgba(0,0,0,.08); overflow:hidden; }}
  details summary {{ cursor:pointer; padding:14px 18px; display:flex; gap:14px; align-items:center; font-size:.95rem; flex-wrap:wrap; }}
  details summary .rank {{ font-weight:800; color:#2c3e50; min-width:32px; }}
  details summary .fname {{ font-weight:600; flex:1; }}
  details summary .lang {{ font-size:.8rem; background:#ecf0f1; padding:2px 8px; border-radius:8px; }}
  details summary .score {{ font-weight:800; font-size:1.1rem; }}
  .details-body {{ padding:0 18px 18px; }}
  .subscore-table {{ width:100%; margin-bottom:12px; box-shadow:none; border:1px solid #eee; }}
  .subscore-table th {{ background:#34495e; }}
  .bar {{ background:#eee; border-radius:4px; height:14px; width:240px; overflow:hidden; }}
  .bar span {{ display:block; height:100%; background:#3498db; }}
  .notes {{ background:#eaf7ff; border-left:4px solid #3498db; padding:8px 14px; font-size:.88rem; }}
  .meta {{ font-size:.83rem; color:#777; }}
  .diff-container {{ display:flex; gap:14px; margin-top:14px; }}
  .diff-pane {{ flex:1; min-width:0; }}
  .diff-title {{ font-weight:700; font-size:.86rem; margin-bottom:6px; color:#2c3e50; }}
  .code-block {{ background:#1e1e2e; border-radius:8px; padding:8px 0; max-height:440px; overflow:auto; font-family:'Cascadia Code', Consolas, monospace; font-size:.8rem; }}
  .code-line {{ display:flex; white-space:pre; padding:0 6px; }}
  .line-no {{ width:44px; min-width:44px; text-align:right; padding-right:10px; color:#666; user-select:none; }}
  .line-txt {{ flex:1; color:#d4d4d4; }}
  .frag-list {{ font-size:.87rem; background:#f9f9f9; padding:10px 14px; border-radius:8px; margin-top:10px; }}
  .frag-list li {{ margin:3px 0; }}
  .frag-score {{ background:#3498db; color:#fff; border-radius:8px; padding:1px 7px; font-size:.78rem; }}
  .no-frag {{ font-size:.88rem; color:#999; font-style:italic; }}
  footer {{ text-align:center; padding:24px; font-size:.82rem; color:#888; margin-top:36px; border-top:1px solid #ddd; }}
  @media (max-width:800px) {{ .diff-container {{ flex-direction:column; }} }}
</style>
</head>
<body>

<header>
  <h1>Rapport de similarité entre codes sources</h1>
  <p>Référence : <strong>{_esc(reference_filename)}</strong> ({_esc(reference_language)}) — {len(results)} candidat(s) évalué(s)</p>
</header>

<div class="ethical">⚠ {_esc(ETHICAL_WARNING)}</div>

<div class="summary">
  <div class="card"><div class="val">{len(results)}</div><div class="lbl">Candidats</div></div>
  <div class="card"><div class="val">{mean_score:.1f} %</div><div class="lbl">Score moyen</div></div>
  <div class="card"><div class="val">{max_score:.1f} %</div><div class="lbl">Score max</div></div>
  <div class="card"><div class="val">{min_score:.1f} %</div><div class="lbl">Score min</div></div>
  <div class="card"><div class="val" style="color:#e74c3c">{count_high}</div><div class="lbl">Alertes élevées</div></div>
  <div class="card"><div class="val" style="color:#e67e22">{count_medium}</div><div class="lbl">Alertes moyennes</div></div>
  <div class="card"><div class="val" style="color:#27ae60">{count_low}</div><div class="lbl">Alertes faibles</div></div>
</div>

<section>
  <h2>Classement des candidats</h2>
  <table>
    <thead><tr>
      <th>Rang</th><th>Fichier</th><th>Langage</th><th>Score</th>
      <th>Alerte</th><th>Fragments</th><th>Temps (ms)</th>
    </tr></thead>
    <tbody>{table_rows}</tbody>
  </table>
</section>

<section>
  <h2>Détail et fragments surlignés</h2>
  {"".join(detail_sections) or "<p>Aucun détail disponible.</p>"}
</section>

<footer>
  Généré par le Détecteur de similarité entre codes sources — {_esc(ETHICAL_WARNING)}
</footer>

</body>
</html>"""

    with open(abs_path, "w", encoding="utf-8") as f:
        f.write(doc)

    return abs_path
