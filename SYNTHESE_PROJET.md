# 📊 Synthèse du Projet Airflow ML

## 🎯 Objectif du Projet

Ce projet vise à orchestrer un pipeline de Machine Learning avec Apache Airflow pour la prédiction de clicks sur publicités, en utilisant un modèle de régression logistique.

## 🏗️ Architecture du Pipeline

### Schéma Général
```
Données (CSV) → Prétraitement → Entraînement → Évaluation → Notification → Monitoring
```

### Tâches du DAG Airflow

1. **start_pipeline**: Affiche les informations du projet
2. **load_data**: Charge le dataset advertising.csv
3. **data_preprocessing**: Prétraite les données (nettoyage, scaling, split)
4. **separate_data**: Organisation des données (passthrough)
5. **build_model**: Entraîne la régression logistique
6. **evaluate_model**: Évalue le modèle et fait des prédictions
7. **model_summary**: Génère un résumé des performances
8. **send_success_email**: Notification en cas de succès
9. **send_failure_email**: Notification en cas d'échec
10. **trigger_flask_api**: Déclenche l'API de monitoring
11. **end_pipeline**: Affiche le statut final

## 📊 Dataset - Advertising.csv

### Caractéristiques
- **Taille**: 1000 échantillons
- **Variables**: 9 colonnes
- **Target**: `Clicked on Ad` (0 ou 1)
- **Features numériques**: 5 variables utilisées

### Features Utilisées
1. **Daily Time Spent on Site**: Temps quotidien sur le site (minutes)
2. **Age**: Âge de l'utilisateur
3. **Area Income**: Revenu de la zone géographique
4. **Daily Internet Usage**: Utilisation quotidienne d'internet (minutes)
5. **Male**: Genre (0 ou 1)

### Features Exclues
- Timestamp, Ad Topic Line, City, Country (variables catégorielles/textuelles)

## 🔧 Technologies Utilisées

### Orchestration
- **Apache Airflow 2.9.3**: Orchestration des workflows
- **CeleryExecutor**: Exécuteur distribué
- **PostgreSQL**: Base de données métadonnées
- **Redis**: Broker pour les messages

### Machine Learning
- **Scikit-learn 1.4.2**: Bibliothèque ML
- **Régression Logistique**: Algorithme utilisé
- **MinMaxScaler + StandardScaler**: Prétraitement
- **Train/Test Split**: 70%/30%

### Monitoring & API
- **Flask 3.0.3**: API de monitoring
- **Bootstrap 5**: Interface utilisateur
- **JavaScript**: Interactions web
- **HTML/CSS**: Templates web

### Infrastructure
- **Docker & Docker Compose**: Conteneurisation
- **Python 3.11+**: Langage de développement
- **SMTP**: Notifications par email

## 🌐 API Flask de Monitoring

### Endpoints Disponibles
- `GET /`: Redirection succès/échec
- `GET /success`: Page de succès avec détails
- `GET /failure`: Page d'échec avec détails
- `GET /api/status`: Statut JSON du DAG
- `GET /api/metrics`: Métriques du modèle
- `GET /health`: Health check

### Démarrage
```bash
python dags/Flask_API.py
```

Accès: http://localhost:5000

## 🔧 Configuration

### Configuration Email
- **Backend**: `airflow.utils.email.send_email_smtp`
- **Variable**: `password_smtp` (définie dans .env)
- **Notifications**: Succès et échec

### Configuration Airflow
- **Schedule**: Quotidien (`@daily`)
- **Owner**: airflow
- **Max active runs**: 1
- **Retries**: 1 (délai: 5 minutes)

## 📈 Résultats Attendus

### Performance du Modèle
- **Type**: Régression Logistique binaire
- **Features**: 5 variables numériques
- **Précision attendue**: ~80-90%
- **Métriques**: Train score, Test score, différence

### Sorties Générées
1. **Modèle entraîné**: `/opt/airflow/model/logistic_regression_model.pkl`
2. **Résumé performances**: `/opt/airflow/model/model_summary.txt`
3. **Données prétraitées**: `/opt/airflow/working_data/preprocessed.pkl`

