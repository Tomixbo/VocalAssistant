from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel
from typing import Dict, Any
import pandas as pd
import os

app = FastAPI()

# Chemin du fichier Excel
file_path = './data/Dossiers_Cabinet_Comptable.xlsx'

# Lecture des données du fichier Excel
def read_dossiers():
    if os.path.exists(file_path):
        df = pd.read_excel(file_path, sheet_name='dossiers')
        dossiers = df.to_dict(orient='records')
        # Convert keys to match the Pydantic model
        converted_dossiers = []
        for dossier in dossiers:
            converted_dossier = {
                "Numero_de_Dossier": dossier["Numero de Dossier"],
                "Nom_du_Client": dossier["Nom du Client"],
                "Date_de_Debut": dossier["Date de Debut"],
                "Date_de_Fin_Prevue": dossier["Date de Fin Prevue"],
                "Etat_d_Avancement": dossier["Etat d'Avancement"],
                "Responsable": dossier["Responsable"],
                "Commentaires": dossier["Commentaires"]
            }
            converted_dossiers.append(converted_dossier)
        return converted_dossiers
    return []

# Sauvegarde des données dans le fichier Excel
def save_dossiers(dossiers):
    df = pd.DataFrame(dossiers)
    # Convert keys back to the original format before saving
    df.columns = [
        "Numero de Dossier",
        "Nom du Client",
        "Date de Debut",
        "Date de Fin Prevue",
        "Etat d'Avancement",
        "Responsable",
        "Commentaires"
    ]
    df = df.rename(columns={
        "Numero_de_Dossier": "Numero de Dossier",
        "Nom_du_Client": "Nom du Client",
        "Date_de_Debut": "Date de Debut",
        "Date_de_Fin_Prevue": "Date de Fin Prevue",
        "Etat_d_Avancement": "Etat d'Avancement",
        "Responsable": "Responsable",
        "Commentaires": "Commentaires"
    })
    with pd.ExcelWriter(file_path, engine='openpyxl', mode='w') as writer:
        df.to_excel(writer, sheet_name='dossiers', index=False)

# Modèle de données pour un dossier complet
class Dossier(BaseModel):
    Numero_de_Dossier: int
    Nom_du_Client: str
    Date_de_Debut: str
    Date_de_Fin_Prevue: str
    Etat_d_Avancement: str
    Responsable: str
    Commentaires: str

# Modèle de données pour un dossier en entrée POST (sans Numero_de_Dossier)
class DossierCreate(BaseModel):
    Nom_du_Client: str
    Date_de_Debut: str
    Date_de_Fin_Prevue: str
    Etat_d_Avancement: str
    Responsable: str
    Commentaires: str

# Modèle de réponse pour inclure un message de succès et un dossier
class DossierResponse(BaseModel):
    message: str
    dossier: Dossier

# Gestionnaire d'exception pour les erreurs de validation
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=400,
        content={"detail": exc.errors()}
    )

# Endpoint GET pour récupérer la liste des dossiers
@app.get("/dossiers", response_model=Dict[str, Any])
def get_dossiers():
    dossiers = read_dossiers()
    return {"total_dossiers": len(dossiers), "dossiers": dossiers}

# Endpoint POST pour ajouter un nouveau dossier
@app.post("/dossiers/add", response_model=DossierResponse)
def add_dossier(dossier: DossierCreate):
    dossiers = read_dossiers()
    # Détermination du nouvel ID basé sur le maximum existant
    if dossiers:
        new_id = max(dossier["Numero_de_Dossier"] for dossier in dossiers) + 1
    else:
        new_id = 1

    # Création du nouveau dossier avec ID incrémenté
    new_dossier = {
        "Numero_de_Dossier": new_id,
        "Nom_du_Client": dossier.Nom_du_Client,
        "Date_de_Debut": dossier.Date_de_Debut,
        "Date_de_Fin_Prevue": dossier.Date_de_Fin_Prevue,
        "Etat_d_Avancement": dossier.Etat_d_Avancement,
        "Responsable": dossier.Responsable,
        "Commentaires": dossier.Commentaires
    }
    dossiers.append(new_dossier)
    save_dossiers(dossiers)
    
    return {"message": "Dossier ajouté avec succès", "dossier": new_dossier}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
