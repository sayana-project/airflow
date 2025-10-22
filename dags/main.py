# Fichier: main.py - DAG principal pour le pipeline ML avec API Flask intégrée
from __future__ import annotations

import os
import sys
import pendulum
from airflow import DAG
from flask import Flask, jsonify, request
from datetime import datetime

# Ajouter le dossier courant au Python path pour les imports
sys.path.insert(0, os.path.dirname(__file__))
from airflow.providers.standard.operators.bash import BashOperator
from airflow.providers.standard.operators.python import PythonOperator
from airflow.providers.smtp.operators.smtp import EmailOperator
from airflow.providers.standard.operators.trigger_dagrun import TriggerDagRunOperator
from airflow.task.trigger_rule import TriggerRule

# Importer les fonctions du module ML
from model_development import (
    load_data,
    data_preprocessing,
    separate_data_outputs,
    build_model,
    load_model,
    print_model_summary,
)

# Arguments par défaut pour le DAG
default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": pendulum.datetime(2024, 1, 1, tz="UTC"),
    "email_on_failure": True,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": pendulum.duration(minutes=5),
}

# Définition du DAG principal
dag = DAG(
    dag_id="ml_pipeline_advertising",
    default_args=default_args,
    description="Pipeline ML pour la prédiction de clicks sur publicités",
    schedule="@daily",
    catchup=False,
    tags=["machine-learning", "logistic-regression", "mlops"],
    max_active_runs=1,
    doc_md="""
    ## Pipeline ML - Prédiction de clicks sur publicités

    Ce DAG orchestre un pipeline complet de machine learning:
    1. Chargement des données advertising.csv
    2. Prétraitement (nettoyage, scaling, train/test split)
    3. Entraînement d'une régression logistique
    4. Sauvegarde et évaluation du modèle
    5. Notification par email des résultats
    6. Déclenchement de l'API Flask pour le monitoring

    ### Technologies:
    - Airflow 2.9.3
    - Scikit-learn 1.4.2
    - Python 3.11+
    """,
)

# Tâche de démarrage - Affiche les informations du projet
start_task = BashOperator(
    task_id="start_pipeline",
    bash_command="""
    echo "=============================================="
    echo " Démarrage du Pipeline ML - Publicité Click"
    echo " Date: $(date)"
    echo " Objectif: Prédiction de clicks sur publicités"
    echo "=============================================="
    echo ""
    echo " Étapes du pipeline:"
    echo "1. Chargement des données"
    echo "2. Prétraitement"
    echo "3. Entraînement du modèle"
    echo "4. Évaluation et sauvegarde"
    echo "=============================================="
    """,
    dag=dag,
)

# Tâche 1: Chargement des données
load_data_task = PythonOperator(
    task_id="load_data",
    python_callable=load_data,
    dag=dag,
)

# Tâche 2: Prétraitement des données
data_preprocessing_task = PythonOperator(
    task_id="data_preprocessing",
    python_callable=data_preprocessing,
    op_args=[load_data_task.output],
    dag=dag,
)

# Tâche 3: Séparation des données (passthrough pour structure)
separate_data_task = PythonOperator(
    task_id="separate_data",
    python_callable=separate_data_outputs,
    op_args=[data_preprocessing_task.output],
    dag=dag,
)

# Tâche 4: Construction et sauvegarde du modèle
build_model_task = PythonOperator(
    task_id="build_model",
    python_callable=build_model,
    op_args=[separate_data_task.output, "logistic_regression_model.pkl"],
    dag=dag,
)

# Tâche 5: Chargement et évaluation du modèle
evaluate_model_task = PythonOperator(
    task_id="evaluate_model",
    python_callable=load_model,
    op_args=[separate_data_task.output, "logistic_regression_model.pkl"],
    dag=dag,
)

# Tâche 6: Génération du résumé du modèle
summary_task = PythonOperator(
    task_id="model_summary",
    python_callable=print_model_summary,
    op_args=[separate_data_task.output, "logistic_regression_model.pkl"],
    dag=dag,
)

