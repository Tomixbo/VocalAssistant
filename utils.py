import json
from openai import OpenAI
import streamlit as st
import base64
from REST import read_dossiers, create_dossier
import requests


# Set OpenAI API key from Streamlit secrets
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
#model = "gpt-3.5-turbo-0125"

assistant = None
thread = None

def init_model(assistant_id, thread_id=None):
    global assistant  # Déclare la variable assistant comme globale
    global thread    # Déclare la variable thread comme globale

    assistant=client.beta.assistants.retrieve(assistant_id=assistant_id)
    print(f"ASSISTANT::: {assistant.id}")
    if not thread_id:
        thread=client.beta.threads.create()
    else:
        thread=client.beta.threads.retrieve(thread_id=thread_id)
    print(f"THREAD::: {thread.id}")
    return thread


def speech_to_text(audio_data):
    try:
        with open(audio_data, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                response_format="text",
                file=audio_file
            )
        return transcript
    except Exception as e:
        print(e)
        return

def text_to_speech(input_text):
    response = client.audio.speech.create(
        model="tts-1",
        voice="nova",
        input=input_text
    )
    webm_file_path = "temp_audio_play.mp3"
    with open(webm_file_path, "wb") as f:  # noqa: F841
        response.stream_to_file(webm_file_path)
    return webm_file_path

def get_answer(message, thread_):
    
    # === Create a Message ===
    message = client.beta.threads.messages.create(
        thread_id=thread_.id,
        role="user",
        content=message
    )

    # === Run our Assistant ===
    run = client.beta.threads.runs.create(
        thread_id=thread_.id,
        assistant_id=assistant.id,
        instructions=""
    )

    while True:
        run = client.beta.threads.runs.retrieve(thread_id=thread_.id, run_id=run.id)
        print(f"\n RUN STATUS : ---> {run.status}")
        try:
            if run.status == "completed":
                # Get messages here once Run is completed!
                messages = client.beta.threads.messages.list(thread_id=thread_.id)
                response = messages.data[0].content[0].text.value
                annotations = messages.data[0].content[0].text.annotations
                print(response, annotations)
                citations = []

                # Iterate over the annotations and add footnotes
                for index, annotation in enumerate(annotations):
                    # Replace the text with a footnote
                    response = response.replace(annotation.text, f' [{index}]')
                    # Gather citations based on annotation attributes
                    if (file_citation := getattr(annotation, 'file_citation', None)):
                        cited_file = client.files.retrieve(file_citation.file_id)
                        if cited_file.filename not in ' '.join(citations):
                            citations.append(f'[{index}] - {cited_file.filename}')
                    elif (file_path := getattr(annotation, 'file_path', None)):
                        cited_file = client.files.retrieve(file_path.file_id)
                        citations.append(f'[{index}] - Click <here> to download {cited_file.filename} \n')
                        # Note: File download functionality not implemented above for brevity
                # Add footnotes to the end of the message before displaying to user

                response += '\n\n' + '\n\n'.join(citations)    
                print(response)
                return response
            
            elif run.status == "requires_action":
                    print("FUNCTION CALLING NOW...")
                    call_required_functions(
                        required_actions=run.required_action.submit_tool_outputs.model_dump(), thread_ = thread_, run_=run
                    )
        except Exception as e:
            print(f"An error occurred while retrieving the run : {e}")
            break


def autoplay_audio(file_path: str):
    with open(file_path, "rb") as f:
        data = f.read()
    b64 = base64.b64encode(data).decode("utf-8")
    md = f"""
    <audio controls autoplay>
    <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
    </audio>
    """
    st.markdown(md, unsafe_allow_html=True)

def sticky_header():

    # make header sticky.
    st.markdown(
        """
            <div class='fixed-header'/>
            <style>
                div[data-testid="stVerticalBlock"] div:has(div.fixed-header) {
                    position: sticky;
                    top: 2.875rem;
                    background-color: white;
                    z-index: 990;
                }
                .fixed-header {
                    border-bottom: 1px solid black;
                }
            </style>
        """,
        unsafe_allow_html=True
    )



# Function to make footer fixed at the bottom
def sticky_footer():
    st.markdown(
        """ <div class='fixed-footer'/>
            <style>
                div[data-testid="stVerticalBlock"] div:has(div.fixed-footer) {
                    position: sticky;
                    bottom: 0;
                    width: 100%;
                    background-color: white;
                    z-index: 990;
                }
                .fixed-footer {
                    top:100px;
                    border-top: 1px solid black;
                    padding: 10px 0;
                    text-align: center;
                }
            </style>
        """,
        unsafe_allow_html=True
    )

