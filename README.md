# Module de Gestion des Membres et Organisations Église

## Fonctionnalités Clés

### 🏛️ Gestion des Organisations
- **Types d'organisations** : 
  - Église (avec pasteur principal et adjoints)
  - Tribu 
  - Cellule de prière
  - Groupe (avec critères d'âge/sexe/situation matrimoniale)
  - Académie
- **Hiérarchie** : Églises mères/filles avec gestion des responsables

### 👥 Gestion des Membres
- **Fiche membre complète** :
  - Informations démographiques (âge, sexe, situation familiale)
  - Rôles ecclésiastiques (pasteur, ancien, diacre, missionnaire)
  - Statuts spéciaux (nouveau membre, anniversaire)
- **Assignation automatique** aux groupes selon critères

## Installation

1. Placer le module dans le dossier `addons`
2. Mettre à jour la liste des apps dans Odoo
3. Installer le module "Gestion des Membres et Organisations Église"

## Configuration

🔧 **Paramètres à configurer** :
- Durée du statut "Nouveau membre" (jours)
- Taille des équipes auto-générées

## Utilisation

### Pour les Églises
1. Créer une fiche église (cocher "Est une église")
2. Assigner un pasteur principal
3. Ajouter des pasteurs adjoints
4. Créer des églises filles si nécessaire

### Pour les Membres
1. Compléter les informations personnelles
2. Assigner des rôles ecclésiastiques
3. La système assignera automatiquement :
   - Groupes par âge/sexe
   - Statut "Nouveau membre"
   - Détection femme de pasteur

## Fonctionnalités Techniques

🛠️ **Automatisations** :
- Calcul de l'âge
- Détection anniversaires (avec notifications)
- Assignation groupes
- Gestion hiérarchique

✅ **Validations** :
- Cohérence conjoints
- Critères groupes
- Rôles ecclésiastiques

## Support

Pour toute question, contacter [votre contact support] ou ouvrir un ticket sur [plateforme de support].

---

*Version 1.0 - © 2023 Votre Société*