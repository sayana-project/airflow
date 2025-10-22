# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**AIRFLOW ML PIPELINE** - Projet MLOps pour l'orchestration de workflows de Machine Learning avec Apache Airflow.

### Contexte
- **Formation**: Simplon Academy MLOps
- **Objectif**: Orchestration d'un pipeline ML complet avec Airflow
- **Technologies**: Airflow 2.9.3, Docker, Scikit-learn, Flask
- **Dataset**: advertising.csv - Prédiction de clicks sur publicités

### Architecture Principale
```
Airflow (orchestration)
├── DAG Principal: ml_pipeline_advertising
│   ├── Chargement données (advertising.csv)
│   ├── Prétraitement (scaling, train/test split)
│   ├── Entraînement (régression logistique)
│   ├── Évaluation et sauvegarde du modèle
│   ├── Notifications email (succès/échec)
│   └── Trigger API Flask monitoring
└── DAG Secondaire: ml_pipeline_flask_api
    ├── API REST pour monitoring
    ├── Pages succès/échec (Bootstrap)
    └── Endpoints de métriques
```

### Key Components
- **dags/main.py**: DAG principal du pipeline ML
- **dags/src/model_development.py**: Fonctions ML complètes
- **dags/Flask_API.py**: API Flask pour monitoring
- **dags/Flask_DAG.py**: DAG pour l'API Flask
- **advertising.csv**: Dataset principal (1000 échantillons)
- **docker-compose.yaml**: Infrastructure complète Airflow

### Development Workflow
```bash
# Démarrer infrastructure
docker-compose up -d

# Accéder Airflow UI
http://localhost:8080 (airflow/airflow)

# Déclencher DAG manuellement
docker-compose exec airflow-cli airflow dags trigger ml_pipeline_advertising

# Voir logs
docker-compose exec airflow-cli airflow logs ml_pipeline_advertising

# Démarrer API Flask
python dags/Flask_API.py
```

### Common Development Commands
```bash
# Vérifier les DAGs disponibles
docker-compose exec airflow-cli airflow dags list

# Vérifier statut des tâches
docker-compose exec airflow-cli airflow task states ml_pipeline_advertising

# Tester le modèle localement
python -c "from dags.src.model_development import load_data; print(load_data())"

# Redémarrer services spécifiques
docker-compose restart airflow-scheduler
docker-compose restart airflow-worker
```

### Configuration Files
- **.env**: Variables d'environnement (SMTP, AIRFLOW_UID)
- **config/airflow.cfg**: Configuration Airflow (email backend)
- **requirements.txt**: Dépendances Python
- **dags/templates/**: Templates HTML pour API Flask

### Important Notes
- Le DAG s'exécute quotidiennement (`@daily`)
- Les emails sont configurés avec SMTP
- L'API Flask fonctionne sur le port 5000
- Les modèles sont sauvegardés dans `/opt/airflow/model/`
- Le dataset doit être à la racine du projet

### Testing and Validation
1. Vérifier que le DAG apparaît dans l'interface Airflow
2. Tester l'exécution manuelle du DAG
3. Vérifier les logs pour toute erreur
4. Tester l'API Flask après exécution réussie
5. Vérifier l'envoi des emails de notification

### Troubleshooting
- **DAG non visible**: Vérifier la syntaxe du fichier DAG
- **Erreur email**: Configuration SMTP dans .env et config/airflow.cfg
- **Permissions**: docker-compose exec airflow-init chown -R airflow:0 /opt/airflow/
- **Dépendances**: docker-compose exec airflow-webserver pip install -r requirements.txt

### Email Configuration
```env
# Dans .env
AIRFLOW__EMAIL__EMAIL_BACKEND=airflow.utils.email.send_email_smtp
password_smtp=votre_mot_de_passe_smtp

# Dans config/airflow.cfg
AIRFLOW__SMTP__SMTP_PASSWORD=password_smtp
```

### API Endpoints
- `GET /`: Redirection succès/échec
- `GET /success`: Page de succès avec détails
- `GET /failure`: Page d'échec avec erreurs
- `GET /api/status`: Statut JSON du DAG
- `GET /api/metrics`: Métriques du modèle
- `GET /health`: Health check

### Output Files
- **Modèle**: `/opt/airflow/model/logistic_regression_model.pkl`
- **Résumé**: `/opt/airflow/model/model_summary.txt`
- **Données**: `/opt/airflow/working_data/preprocessed.pkl`

This project demonstrates complete MLOps pipeline orchestration using Apache Airflow with production-ready features including monitoring, notifications, and error handling.