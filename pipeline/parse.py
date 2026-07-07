"""Parses a single BOAS detail-page HTML document into a canonical-schema record.

Parses by locating section headings and known label text (e.g. "Lien vers
le repo :"), not CSS selectors or class names alone, per CLAUDE.md's known
quirks note — official page markup is otherwise unstable to key off of.

Not a public seam: tested only indirectly through run_pipeline(), per the
PRD's testing decision (assert on run_pipeline()'s output, not on
intermediate parsing helpers).
"""

import re

from bs4 import BeautifulSoup


def _heading(soup: BeautifulSoup, text: str):
    return soup.find(lambda tag: tag.name in ("h2", "h3") and text in tag.get_text())


def _taxonomy_values(soup: BeautifulSoup, heading_text: str) -> list[str]:
    heading = _heading(soup, heading_text)
    if heading is None:
        return []
    block = heading.find_next_sibling()
    if block is None:
        return []
    return [span.get_text(strip=True) for span in block.select(".taxonomie__value span")]


def _taxonomy_value(soup: BeautifulSoup, heading_text: str) -> str:
    values = _taxonomy_values(soup, heading_text)
    return values[0] if values else ""


def _type_auteur(soup: BeautifulSoup) -> str:
    heading = _heading(soup, "Auteur(s)")
    if heading is None:
        return ""
    block = heading.find_next_sibling()
    if block is None:
        return ""
    first_author = block.find("div", class_="author")
    if first_author is None:
        return ""
    type_div = first_author.find("div", class_="type")
    return type_div.get_text(strip=True) if type_div else ""


def _code_disponible_sur(soup: BeautifulSoup) -> str:
    label = soup.find(string=re.compile("Lien vers le repo", re.I))
    if label is None:
        return ""
    link = label.parent.find("a", href=True)
    return link["href"] if link else ""


def parse_detail_page(html: str, url: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")

    h1 = soup.find("h1")
    titre = h1.get_text(strip=True) if h1 else ""
    slug = url.rstrip("/").rsplit("/", 1)[-1]

    return {
        "slug": slug,
        "titre": titre,
        "type_auteur": _type_auteur(soup),
        "objectif": _taxonomy_values(soup, "Objectifs"),
        "domaine_medical": _taxonomy_values(soup, "Domaine médical"),
        "langage": _taxonomy_values(soup, "Langage de programmation"),
        "donnees_application": _taxonomy_values(soup, "Données d'application"),
        "validation": _taxonomy_value(soup, "Validation"),
        "maintenance": _taxonomy_value(soup, "Maintenance"),
        "code_disponible_sur": _code_disponible_sur(soup),
        "url_fiche_boas_source": url,
    }
