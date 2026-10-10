"""Checks for the static site, mirroring docs/SITE_SPEC.md."""
import re
from pathlib import Path

SITE = Path(__file__).resolve().parents[1] / "site"
HTML = (SITE / "index.html").read_text()

SECTIONS = ["summary", "problem", "method", "decisions", "figures", "protocol",
            "results", "demo", "reproduce", "limitations", "references"]


def test_files_exist():
    assert (SITE / "index.html").exists() and (SITE / "logo.svg").exists()


def test_all_spec_sections_present_and_in_order():
    positions = [HTML.find(f'<section id="{s}"') for s in SECTIONS]
    assert all(p > 0 for p in positions), dict(zip(SECTIONS, positions))
    assert positions == sorted(positions)


def test_figures_are_numbered_and_captioned():
    for n in (1, 2, 3, 4, 5):
        assert f"<b>Fig. {n}.</b>" in HTML


def test_interactive_figures_are_labelled():
    assert HTML.count('<span class="tag">Simulated data</span>') == 3
    assert HTML.count('<span class="tag">Illustrative inputs</span>') == 1


def test_results_rendering_shows_profile_and_subgroups():
    # the page must surface the run profile and subgroup tables when results.json provides them
    assert "Run profile:" in HTML and "Performance by sex" in HTML and "Small sample" in HTML
    assert "Where the gate misses" in HTML and "External validation: NIH ChestX-ray14" in HTML
    assert "external_caveats" in HTML  # caveats are always rendered with external results


def test_results_table_has_no_hardcoded_values():
    table = HTML[HTML.index('id="results-table"'):HTML.index('id="results-figs"')]
    values = re.findall(r'<td class="v">(.*?)</td>', table)
    assert values and all("Pending" in v for v in values)


def test_controls_have_labels():
    for control in re.findall(r"<input[^>]*>", HTML):
        cid = re.search(r'id="([^"]+)"', control).group(1)
        before = HTML[max(0, HTML.index(control) - 200):HTML.index(control)]
        wrapped = before.rfind("<label") > before.rfind("</label>")
        assert f'for="{cid}"' in HTML or "aria-label" in control or wrapped, cid


def test_local_references_resolve():
    local = [u for u in re.findall(r'(?:src|href)="([^"#:]+)"', HTML) if not u.startswith("//") and "${" not in u]
    assert all((SITE / u).exists() for u in local), local


def test_no_template_chrome():
    assert "text-transform: uppercase" not in HTML
    assert not re.search(r'>[^<]*→\s*</(a|button)>', HTML)
