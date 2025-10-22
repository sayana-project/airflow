#!/usr/bin/env python3
"""
Script de test pour la configuration SMTP Gmail
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

def test_smtp_connection():
    """Teste la connexion SMTP avec Gmail"""

    # Configuration depuis .env
    smtp_host = "smtp.gmail.com"
    smtp_port = 587
    smtp_user = "pierce.hawthorne59@gmail.com"
    smtp_password = "pavk wicm jhuq kpyi"  # Votre app password
    to_email = "pierce.hawthorne59@gmail.com"

    print("=== Test SMTP Gmail ===")
    print(f"Serveur: {smtp_host}:{smtp_port}")
    print(f"Utilisateur: {smtp_user}")
    print(f"Destinataire: {to_email}")
    print()

    try:
        # Création du message
        msg = MIMEMultipart()
        msg['From'] = smtp_user
        msg['To'] = to_email
        msg['Subject'] = "Test SMTP - Configuration Airflow"

        body = f"""
        <h2>Test de configuration SMTP</h2>
        <p>Ceci est un email de test pour vérifier la configuration SMTP.</p>
        <p>Si vous recevez cet email, la configuration SMTP fonctionne correctement.</p>
        <p><strong>Détails:</strong></p>
        <ul>
            <li>Serveur: smtp.gmail.com</li>
            <li>Port: 587</li>
            <li>STARTTLS: Activé</li>
            <li>Date: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</li>
        </ul>
        """

        msg.attach(MIMEText(body, 'html'))

        # Connexion au serveur SMTP
        print("1. Connexion au serveur SMTP...")
        server = smtplib.SMTP(smtp_host, smtp_port)
        server.set_debuglevel(1)  # Mode debug pour voir les échanges

        print("2. Activation STARTTLS...")
        server.starttls()

        print("3. Authentification...")
        server.login(smtp_user, smtp_password)

        print("4. Envoi de l'email...")
        text = msg.as_string()
        server.sendmail(smtp_user, to_email, text)

        print("5. Déconnexion...")
        server.quit()

        print("\n✅ SUCCÈS: Email envoyé avec succès!")
        return True

    except smtplib.SMTPAuthenticationError as e:
        print(f"\nERREUR d'authentification: {e}")
        print("Vérifiez:")
        print("- Le mot de passe d'application Gmail est correct")
        print("- L'authentification en 2 étapes est activée sur votre compte")
        print("- Le mot de passe d'application est bien généré pour cette app")
        return False

    except smtplib.SMTPException as e:
        print(f"\nERREUR SMTP: {e}")
        return False

    except Exception as e:
        print(f"\nERREUR inattendue: {e}")
        return False

if __name__ == "__main__":
    success = test_smtp_connection()

    if success:
        print("\nSUCCES: La configuration SMTP est correcte!")
    else:
        print("\nATTENTION: La configuration SMTP a des problèmes.")
        print("\nConseils:")
        print("1. Vérifiez que l'authentification en 2 étapes est activée")
        print("2. Générez un nouveau mot de passe d'application Gmail")
        print("3. Vérifiez que le mot de passe d'application est correctement copié")