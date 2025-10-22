# Fichier: main.py - DAG principal pour le pipeline ML
from __future__ import annotations

import os
import sys
import pendulum
from airflow import DAG

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
    - Airflow 3.1.0
    - Scikit-learn 1.7.2
    - Python 3.13+
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
    "",
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
        <li><strong>Modèle:</strong> Régression Logistique</li>
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
    "",
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
    "",
    trigger_rule=TriggerRule.ONE_FAILED,
    dag=dag,
)

# Tâche 9: Déclenchement du DAG Flask pour le monitoring
trigger_flask_task = TriggerDagRunOperator(
    task_id="trigger_flask_api",
    trigger_dag_id="ml_pipeline_flask_api",
    conf={
        "message": "Pipeline ML principal terminé avec succès",
        "dag_id": "ml_pipeline_advertising",
        "status": "success",
        "triggered_by": "ml_pipeline_main"
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
    "",
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