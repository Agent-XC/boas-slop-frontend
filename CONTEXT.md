# Contexte du projet — Catalogue BOAS non-officiel

Ce document résume ce qui a été fait avant la prise en main par Claude Code, pour
éviter de refaire le travail d'exploration et pour signaler clairement ce qui est
solide vs. ce qui reste à vérifier.

## Origine

La Bibliothèque Ouverte d'Algorithmes en Santé (BOAS) est un catalogue publié par
le Health Data Hub (HDH) à cette adresse :

https://www.health-data-hub.fr/bibliotheque-ouverte-algorithmes-sante

Le catalogue liste ~48 projets (algorithmes, requêtes-types, frameworks, data
challenges) avec des filtres par domaine médical, type d'outil, langage, données
utilisées, validation, maintenance, type d'auteur. Le point de départ de ce projet
était : la page officielle est jugée confuse (facettes mal nommées, pas de vue
d'ensemble, catégories qui se chevauchent), d'où l'idée de construire un catalogue
alternatif, mieux structuré.

## Ce qui a été construit jusqu'ici

### 1. Un prototype de site statique (`site/index.html`)
Un fichier HTML/CSS/JS autonome (sans backend, sans build), avec :
- un jeu de données des 48 projets **codé en dur dans une balise `<script>`**
  (tableau JS), reconstruit à partir du site officiel ;
- des filtres à facettes recombinables avec comptage en direct ;
- une facette ajoutée qui n'existe pas sur le site officiel : le "type de fiche"
  (Data challenge / Requête-type / Algorithme), déduit du titre ;
- des libellés de filtres reformulés en français plus clair.

**Important** : ce jeu de données a été initialement halluciné (produit de mémoire
générale sur ce type de catalogue) avant d'être confirmé, page par page, par des
extractions réelles plus tard dans le projet. Le contenu affiché dans ce prototype
a fini par correspondre fidèlement à la liste officielle (48 entrées, confirmées via
fetch direct des pages 0 à 4 du listing), mais **les champs détaillés par projet
dans ce fichier n'ont pas tous été re-vérifiés un par un contre les fiches
individuelles** — voir section "Limites connues" plus bas.

### 2. Deux fichiers CSV d'extraction (`data/`)

**`boas_extraction_brute.csv`** — table brute, une ligne par projet, avec :
- `titre_technique`, `chemin_gitlab` (si applicable), `code_disponible_sur` (URL
  du dépôt de code réel — GitHub, GitLab, ou instance GitLab institutionnelle
  propre), `organisme_porteur_gitlab`, `resume_technique_paraphrase` (résumé en
  langage naturel, jamais une citation verbatim), `statut_extraction` (niveau de
  confiance), `source` (méthode d'extraction), `url_fiche_boas_source` (URL exacte
  de la fiche officielle utilisée comme source, quand disponible).
- Ce fichier mélange plusieurs méthodes d'extraction utilisées à différents
  moments (voir `boas_fetch_log.csv`) : certaines lignes viennent d'un miroir
  GitHub tiers (ecosyste.ms / data.code.gouv.fr) qui référence les dépôts
  `gitlab.com/healthdatahub/*`, d'autres viennent d'une lecture complète et
  directe de la fiche officielle HDH (le cas le plus fiable), d'autres enfin
  restent non confirmées.
- Le champ `statut_extraction` distingue explicitement :
  - `CONFIRMÉ (page détail HDH complète)` — la fiche officielle a été lue
    intégralement, en direct.
  - `Confirmé (GitLab)` — confirmé via le miroir GitLab tiers uniquement, pas
    via la fiche HDH elle-même.
  - `PARTIELLEMENT CONFIRMÉ` — existence et porteur du projet confirmés par une
    source secondaire (article HDH, annonce communauté), mais fiche officielle
    et/ou dépôt de code non localisés à ce stade.
  - `NON CONFIRMÉ` — quasiment aucune ligne ne devrait plus être dans cet état,
    mais vérifier avant de considérer le fichier comme définitif.

**`boas_fetch_log.csv`** — journal des pages effectivement consultées, avec pour
chacune : la session approximative, l'URL exacte de la fiche BOAS, la méthode
d'accès (fetch direct / recherche puis fetch), et si l'URL a été fournie
directement par l'utilisateur ou découverte autrement.

## Découvertes importantes sur la structure du catalogue source

- **Le code n'est pas systématiquement sur GitLab.** Quatre hébergements
  distincts ont été identifiés :
  1. `gitlab.com/healthdatahub/...` — dépôts internes HDH
  2. `github.com/<org>` — contributeurs externes (AP-HP, Epiconcept, SNDStoolers…)
  3. Une instance GitLab institutionnelle propre à un contributeur, hors
     gitlab.com (ex. `git.drees.fr` pour la DREES)
  4. Pour les data challenges : GitHub, mais sous l'org du **prestataire de la
     plateforme de challenge** (`drivendataorg`, `Trustii-team`), pas sous un
     compte HDH — le code n'apparaît qu'après la fin du challenge.
- **L'icône/libellé "Gitlab" affiché sur chaque fiche officielle n'est pas fiable**
  — il est affiché même quand le lien pointe en réalité vers GitHub. Seul le
  `href` réel du bouton "Lien vers le repo" fait foi.
- **Chaque fiche projet suit une structure Markdown/HTML cohérente** avec des
  sections répétées : Objectifs, Auteur(s), Domaine médical, Langage de
  programmation, Données d'application, Validation, Maintenance, Licence et
  conditions d'utilisation, Lien vers le repo. C'est une bonne nouvelle pour un
  futur scraper : le parsing peut se faire sur ces titres de section plutôt que
  sur des sélecteurs CSS fragiles.
- **Incohérences repérées entre sources HDH elles-mêmes** (pas des erreurs
  d'extraction) :
  - MORS est attribué à "GCS HUGO" dans un article d'annonce HDH, mais la fiche
    officielle du projet l'attribue nommément au CHU de Rennes, avec un dépôt
    hébergé hors de l'organisation GitLab HDH.
  - "Top Diabète" et "Cartographie des pathologies G12" pointent vers le **même**
    dépôt GitLab (`boas/cnam/cartographie-des-pathologies`) — ce sont
    vraisemblablement deux fiches pour un seul et même outil / sous-composants
    d'un même outil, à trancher lors du nettoyage.
  - Le chemin GitLab réel d'EHDEN/Persephone est
    `applications-du-hdh/snds_omop`, différent de ce qu'un rapprochement
    approximatif via le miroir GitHub tiers avait suggéré au départ
    (`boas/hdh/snds_omop`).

## Limites connues du jeu de données actuel

1. **Couverture inégale des 48 projets.** Un sous-ensemble a été lu intégralement
   en direct depuis la fiche officielle (le plus fiable). Un autre sous-ensemble
   vient du miroir GitLab tiers (fiable pour le lien de code et une description
   courte, mais pas pour les champs de taxonomie du site officiel — domaine,
   validation, maintenance, etc., qui n'y figurent pas). Quelques lignes restent
   marquées non confirmées.
2. **Le prototype `site/index.html` contient un jeu de données de taxonomie
   complet (48 lignes, tous les champs de filtre) qui n'est PAS le même fichier
   que les deux CSV fournis ici.** Il faudra fusionner/réconcilier ces deux
   sources en un schéma canonique unique avant de construire quoi que ce soit
   d'automatisé dessus — ne pas traiter l'un ou l'autre comme la vérité seule.
3. **Aucun identifiant unique garanti stable** n'a été formellement défini — le
   `slug` de l'URL est le meilleur candidat mais sa stabilité dans le temps n'est
   pas vérifiée (un changement de titre sur le CMS source peut le régénérer).
4. **La découverte automatique des URLs de fiches n'a jamais été testée avec un
   vrai client HTTP** (voir PROJECT_GOAL.md, section "Risques identifiés").
   Toutes les fiches individuelles utilisées dans cette session ont été
   atteintes soit parce que l'utilisateur a copié-collé l'URL exacte, soit via
   une recherche web ciblée — jamais via une extraction automatique des liens
   de la page de listing.
5. **Aucune vérification de robots.txt / conditions d'utilisation** n'a été
   faite à ce stade.

## Recommandation pour la suite

Ne pas considérer `boas_extraction_brute.csv` comme la base de données finale à
mettre à jour en continu. Le traiter comme :
- une spécification de schéma (quels champs existent, quelles valeurs sont
  possibles) ;
- une base de comparaison / test de non-régression une fois qu'un scraper
  systématique aura été écrit et validé sur l'ensemble des fiches actuelles.