# Tâche 7: Notification par email en cas de succès
success_email = EmailOperator(
    conn_id="smtp",
    task_id="send_success_email",
    to="{{ var.value.tosend | default('pierce.hawthorne59@gmail.com') }}",
    subject=" Succès - Pipeline ML Publicité complété",
    html_content="""
    <h2>Pipeline ML Terminé avec Succès</h2>
    <p>Le pipeline de machine learning pour la prédiction de clicks sur publicités s'est exécuté avec succès.</p>

    <h3>Détails de l'exécution:</h3>
    <ul>
        <li><strong>DAG:</strong> ml_pipeline_advertising</li>
        <li><strong>Model:</strong> Régression Logistique</li>
        <li><strong>Dataset:</strong> advertising.csv</li>
    </ul>

    <h3>Étapes complétées:</h3>
    <ol>
        <li>Chargement des données</li>
        <li>Prétraitement et scaling</li>
        <li>Train/Test split</li>
        <li>Entraînement du modèle</li>
        <li>Évaluation et sauvegarde</li>
    </ol>

    <p><em>Consultez les logs et le modèle sauvegardé pour plus de détails.</em></p>
    """,
    dag=dag,
)

# Tâche 8: Notification par email en cas d'échec
failure_email = EmailOperator(
    task_id="send_failure_email",
    to="{{ var.value.tosend | default('pierce.hawthorne59@gmail.com') }}",
    subject=" Échec - Pipeline ML Publicité",
    html_content="""
    <h2> Échec du Pipeline ML</h2>
    <p>Le pipeline de machine learning a rencontré une erreur lors de l'exécution.</p>

    <h3>Détails de l'échec:</h3>
    <ul>
        <li><strong>Date:</strong> {{ ds }}</li>
        <li><strong>DAG:</strong> {{ dag.dag_id }}</li>
        <li><strong>Run ID:</strong> {{ run_id }}</li>
        <li><strong>Log Path:</strong> {{ ti.log_url }}</li>
    </ul>

    <p><em>Veuillez consulter les logs pour plus de détails sur l'erreur.</em></p>
    """,
    trigger_rule=TriggerRule.ONE_FAILED,
    dag=dag,
)

# Tâche 9: Déclenchement du DAG Flask pour le monitoring
trigger_flask_task = TriggerDagRunOperator(
    task_id="trigger_flask_api",
    trigger_dag_id="ml_pipeline_flask_api",
    conf={
        "message": "Pipeline ML principal terminé",
        "dag_run_id": "{{ run_id }}",
        "execution_date": "{{ execution_date }}",
        "status": "success"
    },
    reset_dag_run=False,
    wait_for_completion=False,
    trigger_rule=TriggerRule.ALL_DONE,
    dag=dag,
)

# Tâche 10: Fin du pipeline - Affiche le statut final
end_task = BashOperator(
    task_id="end_pipeline",
    bash_command="""
    echo "=============================================="
    echo " Pipeline ML Terminé"
    echo " Date: $(date)"
    echo " Statut: SUCCESS"
    echo " Modèle sauvegardé: /opt/airflow/model/"
    echo " Résumé disponible dans: /opt/airflow/model/model_summary.txt"
    echo "=============================================="
    """,
    trigger_rule=TriggerRule.ALL_DONE,
    dag=dag,
)

# Définition des dépendances entre les tâches
start_task >> load_data_task >> data_preprocessing_task >> separate_data_task
separate_data_task >> build_model_task >> evaluate_model_task >> summary_task

# Branchement des emails (succès vs échec)
summary_task >> success_email
summary_task >> failure_email

# Fin du pipeline et déclenchement de l'API
success_email >> trigger_flask_task >> end_task
failure_email >> trigger_flask_task >> end_task

