# Décisions de conception — session de cadrage du 2026-07-07

Ce document consigne les décisions prises lors d'une session de "grilling"
(interrogatoire systématique) menée avec l'utilisateur avant de construire le
pipeline d'automatisation et de faire évoluer le site. Il vient compléter
`PROJECT_GOAL.md` (objectif et exigences) et `CONTEXT.md` (état des lieux) :
**PROJECT_GOAL.md** dit ce qu'on veut, **CONTEXT.md** dit d'où on part, ce
document-ci dit **ce qui a été tranché** avant de commencer à coder.

À la fin de cette session, aucune implémentation n'a encore été faite : ni
`git init`, ni scraper, ni site v2. Ce qui suit sert de spécification pour ce
travail à venir.

## Faits vérifiés directement pendant la session (pas des décisions)

Trois des cinq risques listés dans `PROJECT_GOAL.md` ont été validés par des
requêtes HTTP brutes (curl, sans rendu JS) pendant cette session :
- Un client HTTP simple obtient le HTML complet de la page de listing et
  d'une fiche détail (`ehden-persephone`), sans rendu JS nécessaire.
- La page de listing expose directement, dans le HTML brut, les liens
  `href` vers les fiches détail (10 par page) et les paramètres de
  pagination (`page=1` à `page=4`).
- `robots.txt` de health-data-hub.fr n'a aucune règle `Disallow` couvrant
  `/bibliotheque-ouverte-algorithmes-sante` — rien ne s'oppose à une
  collecte hebdomadaire, faible volume, avec user-agent identifié.

Découverte supplémentaire, importante pour la conception du schéma : **tous
les champs de taxonomie (Objectif, Domaine médical, Langage, Données
d'application, Validation, Maintenance) sont déjà des vocabulaires fermés et
officiels**, visibles tels quels dans la barre de filtres de la page de
listing (ex. "Objectif de l'algorithme" n'a que 7 valeurs possibles). Ce ne
sont pas des textes libres à catégoriser — le scraper n'a donc besoin
d'aucune classification ou résumé automatique pour ces champs, juste d'un
parsing déterministe des sections des fiches détail.

Restent non vérifiés (pas retestés cette session) : la stabilité du slug
dans le temps face à un changement de titre côté source, et l'identifiant
unique — traités ci-dessous comme des décisions de conception plutôt que
des faits à observer, puisqu'ils ne peuvent être observés qu'après coup.

## Décisions prises

### Infrastructure
- **Dépôt** : ce répertoire deviendra un dépôt git avec un remote GitHub
  **public** (Pages gratuit, données déjà publiques, permet l'audit externe).
  Le moment de la création (`git init` + remote) est volontairement laissé
  à l'étape d'exécution, pas encore fait.
- **Déploiement du site** : GitHub Pages configuré en "deploy from branch"
  sur `main`, dossier `/site` — pas de workflow Actions dédié au déploiement,
  cohérent avec le choix de ne jamais introduire de build step côté front.
- **Langage du scraper** : Python (`requests`/`httpx` + parsing HTML), déjà
  le candidat par défaut cité dans `PROJECT_GOAL.md`.

### Schéma canonique des données
- Le schéma canonique est une union simplifiée des deux sources actuelles :
  champs de taxonomie structurés (déjà des vocabulaires fermés officiels,
  cf. ci-dessus) + `code_disponible_sur` (URL du dépôt) + slug + URL de la
  fiche officielle.
- **Champs de provenance/confiance abandonnés** (`statut_extraction`,
  `source`) : ils n'ont de sens que pour une extraction manuelle mixte ;
  une fois le scraper live, chaque ligne est reconfirmée chaque semaine
  depuis la fiche officielle. Remplacés par un simple horodatage
  `last_checked`.
- **Pas de champ de résumé/description libre** dans le schéma final : le
  champ `resume_technique_paraphrase` du CSV ne peut pas être maintenu à la
  main chaque semaine pour les nouveaux projets sans casser l'automatisation
  complète. À la place : lien direct vers la fiche officielle.
- **Identifiant** : le slug reste la clé primaire. Si un slug disparaît et
  qu'un nouveau slug apparaît pointant vers le même `code_disponible_sur`
  dans le même run, c'est traité comme un renommage/mise à jour (un seul
  champ modifié : le slug), pas comme une suppression + un ajout.
- **Doublons connus** (ex. "Top Diabète" / "Cartographie G12", même dépôt) :
  le catalogue reste fidèle au site officiel (une entrée par fiche, pas de
  fusion éditoriale), mais un champ `related_to` est calculé automatiquement
  chaque run par correspondance exacte sur `code_disponible_sur`, pour que
  le site puisse les regrouper visuellement.

### Comportement du pipeline
- **Commit direct sur `main`** à chaque changement réel détecté (pas de PR
  intermédiaire à valider à la main chaque semaine).
- **Seuils d'abandon** (pas de commit, job en échec) : toute baisse du
  nombre total de fiches (même d'une seule unité), OU un champ obligatoire
  (titre, slug, URL du dépôt) vide/imparsable sur plus de 10% des lignes.
- **Gestion des échecs répétés** : le bot réutilise une unique issue GitHub
  ouverte (label dédié, ex. `scraper-failure`) au lieu d'en ouvrir une
  nouvelle à chaque run en échec ; il la ferme (ou la laisse se refermer)
  au prochain run réussi.
- **Changelog** : un fichier `changelog.json` séparé, alimenté à chaque run
  réussi (entrées structurées : date, ajouts/suppressions/champs modifiés),
  pour permettre une future vue "historique des changements" sans dépendre
  de l'historique git ou de l'API GitHub côté site statique.
- **Planification** : cron hebdomadaire, lundi tôt le matin UTC.
- **Fixtures de test** : des pages HTML réelles (listing + quelques fiches
  détail) sont committées dans le dépôt (ex. `tests/fixtures/`) pour
  permettre de développer/tester le parser hors ligne. Les pages déjà
  récupérées pendant cette session de cadrage (listing + fiche
  ehden-persephone) peuvent servir de point de départ.

### Bootstrap et migration
- **Premier run du pipeline = scrape complet en direct** des ~48 fiches, qui
  devient le `data.json` initial. Le `DATA` array de `site/index.html` et
  les CSV existants ne sont **pas** utilisés comme source pour ce bootstrap
  — ils sont supplantés, pas réconciliés à la main.
- **CSV existants** (`data/boas_extraction_brute.csv`,
  `data/boas_fetch_log.csv`) : supprimés une fois `data.json` vérifié
  équivalent/suffisant. L'historique reste accessible via git.

### Périmètre du site v1
- v1 = le prototype actuel (facettes, recherche, cartes) **inchangé
  fonctionnellement**, seule différence : chargement de `data.json` au
  runtime au lieu du tableau `DATA` codé en dur.
- Explicitement reportés à v2+ : options de tri, export (CSV/JSON), page de
  changelog dans l'UI (même si les données du changelog existent dès le
  départ, cf. ci-dessus).

## Ce qui reste ouvert après cette session

- Le `git init` / la création du dépôt GitHub lui-même (décidé : timing
  différé, pas encore fait).
- Le détail d'implémentation du scraper (structure de code, gestion des
  erreurs réseau, retries, etc.) — non couvert par cette session, à traiter
  à l'étape de build.
- La table de correspondance "libellé officiel → libellé reformulé" pour
  chaque champ de taxonomie (ex. "Outils de manipulation / transformation
  de la base principale du SNDS" → "Transformation de données") existe déjà
  implicitement dans `site/index.html` mais n'a pas été formalisée comme
  fichier de configuration séparé.
