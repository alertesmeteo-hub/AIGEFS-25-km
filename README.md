# AIGEFS 25 km — Alertes Météo

Module WordPress `[aigefs_meteo]`, indépendant de PEARP et de GEFS.

Source opérationnelle NOAA/NCEP, 31 membres 000–030, grille 0,25°,
65 échéances H+0 à H+384 par pas de 6 h. Aucun secret NOAA nécessaire.
« 25 km » est un nom de module : 0,25° ne représente pas une distance constante.

Produits : température à 2 m, vent scalaire à 10 m, pression mer,
précipitations des 6 dernières heures et cumul depuis le run en équivalent eau.
Pas de rafales, nébulosité ou neige en cm inventées. Les colonnes absentes restent null.
Le cumul total est reconstruit à partir de toutes les périodes de 6 h pour
chaque membre ; moyenne, médiane, P10 et P90 sont calculés ensuite.
La norme du vent est également calculée avant les statistiques, jamais à
partir du vecteur moyen. Affichage par paliers supérieurs de 5 km/h.

792 cartes SVG France/Europe : 4 statistiques, 5 produits, 20 échéances
(H+0, 6, 12, 18, puis toutes les 24 h), hors pluie 6 h à H+0.
Tableaux : 34 746 communes et 96 départements, format JSON v3 à 33 colonnes,
65 échéances. Moyenne des 31 membres, pas un scénario déterministe.
La géolocalisation est facultative, sur HTTPS et sur clic seulement ; le calcul
de proximité est local. Tableau compact en haut et carte ajustée au cadre.

## Production

Workflow `build-aigefs.yml`, manuel ou programmé 4 fois par jour.
Validation de chaque GRIB : run, membre, 31 membres annoncés, grille, balayage,
unités, niveau, période et absence de valeurs manquantes. Toute erreur bloque
la publication et conserve la précédente. Pas de mélange de runs.
Les 31 fichiers H+384 sont vérifiés avant de sélectionner un cycle.
Trois téléchargements concurrents au maximum, avec cadence globale limitée à
40 requêtes/minute (y compris les contrôles de disponibilité). Réponses non GRIB
rejetées et reprises après 60 puis 120 secondes ; pas de téléchargement des niveaux
isobares inutilisés. Les fichiers complets restent temporaires en mémoire.

Tests : `python -m unittest discover -s tests` et `node tests/test_module.cjs`.
Installation : importer le ZIP WordPress, activer, placer `[aigefs_meteo]`.

## Sources vérifiées le 28 septembre 2026

- https://www.emc.ncep.noaa.gov/users/verification/global/aigefs/prod/main.php
- https://www.nco.ncep.noaa.gov/pmb/products/aigefs/
- https://nomads.ncep.noaa.gov/pub/data/nccf/com/aigefs/prod/
- https://www.weather.gov/media/notification/pdf_2025/scn25-89_AIGFS_AIGEFS_and_HGEFS.pdf

Le bucket expérimental GraphCast/EAGLE n'est pas utilisé pour remplacer AIGEFS.
Contours Natural Earth (domaine public). Catalogue communal repris du catalogue
national des modules Alertes Météo. Code de l'extension : GPL-2.0-or-later.
