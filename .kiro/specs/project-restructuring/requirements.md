# Requirements Document

## Introduction

Ce document définit les exigences pour la réorganisation structurelle du projet n8n-local-stack, un système d'analyse de sentiment financier automatisé. Le projet actuel fonctionne correctement mais souffre d'une organisation sous-optimale qui complique la maintenance et l'évolution.

## Glossary

- **Project_Root**: Le répertoire racine du projet n8n-local-stack
- **Production_Code**: Code actif utilisé en production dans le dossier prod/
- **Archive_Code**: Code historique et obsolète actuellement mélangé avec le code de production
- **Pipeline**: Séquence automatisée de traitement de données (collection → analyse → génération)
- **Dashboard**: Interface utilisateur pour visualiser les résultats d'analyse
- **Sentiment_Engine**: Moteur d'analyse de sentiment utilisant une architecture dual-brain
- **Migration_System**: Système automatisé pour déplacer et réorganiser les fichiers
- **Validation_Suite**: Ensemble de tests pour vérifier l'intégrité après migration

## Requirements

### Requirement 1: Archive Isolation

**User Story:** En tant que développeur, je veux que le code historique soit isolé du code de production, afin d'éviter toute confusion et de maintenir un environnement de développement propre.

#### Acceptance Criteria

1. WHEN the migration system processes archive files, THE Migration_System SHALL move all files from prod/_archive/ to a top-level archive/ directory
2. WHEN archive files are moved, THE Migration_System SHALL create comprehensive documentation explaining the content archivé
3. WHEN developers browse the project, THE Project_Root SHALL contain a clear separation between active code and historical code
4. WHEN the archive is created, THE Migration_System SHALL preserve the original file structure for historical reference
5. WHERE archive documentation is needed, THE Migration_System SHALL generate README_ARCHIVE.md explaining why files were archived

### Requirement 2: Logical Directory Structure

**User Story:** En tant que développeur, je veux une structure de répertoires logique qui sépare clairement les responsabilités, afin de naviguer facilement dans le code et d'ajouter de nouvelles fonctionnalités.

#### Acceptance Criteria

1. THE Migration_System SHALL create a pipelines/ directory containing all data processing modules
2. WHEN organizing pipelines, THE Migration_System SHALL group collection, analysis, and automation modules separately
3. THE Migration_System SHALL create a dashboards/ directory separating generators from runtime artifacts
4. WHEN organizing services, THE Migration_System SHALL move standalone services to a dedicated services/ directory
5. THE Migration_System SHALL consolidate shared utilities in a utils/ directory with clear module separation
6. THE Migration_System SHALL create a proper tests/ directory with unit, integration, and fixtures subdirectories

### Requirement 3: Import Path Consistency

**User Story:** En tant que développeur, je veux des chemins d'import cohérents et prévisibles, afin de comprendre facilement les dépendances et de maintenir le code efficacement.

#### Acceptance Criteria

1. WHEN the migration system updates imports, THE Migration_System SHALL convert all relative imports to use the new directory structure
2. WHEN processing Python files, THE Migration_System SHALL update import statements to reflect new module locations
3. THE Migration_System SHALL ensure all critical modules can be imported without errors after migration
4. WHEN import paths are updated, THE Migration_System SHALL maintain backward compatibility where possible
5. THE Migration_System SHALL create a centralized path resolution utility for Docker vs local environment handling

### Requirement 4: Data Integrity Preservation

**User Story:** En tant que utilisateur du système, je veux que toutes les fonctionnalités existantes continuent de fonctionner après la réorganisation, afin de maintenir la continuité opérationnelle.

#### Acceptance Criteria

1. WHEN the migration is complete, THE Sentiment_Engine SHALL continue to process all 15 tickers without errors
2. WHEN dashboards are generated, THE Dashboard SHALL display the same data and functionality as before migration
3. THE Migration_System SHALL preserve all configuration files and their current settings
4. WHEN the daily automation runs, THE Pipeline SHALL execute all steps (collection, analysis, generation) successfully
5. THE Migration_System SHALL ensure all data file paths remain accessible to the migrated code

### Requirement 5: Validation and Testing

**User Story:** En tant que développeur, je veux un système de validation complet qui vérifie l'intégrité de la migration, afin d'avoir confiance que la réorganisation n'a pas introduit de régressions.

#### Acceptance Criteria

1. THE Validation_Suite SHALL test that all critical Python modules can be imported successfully
2. WHEN validation runs, THE Validation_Suite SHALL verify that the sentiment engine can process at least one ticker end-to-end
3. THE Validation_Suite SHALL confirm that dashboard generation produces valid HTML output
4. WHEN testing the pipeline, THE Validation_Suite SHALL verify that daily automation can execute without errors
5. THE Validation_Suite SHALL validate that all configuration files are accessible and parseable
6. THE Validation_Suite SHALL check that data file paths resolve correctly in both Docker and local environments

### Requirement 6: Rollback Capability

**User Story:** En tant que développeur, je veux pouvoir annuler la migration en cas de problème, afin de restaurer rapidement l'état fonctionnel précédent.

#### Acceptance Criteria

1. WHEN starting migration, THE Migration_System SHALL create a complete backup of the current state
2. THE Migration_System SHALL provide a rollback command that restores the original file structure
3. WHEN rollback is executed, THE Migration_System SHALL verify that the restored state is functional
4. THE Migration_System SHALL maintain a log of all changes made during migration for troubleshooting
5. WHERE rollback is needed, THE Migration_System SHALL preserve any data files created during the migration period

### Requirement 7: Documentation Generation

**User Story:** En tant que développeur, je veux une documentation à jour qui reflète la nouvelle structure, afin de comprendre rapidement comment utiliser et maintenir le système réorganisé.

#### Acceptance Criteria

1. THE Migration_System SHALL generate updated documentation reflecting the new directory structure
2. WHEN documentation is created, THE Migration_System SHALL include migration guides for existing scripts
3. THE Migration_System SHALL update all existing documentation files to reference new paths
4. THE Migration_System SHALL create architectural diagrams showing the new organization
5. WHERE import changes are made, THE Migration_System SHALL document the old → new mapping for reference

### Requirement 8: Environment Compatibility

**User Story:** En tant que utilisateur, je veux que le système continue de fonctionner dans tous les environnements supportés (Docker et local Windows), afin de maintenir la flexibilité de déploiement.

#### Acceptance Criteria

1. WHEN the migration is complete, THE Migration_System SHALL ensure Docker container execution remains functional
2. THE Migration_System SHALL verify that local Windows development environment continues to work
3. WHEN path resolution is updated, THE Migration_System SHALL maintain compatibility with both /data/ (Docker) and local_files/ (Windows) paths
4. THE Migration_System SHALL preserve all environment-specific configurations and variables
5. THE Migration_System SHALL test that data file access works correctly in both environments