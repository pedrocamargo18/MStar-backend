from flask import Flask, jsonify, send_file, request
from extensions import db
from flask_migrate import Migrate
from flask_cors import CORS
from models import Mercadoria
from models import Entrada
from models import Saida
from models import User
import pandas as pd
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from datetime import datetime
from flask_jwt_extended import create_access_token, JWTManager,jwt_required, get_jwt_identity
from flask_bcrypt import Bcrypt
from sqlalchemy import extract

app = Flask(__name__)
CORS(app)
bcrypt = Bcrypt(app)

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql+psycopg://postgres:postgres123@localhost:5432/mstar_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'EzjgaevBa40GQX2aDP1o3t'

jwt = JWTManager(app)
db.init_app(app)
migrate = Migrate(app, db)

#rotas
@app.route('/endpoint', methods=['GET'])
def get_data():
    return {'message': 'Dados do backend'}


@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()

    if not data or 'email' not in data or 'password' not in data:
        return jsonify({'error': 'Email e senha são obrigatórios'}), 400

    email = data['email']
    senha = data['password']

    usuario = User.query.filter_by(email=email).first()

    if usuario:
        if bcrypt.check_password_hash(usuario.password, senha):
            access_token = create_access_token(identity={'id': usuario.id, 'email': usuario.email,"role":"admin" })
            return jsonify({
                'message': 'Login realizado com sucesso!',
                'token': access_token
            }), 200
        else:
            return jsonify({'error': 'Credenciais inválidas'}), 401
    else:
        return jsonify({'error': 'Credenciais inválidas'}), 401

@app.route('/mercadorias', methods=['GET'])
def get_mercadorias():
    mercadorias = Mercadoria.query.all()
    result = []
    for mercadoria in mercadorias:
        result.append({
            'nome': mercadoria.nome,
            'nro_registro': mercadoria.nro_registro,
            'fabricante': mercadoria.fabricante,
            'tipo': mercadoria.tipo,
            'descricao': mercadoria.descricao,
        })
    return jsonify(result)

@app.route('/exportar-mercadorias', methods=['GET'])
def exportar_mercadorias():
    mercadorias = Mercadoria.query.all()
    data = [
        {
            'nome': m.nome,
            'nro_registro': m.nro_registro,
            'fabricante': m.fabricante,
            'tipo': m.tipo,
            'descricao': m.descricao
        } for m in mercadorias
    ]

    df = pd.DataFrame(data)
    excel_file = BytesIO()
    with pd.ExcelWriter(excel_file, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name="Mercadorias")

    excel_file.seek(0)
    return send_file(
        excel_file,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name="mercadorias.xlsx"
    )


@app.route('/exportar-mercadorias-pdf', methods=['GET'])
def exportar_mercadorias_pdf():
    mercadorias = Mercadoria.query.all()
    pdf_file = BytesIO()

    c = canvas.Canvas(pdf_file, pagesize=A4)
    largura, altura = A4

    c.setFont("Helvetica-Bold", 16)
    c.drawString(200, altura - 50, "Relatório de Mercadorias")

    c.setFont("Helvetica-Bold", 12)
    headers = ["Nome", "Registro", "Fabricante", "Tipo", "Descrição"]
    x_start = 50
    y_start = altura - 100
    col_widths = [100, 100, 100, 100, 150]

    for i, header in enumerate(headers):
        c.drawString(x_start + sum(col_widths[:i]), y_start, header)

    c.setFont("Helvetica", 10)
    y = y_start - 20
    for mercadoria in mercadorias:
        linha = [
            mercadoria.nome, mercadoria.nro_registro,
            mercadoria.fabricante, mercadoria.tipo, mercadoria.descricao
        ]
        for i, item in enumerate(linha):
            c.drawString(x_start + sum(col_widths[:i]), y, str(item))
        y -= 20

        if y < 50:
            c.showPage()
            y = altura - 100

    c.save()
    pdf_file.seek(0)
    return send_file(
        pdf_file,
        mimetype='application/pdf',
        as_attachment=True,
        download_name="mercadorias.pdf"
    )

