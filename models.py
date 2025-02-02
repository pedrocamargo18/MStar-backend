from extensions import db
from datetime import datetime
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    telefone = db.Column(db.String(15), nullable=True)

    def __repr__(self):
        return f'<User {self.name}>'

class Mercadoria(db.Model):
    __tablename__ = 'mercadorias'
    nome = db.Column(db.String(100), primary_key=True)
    nro_registro = db.Column(db.String(50), nullable=False)
    fabricante = db.Column(db.String(100), nullable=False)
    tipo = db.Column(db.String(50), nullable=False)
    descricao = db.Column(db.String(255), nullable=True)

    entradas = db.relationship('Entrada', backref='mercadoria', lazy=True)

    def __repr__(self):
        return f'<Mercadoria {self.nome}>'

class Entrada(db.Model):
    __tablename__ = 'entradas'
    id = db.Column(db.Integer, primary_key=True)
    quantidade = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime,default=datetime.utcnow)
    local = db.Column(db.String(100), nullable=False)
    mercadoria_nome = db.Column(db.String(100), db.ForeignKey('mercadorias.nome'), nullable=False)

    def __repr__(self):
        return f'<Entrada {self.id}>'

class Saida(db.Model):
    __tablename__ = 'saidas'
    id = db.Column(db.Integer, primary_key=True)
    quantidade = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    local = db.Column(db.String(100), nullable=False)
    mercadoria_nome = db.Column(db.String(100), db.ForeignKey('mercadorias.nome'), nullable=False)

    def __repr__(self):
        return f'<Saida {self.id}>'
