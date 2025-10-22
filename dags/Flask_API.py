# Fichier: Flask_API.py - API Flask pour le monitoring du DAG
from flask import Flask, redirect, render_template, request, jsonify
import requests
import os
from datetime import datetime
import json

app = Flask(__name__, template_folder="templates")

# Configuration Airflow
AIRFLOW_BASE_URL = "http://localhost:8080/api/v1"
AIRFLOW_USERNAME = "airflow"
AIRFLOW_PASSWORD = "airflow"

def get_airflow_auth():
    """
    Récupérer le token d'authentification Airflow
    """
    auth_url = f"{AIRFLOW_BASE_URL}/auth/login"
    auth_data = {
        "username": AIRFLOW_USERNAME,
        "password": AIRFLOW_PASSWORD
    }

    try:
        response = requests.post(auth_url, json=auth_data)
        response.raise_for_status()
        return response.json()["access_token"]
    except requests.exceptions.RequestException as e:
        print(f"Erreur d'authentification Airflow: {e}")
        return None

def get_latest_dag_run(dag_id="ml_pipeline_advertising"):
    """
    Récupérer les informations sur la dernière exécution du DAG
    """
    token = get_airflow_auth()
    if not token:
        return False, {"error": "Impossible de s'authentifier à Airflow"}

    headers = {"Authorization": f"Bearer {token}"}
    url = f"{AIRFLOW_BASE_URL}/dags/{dag_id}/dagRuns"

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        dag_runs = response.json()["dag_runs"]

        if not dag_runs:
            return False, {"message": "Aucune exécution trouvée"}

        # Récupérer la dernière exécution
        latest_run = dag_runs[0]
        run_id = latest_run["dag_run_id"]

        # Récupérer les détails de l'exécution
        details_url = f"{AIRFLOW_BASE_URL}/dags/{dag_id}/dagRuns/{run_id}"
        details_response = requests.get(details_url, headers=headers)
        details_response.raise_for_status()
        run_details = details_response.json()

        # Déterminer le statut
        status = run_details["state"]
        is_success = status == "success"

        # Formater les informations
        info = {
            "dag_id": dag_id,
            "run_id": run_id,
            "status": status,
            "execution_date": run_details["execution_date"],
            "start_date": run_details["start_date"],
            "end_date": run_details["end_date"],
            "duration": "N/A"
        }

        # Calculer la durée si les dates sont disponibles
        if run_details["start_date"] and run_details["end_date"]:
            start = datetime.fromisoformat(run_details["start_date"].replace('Z', '+00:00'))
            end = datetime.fromisoformat(run_details["end_date"].replace('Z', '+00:00'))
            duration = end - start
            info["duration"] = str(duration)

        return is_success, info

    except requests.exceptions.RequestException as e:
        return False, {"error": f"Erreur de communication avec Airflow: {e}"}

@app.route("/")
def index():
    """
    Page d'accueil - Redirection vers succès/échec
    """
    ok, info = get_latest_dag_run()
    return redirect("/success" if ok else "/failure")

@app.route("/api/status")
def api_status():
    """
    API endpoint pour le statut du DAG
    """
    ok, info = get_latest_dag_run()
    status = {
        "status": "success" if ok else "failure",
        "timestamp": datetime.now().isoformat(),
        "dag_info": info
    }
    return jsonify(status)

@app.route("/success")
def success():
    """
    Page de succès
    """
    ok, info = get_latest_dag_run()
    return render_template("success.html", **info)

@app.route("/failure")
def failure():
    """
    Page d'échec
    """
    ok, info = get_latest_dag_run()
    return render_template("failure.html", **info)

@app.route("/health")
def health_check():
    """
    Health check endpoint
    """
    return jsonify({
        "status": "healthy",
        "service": "ml_pipeline_flask_api",
        "timestamp": datetime.now().isoformat()
    })

@app.route("/api/metrics")
def get_metrics():
    """
    API endpoint pour les métriques du modèle
    """
    try:
        # Essayer de lire le résumé du modèle
        summary_path = "/opt/airflow/model/model_summary.txt"

        if os.path.exists(summary_path):
            with open(summary_path, 'r') as f:
                summary_content = f.read()

            # Parser le contenu pour extraire les métriques
            metrics = {
                "model_type": "Logistic Regression",
                "dataset": "advertising.csv",
                "last_updated": datetime.fromtimestamp(os.path.getmtime(summary_path)).isoformat(),
                "summary": summary_content
            }

            # Extraire les scores du résumé
            import re
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
                "message": "Run the DAG first to generate model metrics"
            }), 404

    except Exception as e:
        return jsonify({
            "error": "Internal server error",
            "message": str(e)
        }), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)