@app.route('/add-mercadorias', methods=['POST'])
def add_mercadoria():
    data = request.get_json()
    try:
        if not all(key in data for key in ['nome', 'nro_registro', 'fabricante', 'tipo', 'descricao']):
            return jsonify({'error': 'Dados incompletos'}), 400

        mercadoria_existente = Mercadoria.query.filter_by(nro_registro=data['nro_registro']).first()
        if mercadoria_existente:
            return jsonify({'error': 'Já existe uma mercadoria com este número de registro'}), 400

        nova_mercadoria = Mercadoria(
            nome=data['nome'],
            nro_registro=data['nro_registro'],
            fabricante=data['fabricante'],
            tipo=data['tipo'],
            descricao=data['descricao']
        )

        db.session.add(nova_mercadoria)
        db.session.commit()

        return jsonify({
            'nome': nova_mercadoria.nome,
            'nro_registro': nova_mercadoria.nro_registro,
            'fabricante': nova_mercadoria.fabricante,
            'tipo': nova_mercadoria.tipo,
            'descricao': nova_mercadoria.descricao,
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/tipos-mercadorias', methods=['GET'])
def get_tipos_mercadorias():
    tipos = db.session.query(Mercadoria.tipo).distinct().all()
    tipos_list = [tipo[0] for tipo in tipos]
    return jsonify(tipos_list)

##entrada
@app.route('/entradas', methods=['GET'])
def get_entradas():
    entradas = Entrada.query.all()
    result = []
    for entrada in entradas:
        result.append({
            'id': entrada.id,
            'mercadoria_nome': entrada.mercadoria_nome,
            'quantidade': entrada.quantidade,
            'local': entrada.local,
            'created_at': entrada.created_at.isoformat()
        })
    return jsonify(result)

@app.route('/add-entrada', methods=['POST'])
def add_entrada():
    data = request.get_json()
    try:
        if not all(key in data for key in ['mercadoriaId', 'quantidade', 'local']):
            return jsonify({'error': 'Dados incompletos'}), 400

        nova_entrada = Entrada(
            mercadoria_nome=data['mercadoriaId'],
            quantidade=data['quantidade'],
            local=data['local'],
            created_at=datetime.utcnow()
        )

        db.session.add(nova_entrada)
        db.session.commit()

        return jsonify({
            'mercadoria_nome': nova_entrada.mercadoria_nome,
            'quantidade': nova_entrada.quantidade,
            'local': nova_entrada.local,
            'created_at': nova_entrada.created_at.isoformat()
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/exportar-entradas-pdf', methods=['GET'])
def exportar_entradas_pdf():
    entradas = Entrada.query.all()
    pdf_file = BytesIO()

    c = canvas.Canvas(pdf_file, pagesize=A4)
    largura, altura = A4

    c.setFont("Helvetica-Bold", 16)
    c.drawString(200, altura - 50, "Relatório de Entradas")

    c.setFont("Helvetica-Bold", 12)
    headers = ["Criado em", "ID", "Quantidade", "Mercadoria", "Local"]
    x_start = 50
    y_start = altura - 100
    col_widths = [100, 100, 100, 100, 150]

    for i, header in enumerate(headers):
        c.drawString(x_start + sum(col_widths[:i]), y_start, header)

    c.setFont("Helvetica", 10)
    y = y_start - 20

    for entrada in entradas:
        linha = [
            entrada.created_at.strftime('%d/%m/%Y %H:%M'), entrada.id,
            entrada.quantidade, entrada.mercadoria_nome, entrada.local
        ]

        for i, item in enumerate(linha):
            c.drawString(x_start + sum(col_widths[:i]), y, str(item))

        y -= 20

        if y < 50:
            c.showPage()
            y = altura - 100
            for i, header in enumerate(headers):
                c.drawString(x_start + sum(col_widths[:i]), y_start, header)
            y = y_start - 20

    c.save()
    pdf_file.seek(0)
    return send_file(
        pdf_file,
        mimetype='application/pdf',
        as_attachment=True,
        download_name="entradas.pdf"
    )


##saida
@app.route('/saidas', methods=['GET'])
def get_saidas():
    saidas = Saida.query.all()
    result = []
    for saida in saidas:
        result.append({
            'id': saida.id,
            'mercadoria_nome': saida.mercadoria_nome,
            'quantidade': saida.quantidade,
            'local': saida.local,
            'created_at': saida.created_at.isoformat()
        })
    return jsonify(result)

@app.route('/add-saida', methods=['POST'])
def add_saida():
    data = request.get_json()
    try:
        if not all(key in data for key in ['mercadoriaId', 'quantidade', 'local']):
            return jsonify({'error': 'Dados incompletos'}), 400

        nova_saida = Saida(
            mercadoria_nome=data['mercadoriaId'],
            quantidade=data['quantidade'],
            local=data['local'],
            created_at=datetime.utcnow()
        )
        db.session.add(nova_saida)
        db.session.commit()

        return jsonify({
            'mercadoria_nome': nova_saida.mercadoria_nome,
            'quantidade': nova_saida.quantidade,
            'local': nova_saida.local,
            'created_at': nova_saida.created_at.isoformat()
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/exportar-saidas-pdf', methods=['GET'])
def exportar_saidas_pdf():
    saidas = Entrada.query.all()
    pdf_file = BytesIO()

    c = canvas.Canvas(pdf_file, pagesize=A4)
    largura, altura = A4

    c.setFont("Helvetica-Bold", 16)
    c.drawString(200, altura - 50, "Relatório de Saidas")

    c.setFont("Helvetica-Bold", 12)
    headers = ["Data de Saída", "Quantidade", "Mercadoria", "Local"]
    x_start = 50
    y_start = altura - 100
    col_widths = [100, 100, 100, 100, 150]

    for i, header in enumerate(headers):
        c.drawString(x_start + sum(col_widths[:i]), y_start, header)

    c.setFont("Helvetica", 10)
    y = y_start - 20

    for saida in saidas:
        linha = [
            saida.created_at.strftime('%d/%m/%Y %H:%M'),
            saida.quantidade, saida.mercadoria_nome, saida.local
        ]

        for i, item in enumerate(linha):
            c.drawString(x_start + sum(col_widths[:i]), y, str(item))

        y -= 20

        if y < 50:
            c.showPage()
            y = altura - 100
            for i, header in enumerate(headers):
                c.drawString(x_start + sum(col_widths[:i]), y_start, header)
            y = y_start - 20

    c.save()
    pdf_file.seek(0)
    return send_file(
        pdf_file,
        mimetype='application/pdf',
        as_attachment=True,
        download_name="saidas.pdf"
    )

##Charts retorno de entrada e de saida p/ mes
@app.route('/entradas-por-mes', methods=['GET'])
def entradas_por_mes():
    entradas = db.session.query(
        extract('month', Entrada.created_at).label('mes'),
        db.func.sum(Entrada.quantidade).label('quantidade')
    ).group_by(extract('month', Entrada.created_at)).all()

    entradas_data = [{"mes": str(int(entrada.mes)), "quantidade": entrada.quantidade} for entrada in entradas]

    return jsonify(entradas_data)

@app.route('/saidas-por-mes', methods=['GET'])
def saidas_por_mes():
    saidas = db.session.query(
        extract('month', Saida.created_at).label('mes'),
        db.func.sum(Saida.quantidade).label('quantidade')
    ).group_by(extract('month', Saida.created_at)).all()

    saidas_data = [{"mes": str(int(saida.mes)), "quantidade": saida.quantidade} for saida in saidas]

    return jsonify(saidas_data)


if __name__ == '__main__':
    app.run(debug=True)