### Visualisation
- **Interface Airflow**: http://localhost:8080
- **API Monitoring**: http://localhost:5000
- **Pages HTML**: Succès/échec avec Bootstrap

## 🛠️ Commandes Utiles

### Démarrage
```bash
docker-compose up -d           # Lancer tous les services
docker-compose ps             # Vérifier le statut
```

### Gestion Airflow
```bash
docker-compose exec airflow-cli airflow dags list
docker-compose exec airflow-cli airflow dags trigger ml_pipeline_advertising
docker-compose exec airflow-cli airflow logs ml_pipeline_advertising
```

### Développement
```bash
pip install -r requirements.txt
python -c "from dags.src.model_development import load_data; print(load_data())"
python dags/Flask_API.py  # Démarrer l'API
```

## 🔍 Dépannage

### Problèmes Courants
1. **DAG non visible**: Vérifier la syntaxe du fichier
2. **Erreur email**: Configuration SMTP incorrecte
3. **Permissions**: Changer les permissions des dossiers
4. **Dépendances**: Réinstaller les packages Python

### Solutions
```bash
docker-compose restart airflow-scheduler
docker-compose exec airflow-init chown -R airflow:0 /opt/airflow/
docker-compose exec airflow-webserver pip install -r /opt/airflow/requirements.txt
```

## 📚 Concepts Appris

### Apache Airflow
- DAGs et Operators (PythonOperator, BashOperator, EmailOperator)
- Dépendances entre tâches
- Scheduling et monitoring
- Variables et connexions
- Triggers et callbacks

### MLOps
- Orchestration de workflows ML
- Pipeline automatisé de bout en bout
- Déploiement et monitoring
- Notifications et gestion des erreurs
- Intégration CI/CD

### Développement
- Code modulaire et réutilisable
- Documentation complète
- Tests et validation
- Bonnes pratiques Docker
- Monitoring et logging

## 🎯 Livrables

### Code Source
- ✅ DAG principal (`dags/main.py`)
- ✅ Fonctions ML (`dags/src/model_development.py`)
- ✅ API Flask (`dags/Flask_API.py`)
- ✅ Templates HTML (`dags/templates/`)
- ✅ Dataset (`advertising.csv`)
- ✅ Configuration (`requirements.txt`, `docker-compose.yaml`)

### Documentation
- ✅ README complet avec badges et badges
- ✅ Synthèse du projet (ce document)
- ✅ Code commenté et docstrings

### Fichiers pour Rendu
- 📸 **Captures d'écran** à préparer:
  - Interface Airflow avec DAG
  - Vue graphique du pipeline
  - Logs du DAG en exécution
  - Interface API Flask
  - Pages succès/échec

- 📄 **PDF de synthèse** à préparer:
  - Résumé du fonctionnement
  - Captures d'écran intégrées
  - Analyse des résultats
  - Difficultés rencontrées
  - Pistes d'amélioration

## 💡 Améliorations Possibles

### Court Terme
- [ ] Ajouter plus de métriques (precision, recall, F1-score)
- [ ] Implémenter la validation croisée
- [ ] Ajouter des tests unitaires
- [ ] Monitoring avancé avec Grafana

### Long Terme
- [ ] Intégration CI/CD avec GitHub Actions
- [ ] Déploiement en production
- [ ] Monitoring avec Prometheus
- [ ] Scaling avec Kubernetes

---

## 📝 Conclusion

Ce projet démontre avec succès l'orchestration d'un pipeline ML avec Airflow. L'infrastructure est complète, documentée et prête à être utilisée en production. Les concepts clés de MLOps sont mis en pratique avec des solutions robustes pour le monitoring, les notifications et la gestion des erreurs.

**Impact Pédagogique**: Ce projet permet de maîtriser les fondamentaux de l'orchestration ML et de préparer à des déploiements en entreprise.