def get_dossiers():
    result = read_dossiers()
    print(result)
    if result:
        total_dossiers = result["total_dossiers"]
        dossiers = result["dossiers"]
        tasks_list = [f"Total dossiers: {total_dossiers}"]

        for d in dossiers:
            task_description = (
                f"Numero_de_Dossier: {d['Numero_de_Dossier']}, "
                f"Nom_du_Client: {d['Nom_du_Client']}, "
                f"Date_de_Debut: {d['Date_de_Debut']}, "
                f"Date_de_Fin_Prevue: {d['Date_de_Fin_Prevue']}, "
                f"Etat_d_Avancement: {d['Etat_d_Avancement']}, "
                f"Responsable: {d['Responsable']}, "
                f"Commentaires: {d['Commentaires']}"
            )
            tasks_list.append(task_description)

        return "\n".join(tasks_list)
    else:
        return "Erreur fetch dossier"

def get_collaborators():
    response = requests.get("http://192.168.88.254:5000/get-collaborators")
    
    # Vérifier si la requête a réussi
    if response.status_code == 200:
        data = response.json()
        
        # Vérifier si la réponse contient un succès
        if data.get("success"):
            collabs = []
            for c in data.get("collaborators", []):
                collab_description = (
                    f"Nom_du_Collaborateur: {c['Nom du Collaborateur']}, "
                    f"Entreprise: {c['Entreprise']}, "
                    f"Email: {c['Email']}, "
                    f"Telephone: {c['Telephone']}"
                )
                collabs.append(collab_description)
            
            # Retourner la liste des collaborateurs sous forme de chaîne
            return "\n".join(collabs)
        else:
            # Gérer le cas où il y a une erreur côté serveur
            return f"Erreur du serveur: {data.get('error', 'Erreur inconnue')}"
    else:
        # Gérer le cas où la requête n'a pas réussi
        return f"Erreur HTTP: {response.status_code}"

    
def add_dossier(nom_du_client, date_de_debut, date_de_fin_prevue, etat_d_avancement, responsable, commentaires):
    data = {
        "Nom_du_Client": nom_du_client,
        "Date_de_Debut": date_de_debut,
        "Date_de_Fin_Prevue": date_de_fin_prevue,
        "Etat_d_Avancement": etat_d_avancement,
        "Responsable": responsable,
        "Commentaires": commentaires
    }
    print(data)
    response = create_dossier(data)
    if response:
        print("Dossier ajouté avec succès:", response)
        return f"Dossier ajouté avec succès: {response}"
    else:
        return "Error à l'ajout du dossier"

def add_collaborator(nom_du_collaborateur, entreprise, email, telephone):
    # Créer les données du nouveau collaborateur
    data = {
        "Nom_du_Collaborateur": nom_du_collaborateur,
        "Entreprise": entreprise,
        "Email": email,
        "Telephone": telephone
    }
    
    print(data)
    
    # Envoyer la requête POST au serveur Flask pour ajouter le collaborateur
    response = requests.post("http://192.168.88.254:5000/add-collaborator", json=data)
    
    # Vérifier si la requête a réussi
    if response.status_code == 200:
        c = response.json()  # Récupérer la réponse JSON
        collab = f"Nom_du_Collaborateur: {data['Nom_du_Collaborateur']}, Entreprise: {data['Entreprise']}, Email: {data['Email']}, Telephone: {data['Telephone']}"
        print("Collaborateur ajouté avec succès:", collab)
        return f"Collaborateur ajouté avec succès: {collab}"
    else:
        return f"Problème à l'ajout du nouveau collaborateur - Erreur {response.status_code}"


def call_required_functions(required_actions, thread_, run_):
    if not run_:
        return
    tool_outputs = []

    for action in required_actions["tool_calls"]:
        func_name = action["function"]["name"]
        arguments = json.loads(action["function"]["arguments"])

        if func_name == "get_dossiers":
            output = get_dossiers()
            print(f"STUFFFF::::{output}")
            tool_outputs.append({
                "tool_call_id": action["id"],
                "output": output
            })
        elif func_name == "add_dossier":
            output = add_dossier(
                nom_du_client=arguments["Nom_du_Client"],
                date_de_debut=arguments["Date_de_Debut"],
                date_de_fin_prevue=arguments["Date_de_Fin_Prevue"],
                etat_d_avancement=arguments["Etat_d_Avancement"],
                responsable=arguments["Responsable"],
                commentaires=arguments["Commentaires"]
            )
            print(f"STUFFFF::::{output}")
            tool_outputs.append({
                "tool_call_id": action["id"],
                "output": output
            })
        elif func_name == "get_collaborators":
            output = get_collaborators()
            print(f"STUFFFF::::{output}")
            tool_outputs.append({
                "tool_call_id": action["id"],
                "output": output
            })
        elif func_name == "add_collaborator":
            output = add_collaborator(
                nom_du_collaborateur=arguments["Nom_du_Collaborateur"],
                entreprise=arguments["Entreprise"],
                email=arguments["Email"],
                telephone=arguments["Telephone"]
            )
            print(f"STUFFFF::::{output}")
            tool_outputs.append({
                "tool_call_id": action["id"],
                "output": output
            })
        else:
            raise ValueError(f"Unknown function: {func_name}")
    
    print("Submitting output back to the Assistant...")
    client.beta.threads.runs.submit_tool_outputs(
        thread_id=thread_.id,
        run_id=run_.id,
        tool_outputs=tool_outputs
    )