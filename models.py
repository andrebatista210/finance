from flask_sqlalchemy import SQLAlchemy
from datetime import date

db = SQLAlchemy()

class Cartao(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(50))
    bandeira = db.Column(db.String(20))
    limite = db.Column(db.Float)

class TipoGasto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(50))

class Gasto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tipo_id = db.Column(db.Integer, db.ForeignKey('tipo_gasto.id'))
    valor = db.Column(db.Float)
    categoria = db.Column(db.String(20))  # 'Dinheiro' ou 'Cartao'
    cartao_id = db.Column(db.Integer, db.ForeignKey('cartao.id'), nullable=True)
    data = db.Column(db.Date, default=date.today)
    parcela = db.Column(db.Integer, default=1)
    total_parcelas = db.Column(db.Integer, default=1)

    tipo = db.relationship('TipoGasto')
    cartao = db.relationship('Cartao')
