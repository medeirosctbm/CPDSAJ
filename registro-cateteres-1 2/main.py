import firebase_admin
from firebase_admin import credentials, firestore
from flask import Flask, request, jsonify, render_template

# Inicializar Firebase
cred = credentials.Certificate("registro-de-cpds-firebase-adminsdk-fbsvc-172c29d07f.json")  # Nome do arquivo JSON do Firebase
firebase_admin.initialize_app(cred)
db = firestore.client()

app = Flask(__name__)

# Página inicial com formulário
@app.route("/")
def home():
    return render_template("index.html")

# Rota para registrar um novo cateter
@app.route("/registrar", methods=["POST"])
def registrar_cateter():
    dados = request.json
    db.collection("cateteres").add(dados)
    return jsonify({"mensagem": "Cateter registrado com sucesso!"})

# Rota para listar cateteres
@app.route("/listar", methods=["GET"])
def listar_cateteres():
    if request.headers.get('Accept') == 'application/json':
        # Para requisições de API
        cateteres_data = []
        for doc in db.collection("cateteres").stream():
            cateter = doc.to_dict()
            cateter['id'] = doc.id  # Adiciona o ID do documento
            cateteres_data.append(cateter)
        return jsonify(cateteres_data)
    else:
        # Para requisições de navegador
        return render_template("listar.html")

@app.route("/visualizar")
def visualizar_cateteres():
    return render_template("listar.html")

# Rota para visualizar cateteres retirados
@app.route("/visualizar/retirados")
def visualizar_retirados():
    return render_template("retirados.html")

# Rota para listar cateteres retirados (API)
@app.route("/retirados", methods=["GET"])
def listar_retirados():
    cateteres_data = []
    for doc in db.collection("cateteres").where("retirado", "==", True).stream():
        cateter = doc.to_dict()
        cateter['id'] = doc.id  # Adiciona o ID do documento
        cateteres_data.append(cateter)
    return jsonify(cateteres_data)

# Rota para filtrar cateteres por hospital
@app.route("/filtrar/<hospital>")
def filtrar_por_hospital(hospital):
    return render_template("listar.html")

# Rota para listar cateteres filtrados por hospital
@app.route("/listar/hospital/<hospital>", methods=["GET"])
def listar_por_hospital(hospital):
    cateteres_data = []
    query = db.collection("cateteres").where("hospital", "==", hospital)
    
    for doc in query.stream():
        cateter = doc.to_dict()
        cateter['id'] = doc.id
        cateteres_data.append(cateter)
    
    return jsonify(cateteres_data)

# Rota para registrar um repique
@app.route("/repique/<id>", methods=["POST"])
def registrar_repique(id):
    try:
        dados = request.json
        # Obter o documento atual
        doc_ref = db.collection("cateteres").document(id)
        doc = doc_ref.get()
        
        if doc.exists:
            # Verificar se já existe o campo repiques
            cateter = doc.to_dict()
            if 'repiques' not in cateter:
                cateter['repiques'] = []
            
            # Garantir que todos os campos necessários existam
            repique_data = {
                'data': dados.get('data'),
                'eva': dados.get('eva'),
                'dose': dados.get('dose'),
                'observacoes': dados.get('observacoes', ''),
                'dataRegistro': dados.get('dataRegistro')
            }
            
            # Adicionar o novo repique à lista
            cateter['repiques'].append(repique_data)
            
            # Atualizar o documento
            doc_ref.update({'repiques': cateter['repiques']})
            
            return jsonify({"mensagem": "Repique registrado com sucesso!"})
        else:
            return jsonify({"mensagem": "Cateter não encontrado!"}), 404
    except Exception as e:
        print(f"Erro ao registrar repique: {str(e)}")
        return jsonify({"mensagem": f"Erro ao registrar repique: {str(e)}"}), 500

# Rota para atualizar um repique
@app.route("/atualizar/<id>", methods=["PUT"])
def atualizar_repique(id):
    dados = request.json
    db.collection("cateteres").document(id).update(dados)
    return jsonify({"mensagem": "Repique atualizado!"})

# Rota para registrar retirada
@app.route("/retirar/<id>", methods=["POST"])
def retirar_cateter(id):
    dados = request.json
    
    # Obter o documento atual
    doc_ref = db.collection("cateteres").document(id)
    doc = doc_ref.get()
    
    if doc.exists:
        # Atualizar o documento com dados de retirada
        cateter = doc.to_dict()
        cateter['retirado'] = True
        cateter['dataRetirada'] = dados.get('dataRetirada')
        cateter['observacoesRetirada'] = dados.get('observacoesRetirada')
        
        # Salvar em cateteres retirados e atualizar o documento original
        doc_ref.update(cateter)
        
        return jsonify({"mensagem": "Cateter retirado com sucesso!"})
    else:
        return jsonify({"mensagem": "Cateter não encontrado!"}), 404

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)