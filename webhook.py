import requests
from flask import Flask, request, jsonify
import threading
import time

app = Flask(__name__)

# Dictionnaire pour stocker les réponses reçues par identifiant unique
responses = {}
lock = threading.Lock()

@app.route('/webhook', methods=['POST'])
def webhook():
    # Récupérer les données envoyées par n8n
    data = request.json
    request_id = data.get('request_id')  # Récupérer l'identifiant unique
    collaborators = data.get('Data', [])
    
    # Stocker la réponse dans le dictionnaire avec le verrou
    with lock:
        responses[request_id] = collaborators
    
    return jsonify({"status": "received"}), 200

def start_workflow_and_get_response():
    # Générer un identifiant unique pour cette requête
    request_id = str(threading.get_ident())

    # Envoyer la requête GET pour lancer le workflow n8n
    url = "https://n8n.tomixbo.com/webhook/automation01"
    headers = {"Authorization": "1234"}
    params = {"request_id": request_id}  # Passer l'identifiant unique

    response = requests.get(url, headers=headers, params=params, verify=False)
    
    if response.status_code != 200:
        raise Exception("Failed to start n8n workflow")
    
    # Attendre que le webhook envoie les données pour cet identifiant unique
    for _ in range(60):  # Attendre jusqu'à 60 secondes
        with lock:
            if request_id in responses:
                collaborators = responses.pop(request_id)  # Supprime et retourne les données
                return collaborators
        time.sleep(1)  # Attendre 1 seconde avant de vérifier à nouveau
    
    raise TimeoutError("No data received from webhook after 60 seconds")

@app.route('/get-collaborators', methods=['GET'])
def get_collaborators():
    try:
        collaborators = start_workflow_and_get_response()
        return jsonify({"success": True, "collaborators": collaborators}), 200
    except TimeoutError as e:
        return jsonify({"success": False, "error": str(e)}), 504

if __name__ == '__main__':
    app.run(host='192.168.88.254', port=5000, debug=True)