# Fonction Flask intégrée pour le monitoring
def create_flask_app():
    """
    Crée et configure l'application Flask pour le monitoring du pipeline ML
    """
    app = Flask(__name__)

    @app.route('/health')
    def health_check():
        """Health check endpoint"""
        return jsonify({
            "status": "healthy",
            "service": "ml_pipeline_monitoring",
            "timestamp": datetime.now().isoformat(),
            "dag_id": "ml_pipeline_advertising"
        })

    @app.route('/api/status')
    def dag_status():
        """Endpoint pour vérifier le statut du DAG"""
        try:
            # Simuler le statut basé sur les fichiers de sortie
            model_path = "/opt/airflow/model/logistic_regression_model.pkl"
            summary_path = "/opt/airflow/model/model_summary.txt"

            if os.path.exists(model_path) and os.path.exists(summary_path):
                # Lire les informations du modèle
                import pickle
                with open(model_path, 'rb') as f:
                    model = pickle.load(f)

                with open(summary_path, 'r') as f:
                    summary = f.read()

                return jsonify({
                    "status": "success",
                    "message": "Pipeline ML exécuté avec succès",
                    "timestamp": datetime.now().isoformat(),
                    "model_info": {
                        "type": str(type(model).__name__),
                        "model_path": model_path,
                        "summary_path": summary_path,
                        "last_updated": datetime.fromtimestamp(os.path.getmtime(model_path)).isoformat()
                    }
                })
            else:
                return jsonify({
                    "status": "pending",
                    "message": "Le pipeline ML n'a pas encore été exécuté",
                    "timestamp": datetime.now().isoformat()
                }), 404

        except Exception as e:
            return jsonify({
                "status": "error",
                "message": f"Erreur lors de la vérification du statut: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }), 500

    @app.route('/api/metrics')
    def get_metrics():
        """Endpoint pour récupérer les métriques du modèle"""
        try:
            summary_path = "/opt/airflow/model/model_summary.txt"

            if os.path.exists(summary_path):
                with open(summary_path, 'r') as f:
                    summary_content = f.read()

                # Parser le contenu pour extraire les métriques
                import re
                metrics = {
                    "model_type": "Logistic Regression",
                    "dataset": "advertising.csv",
                    "last_updated": datetime.fromtimestamp(os.path.getmtime(summary_path)).isoformat(),
                    "summary": summary_content
                }

                # Extraire les scores du résumé
                train_match = re.search(r'Score Train:\s*([\d.]+)', summary_content)
                test_match = re.search(r'Score Test:\s*([\d.]+)', summary_content)

                if train_match:
                    metrics["train_score"] = float(train_match.group(1))
                if test_match:
                    metrics["test_score"] = float(test_match.group(1))

                return jsonify(metrics)
            else:
                return jsonify({
                    "error": "Model summary not found",
                    "message": "Executez le DAG principal d'abord pour générer les métriques"
                }), 404

        except Exception as e:
            return jsonify({
                "error": "Internal server error",
                "message": str(e)
            }), 500

    @app.route('/')
    def index():
        """Page d'accueil - informations du pipeline"""
        return jsonify({
            "service": "ML Pipeline Monitoring API",
            "version": "1.0.0",
            "endpoints": {
                "/health": "Health check",
                "/api/status": "Statut du DAG ML",
                "/api/metrics": "Métriques du modèle"
            },
            "timestamp": datetime.now().isoformat()
        })

    return app

# Fonction pour démarrer l'API Flask (peut être appelée indépendamment)
def start_flask_monitoring():
    """
    Démarre l'API Flask de monitoring intégrée
    """
    app = create_flask_app()
    print("🚀 Démarrage de l'API Flask intégrée...")
    print("📡 Endpoints disponibles:")
    print("  - GET  /health     -> Health check")
    print("  - GET  /           -> Informations")
    print("  - GET  /api/status -> Statut DAG ML")
    print("  - GET  /api/metrics -> Métriques modèle")
    print("🌐 Port: 5000")
    app.run(host="0.0.0.0", port=5000, debug=True)

# Point d'entrée pour exécution directe
if __name__ == "__main__":
    start_flask_monitoring()