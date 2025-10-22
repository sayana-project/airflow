# Fichier: Flask_DAG.py - DAG pour l'API Flask de monitoring
from __future__ import annotations

import pendulum
from airflow import DAG
from airflow.providers.standard.operators.bash import BashOperator

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

# Définition du DAG Flask
flask_dag = DAG(
    dag_id="ml_pipeline_flask_api",
    default_args=default_args,
    description="API Flask pour le monitoring du pipeline ML",
    schedule=None,  # DAG déclenché manuellement ou par trigger
    catchup=False,
    tags=["api", "monitoring", "flask"],
    max_active_runs=1,
    doc_md="""
    ## API Flask - Monitoring Pipeline ML

    Ce DAG démarre l'API Flask pour le monitoring du pipeline ML:
    - Endpoint / : Redirection succès/échec
    - Endpoint /api/status : Statut du DAG principal
    - Endpoint /success : Page de succès
    - Endpoint /failure : Page d'échec
    - Endpoint /health : Health check
    - Endpoint /api/metrics : Métriques du modèle

    ### Démarrage:
    ```bash
    python dags/Flask_API.py
    ```

    ### Accès:
    - UI: http://localhost:5000
    - API: http://localhost:5000/api/status
    """,
)

# Tâche de démarrage de l'API Flask
start_flask_api = BashOperator(
    task_id="start_flask_api",
    bash_command="""
    echo "=============================================="
    echo " Démarrage de l'API Flask de monitoring"
    echo " Date: $(date)"
    echo " Port: 5000"
    echo " Endpoints disponibles:"
    echo "  - GET  /           -> Redirection succès/échec"
    echo "  - GET  /api/status -> Statut DAG ML"
    echo "  - GET  /success    -> Page succès"
    echo "  - GET  /failure    -> Page échec"
    echo "  - GET  /health     -> Health check"
    echo "  - GET  /api/metrics -> Métriques modèle"
    echo "=============================================="
    echo ""
    echo " Démarrage de l'application Flask..."
    echo "  Note: L'API s'exécute en foreground (Ctrl+C pour arrêter)"
    echo "=============================================="

    # Démarrer l'API Flask
    python dags/Flask_API.py
    """,
    dag=flask_dag,
)

# Tâche de vérification de l'API
health_check = BashOperator(
    task_id="api_health_check",
    bash_command="""
    echo " Vérification de la disponibilité de l'API..."

    # Attendre quelques secondes que l'API démarre
    sleep 5

    # Tester l'endpoint health
    if curl -s http://localhost:5000/health | grep -q "healthy"; then
        echo " API Flask est opérationnelle"
        echo " Accessible à: http://localhost:5000"
        echo " API Status: http://localhost:5000/api/status"
        exit 0
    else
        echo " API Flask n'est pas accessible"
        exit 1
    fi
    """,
    dag=flask_dag,
)

# Dépendances
start_flask_api >> health_check