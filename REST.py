from pydantic import BaseModel
import requests
import streamlit as st
# from fastapi import FastAPI, HTTPException

# app = FastAPI()

# Configuration Airtable
AIRTABLE_PAT = st.secrets["AIRTABLE_PAT"]
BASE_ID = st.secrets["BASE_ID"]
TABLE_NAME = st.secrets["TABLE_NAME"]

HEADERS = {
    'Authorization': f'Bearer {AIRTABLE_PAT}',
    'Content-Type': 'application/json'
}

# Modèle de données pour un dossier complet
class Dossier(BaseModel):
    Numero_de_Dossier: int
    Nom_du_Client: str
    Date_de_Début: str
    Date_de_Fin_Prevue: str
    Etat_d_Avancement: str
    Responsable: str
    Commentaires: str

# Modèle de données pour un dossier en entrée POST (sans Numero_de_Dossier)
class DossierCreate(BaseModel):
    Nom_du_Client: str
    Date_de_Début: str
    Date_de_Fin_Prevue: str
    Etat_d_Avancement: str
    Responsable: str
    Commentaires: str

# Fonction pour obtenir tous les dossiers
def get_all_dossiers():
    url = f'https://api.airtable.com/v0/{BASE_ID}/{TABLE_NAME}'
    response = requests.get(url, headers=HEADERS)
    if response.status_code != 200:
        print(f"message: Error à get du dossier - erreur {response.json()}")
        return False
    records = response.json().get('records', [])
    dossiers = []
    for record in records:
        fields = record.get('fields', {})
        dossiers.append({
            "Numero_de_Dossier": fields.get("Numero de Dossier"),
            "Nom_du_Client": fields.get("Nom du Client"),
            "Date_de_Debut": fields.get("Date de Debut"),
            "Date_de_Fin_Prevue": fields.get("Date de Fin Prevue"),
            "Etat_d_Avancement": fields.get("Etat d'Avancement"),
            "Responsable": fields.get("Responsable"),
            "Commentaires": fields.get("Commentaires")
        })
    return dossiers

# Endpoint GET pour récupérer la liste des dossiers
#@app.get("/dossiers")
def read_dossiers():
    dossiers = get_all_dossiers()
    return {"total_dossiers": len(dossiers), "dossiers": dossiers}

# Endpoint POST pour ajouter un nouveau dossier
#@app.post("/dossiers/add")
def create_dossier(dossier: DossierCreate):
    dossiers = get_all_dossiers()

    new_id = max([d["Numero_de_Dossier"] for d in dossiers] or [0]) + 1

    new_dossier = {
        "Numero de Dossier": new_id,
        "Nom du Client": dossier['Nom_du_Client'],
        "Date de Debut": dossier['Date_de_Debut'],
        "Date de Fin Prevue": dossier['Date_de_Fin_Prevue'],
        "Etat d'Avancement": dossier['Etat_d_Avancement'],
        "Responsable": dossier['Responsable'],
        "Commentaires": dossier['Commentaires']
    }
    print(new_dossier)

    url = f'https://api.airtable.com/v0/{BASE_ID}/{TABLE_NAME}'
    response = requests.post(url, headers=HEADERS, json={"fields": new_dossier})
    if response.status_code != 200:
        print(f"message: Error à l'ajout du dossier - erreur {response.json()}")
        return False

    return {"message": "Dossier ajouté avec succès", "dossier": new_dossier}

"""if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)"""
