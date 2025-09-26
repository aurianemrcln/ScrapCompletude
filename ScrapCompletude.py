from concurrent.futures import wait
from lib2to3.pgen2 import driver
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import json
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
load_dotenv()

# --- Paramètres utilisateur ---
URL = os.getenv("URL")
USERNAME = os.getenv("Identifiant")
PASSWORD = os.getenv("MotDePasse")
STORAGE_FILE = os.getenv("Storage_File")

# --- Paramètres email ---
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = os.getenv("SMTP_PORT")
EMAIL_1 = os.getenv("EMAIL_1")
EMAIL_1_PASSWORD = os.getenv("EMAIL_1_PASSWORD")
EMAIL_2 = os.getenv("EMAIL_2")

def envoyer_mail(nouvelles_annonces):
    subject = "📢 Nouvelles offres détectées sur Complétude"
    body = "\n\n".join(
        [f"{a['ville']} - {a['matiere']} - {a['niveau']} - {a['tarif']} - {a['date_debut']} ({a['ref']})"
         for a in nouvelles_annonces]
    )

    msg = MIMEMultipart()
    msg["From"] = EMAIL_1
    msg["To"] = f"{EMAIL_1}, {EMAIL_2}"
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(EMAIL_1, EMAIL_1_PASSWORD)
        server.sendmail(EMAIL_1, [EMAIL_1, EMAIL_2], msg.as_string())

def charger_annonces_existantes():
    if os.path.exists(STORAGE_FILE):
        with open(STORAGE_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []

def sauvegarder_annonces(annonces):
    with open(STORAGE_FILE, "w", encoding="utf-8") as f:
        json.dump(annonces, f, ensure_ascii=False, indent=2)

def extraire_infos_offre(card):
    def safe_find(css):
        try:
            return card.find_element(By.CSS_SELECTOR, css).text.strip()
        except:
            return ""

    return {
        "ville": safe_find("h5"),
        "matiere": safe_find("div.subject"),
        "niveau": safe_find("div.level"),
        "tarif": safe_find("div.rate"),
        "date_debut": safe_find("div.start-date"),
        "ref": safe_find("div.reference"),
    }

def main():
    driver = webdriver.Chrome()
    wait = WebDriverWait(driver, 30)

    try:
        # Connexion
        driver.get(URL)
        username_input = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[name='username']")))
        username_input.send_keys(USERNAME)
        password_input = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[name='password']")))
        password_input.send_keys(PASSWORD)
        submit_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "ion-button[type='submit']")))
        driver.execute_script("arguments[0].click();", submit_button)

        # Sélection adresse
        champ_ou = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "div.result-container")))
        champ_ou.click()
        adresse = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "div.option-item.ng-star-inserted label")))
        adresse.click()

        # Voir les offres
        offres_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "ion-button[expand='full']")))
        driver.execute_script("arguments[0].click();", offres_button)

        # Récupérer les annonces
        time.sleep(3)
        cards = driver.find_elements(By.CSS_SELECTOR, "div.card")
        annonces = [extraire_infos_offre(c) for c in cards]

        # Comparer avec le fichier JSON
        anciennes = charger_annonces_existantes()
        anciennes_refs = {a["ref"] for a in anciennes}
        nouvelles = [a for a in annonces if a["ref"] not in anciennes_refs]

        if nouvelles:
            print(f"🚀 {len(nouvelles)} nouvelles offres détectées 😁 ! Envoi d'email 📧 ...")
            envoyer_mail(nouvelles)
            sauvegarder_annonces(annonces)  # met à jour le JSON
        else:
            print("Aucune nouvelle offre 🙁")

    finally:
        driver.quit()

if __name__ == "__main__":
    main()