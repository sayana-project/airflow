# Fichier: model_development.py
import os
import pickle
import pandas as pd
from sklearn.compose import make_column_transformer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler, StandardScaler

# Définition des chemins pour Airflow
WORKING_DIR = "/opt/airflow/working_data"
MODEL_DIR = "/opt/airflow/model"

# Création des répertoires s'ils n'existent pas
os.makedirs(WORKING_DIR, exist_ok=True)
os.makedirs(MODEL_DIR, exist_ok=True)

def load_data() -> str:
    """
    Charger le fichier CSV advertising.csv et sauvegarder le dataframe brut.

    Returns:
        str: Chemin vers le fichier pickle sauvegardé
    """
    csv_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),  # Remonter de src/dags à la racine
        "advertising.csv",
    )

    # Charger les données
    df = pd.read_csv(csv_path)

    # Sauvegarder en pickle
    out_path = os.path.join(WORKING_DIR, "raw.pkl")
    with open(out_path, "wb") as f:
        pickle.dump(df, f)

    print(f"Données brutes chargées et sauvegardées: {df.shape}")
    return out_path

def data_preprocessing(file_path: str) -> str:
    """
    Prétraiter les données: nettoyage, splitting, scaling

    Args:
        file_path: Chemin vers le fichier pickle des données brutes

    Returns:
        str: Chemin vers le fichier pickle prétraité
    """
    # Charger les données brutes
    with open(file_path, "rb") as f:
        df = pickle.load(f)

    # Préparation des features et target
    X = df.drop(
        ["Timestamp", "Clicked on Ad", "Ad Topic Line", "Country", "City"],
        axis=1,
    )
    y = df["Clicked on Ad"]

    print(f"Features shape: {X.shape}, Target shape: {y.shape}")

    # Split train/test
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.3, random_state=42
    )

    print(f"Train set: {X_train.shape}, Test set: {X_test.shape}")

    # Définition des colonnes numériques pour le scaling
    num_columns = [
        "Daily Time Spent on Site",
        "Age",
        "Area Income",
        "Daily Internet Usage",
        "Male",
    ]

    # Création du ColumnTransformer pour le preprocessing
    ct = make_column_transformer(
        (MinMaxScaler(), num_columns),
        (StandardScaler(), num_columns),
        remainder="passthrough",
    )

    # Appliquer le preprocessing
    X_train_tr = ct.fit_transform(X_train)
    X_test_tr = ct.transform(X_test)

    print(f"X_train transformé shape: {X_train_tr.shape}")
    print(f"X_test transformé shape: {X_test_tr.shape}")

    # Sauvegarder les données prétraitées
    out_path = os.path.join(WORKING_DIR, "preprocessed.pkl")
    with open(out_path, "wb") as f:
        pickle.dump((X_train_tr, X_test_tr, y_train.values, y_test.values), f)

    return out_path

def separate_data_outputs(file_path: str) -> str:
    """
    Fonction de passage pour maintenir la structure du DAG

    Args:
        file_path: Chemin vers le fichier pickle prétraité

    Returns:
        str: Même chemin (passthrough)
    """
    return file_path

def build_model(file_path: str, filename: str) -> str:
    """
    Entraîner le modèle de régression logistique et le sauvegarder

    Args:
        file_path: Chemin vers le fichier pickle prétraité
        filename: Nom du fichier modèle à sauvegarder

    Returns:
        str: Chemin vers le modèle sauvegardé
    """
    # Charger les données prétraitées
    with open(file_path, "rb") as f:
        X_train, X_test, y_train, y_test = pickle.load(f)

    print(f"Entraînement du modèle avec X_train shape: {X_train.shape}")

    # Création et entraînement du modèle
    model = LogisticRegression(random_state=42, max_iter=1000)
    model.fit(X_train, y_train)

    # Sauvegarder le modèle
    model_path = os.path.join(MODEL_DIR, filename)
    with open(model_path, "wb") as f:
        pickle.dump(model, f)

    print(f"Modèle entraîné et sauvegardé: {model_path}")
    return model_path

def load_model(file_path: str, filename: str) -> int:
    """
    Charger le modèle et faire des prédictions

    Args:
        file_path: Chemin vers le fichier pickle prétraité
        filename: Nom du fichier modèle

    Returns:
        int: Première prédiction du modèle
    """
    # Charger les données prétraitées
    with open(file_path, "rb") as f:
        X_train, X_test, y_train, y_test = pickle.load(f)

    # Charger le modèle entraîné
    model_path = os.path.join(MODEL_DIR, filename)
    with open(model_path, "rb") as f:
        model = pickle.load(f)

    # Évaluer le modèle
    score = model.score(X_test, y_test)
    print(f"Score du modèle sur les données de test: {score:.4f}")

    # Faire une prédiction
    pred = model.predict(X_test)
    print(f"Exemple de prédiction: {pred[0]}")

    # Retourner la première prédiction comme entier
    return int(pred[0])

def print_model_summary(file_path: str, filename: str) -> str:
    """
    Afficher un résumé détaillé du modèle

    Args:
        file_path: Chemin vers le fichier pickle prétraité
        filename: Nom du fichier modèle

    Returns:
        str: Résumé du modèle
    """
    # Charger les données et le modèle
    with open(file_path, "rb") as f:
        X_train, X_test, y_train, y_test = pickle.load(f)

    model_path = os.path.join(MODEL_DIR, filename)
    with open(model_path, "rb") as f:
        model = pickle.load(f)

    # Calculer les métriques
    train_score = model.score(X_train, y_train)
    test_score = model.score(X_test, y_test)

    # Créer le résumé
    summary = f"""
    === Résumé du modèle de Régression Logistique ===

    📊 Performance:
    - Score Train: {train_score:.4f}
    - Score Test:  {test_score:.4f}
    - Différence:  {abs(train_score - test_score):.4f}

    📈 Données:
    - Train samples: {len(y_train)}
    - Test samples:  {len(y_test)}
    - Ratio Test:    {len(y_test)/(len(y_train)+len(y_test)):.2%}

    🎯 Classes:
    - Classe 0 (Pas de click): {len(y_test)-sum(y_test)} samples
    - Classe 1 (Click):       {sum(y_test)} samples

    📋 Features: 5 features numériques après preprocessing
    """

    print(summary)

    # Sauvegarder le résumé
    summary_path = os.path.join(MODEL_DIR, "model_summary.txt")
    with open(summary_path, "w") as f:
        f.write(summary)

    return summary_path