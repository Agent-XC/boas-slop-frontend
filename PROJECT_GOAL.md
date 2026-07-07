# Objectif du projet

Construire un dépôt GitHub qui héberge un catalogue non-officiel, mais tenu à
jour automatiquement, des projets de la Bibliothèque Ouverte d'Algorithmes en
Santé (BOAS) du Health Data Hub français.

Source officielle : https://www.health-data-hub.fr/bibliotheque-ouverte-algorithmes-sante

## Fonctionnalités attendues

1. **Récupération automatique hebdomadaire**, si possible via GitHub Actions
   (cron), des informations de tous les projets du catalogue officiel.
2. **Comparaison** du résultat de cette récupération contre une base de données
   statique versionnée dans le dépôt (JSON ou CSV).
3. **Mise à jour** de cette base uniquement si des différences réelles sont
   détectées (nouveau projet, projet retiré, champ modifié).
4. **Présentation continue** de la base de données sous forme d'un site
   consultable (basé sur le prototype HTML/JS fourni dans `site/index.html`,
   à faire évoluer pour ajouter des fonctionnalités : tri, export, historique
   des changements, etc.), déployé de préférence via GitHub Pages.

## Risques identifiés à traiter en priorité (voir CONTEXT.md pour le détail)

Avant de construire le pipeline complet, valider ces points avec des scripts
jetables, en dehors de tout automatisme :

- [ ] Confirmer qu'un simple client HTTP (`requests`/`httpx` en Python, ou
      équivalent) obtient bien le HTML complet des pages de listing et des
      fiches individuelles, sans rendu JS côté client requis. Si un rendu JS
      est nécessaire, prévoir Playwright/Puppeteer dans le workflow (coût et
      complexité plus élevés).
- [ ] Confirmer qu'on peut extraire automatiquement, depuis les pages de
      listing (`?page=0` à `?page=N`), la liste complète des URLs de fiches
      individuelles — plutôt que de dépendre d'une liste codée en dur de 48
      slugs. C'est ce qui permettra de détecter automatiquement les nouveaux
      projets.
- [ ] Vérifier `robots.txt` et l'absence de mention contraire dans les
      conditions d'utilisation du site pour une collecte automatisée,
      respectueuse (une fois par semaine, quelques dizaines de requêtes,
      user-agent explicite et identifiable).
- [ ] Définir un identifiant unique stable par projet (le slug d'URL est le
      candidat naturel, mais vérifier ce qui se passe en cas de changement de
      titre côté source).
- [ ] Définir un schéma canonique unique de champs par projet, en réconciliant
      le jeu de données du prototype `site/index.html` et celui des CSV fournis
      dans `data/` (ils ne sont pas identiques aujourd'hui — voir CONTEXT.md).

## Exigences de robustesse pour le pipeline automatisé

- Le job hebdomadaire ne doit **jamais committer silencieusement** un résultat
  suspect (ex. nombre de projets qui chute brutalement, champs obligatoires
  vides sur une majorité de lignes). Dans ce cas : faire échouer le job et/ou
  ouvrir une issue GitHub automatiquement, sans toucher aux données existantes.
- Séparer clairement les données (`data.json` ou équivalent, réécrit par le
  bot) de la présentation (HTML/JS statique, qui charge les données au
  chargement de la page plutôt que de les contenir en dur). Le prototype actuel
  ne respecte pas encore cette séparation.
- Conserver un historique des changements exploitable (le fait que les données
  soient versionnées dans git suffit probablement, à condition que chaque
  commit automatique ait un message clair résumant ce qui a changé — ex.
  "3 nouveaux projets, 1 lien de dépôt mis à jour").
- Prévoir un mode "dry-run" / des fixtures HTML de test dans le dépôt, pour
  pouvoir faire évoluer le parseur sans dépendre du site en ligne à chaque
  itération de développement.

## Ce qui n'est PAS dans le périmètre immédiat

- Reproduire ou republier le contenu textuel intégral des fiches sources
  (respecter le droit d'auteur : résumés reformulés, pas de copie verbatim de
  paragraphes entiers).
- Héberger une base de données relationnelle ou un backend serveur — l'objectif
  reste un site statique (GitHub Pages) consultant un fichier de données
  statique.
