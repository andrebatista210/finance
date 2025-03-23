from flask import Flask, render_template, request, redirect
from models import db, Cartao, TipoGasto, Gasto
from datetime import datetime
from dateutil.relativedelta import relativedelta
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

with app.app_context():
    db.create_all()

@app.route('/')
def index():
    gastos = Gasto.query.order_by(Gasto.data.desc()).all()
    return render_template('index.html', gastos=gastos)

@app.route('/cadastrar-cartao', methods=['GET', 'POST'])
def cadastrar_cartao():
    if request.method == 'POST':
        nome = request.form['nome']
        bandeira = request.form['bandeira']
        limite = float(request.form['limite'])
        cartao = Cartao(nome=nome, bandeira=bandeira, limite=limite)
        db.session.add(cartao)
        db.session.commit()
        return redirect('/')
    return render_template('cadastrar_cartao.html')

@app.route('/cadastrar-tipo', methods=['GET', 'POST'])
def cadastrar_tipo():
    if request.method == 'POST':
        nome = request.form['nome']
        tipo = TipoGasto(nome=nome)
        db.session.add(tipo)
        db.session.commit()
        return redirect('/')
    return render_template('cadastrar_tipo.html')

@app.route('/novo-gasto', methods=['GET', 'POST'])
@app.route('/novo-gasto', methods=['GET', 'POST'])
def novo_gasto():
    cartoes = Cartao.query.all()
    tipos = TipoGasto.query.all()

    if request.method == 'POST':
        tipo_id = int(request.form['tipo'])
        valor = float(request.form['valor'])
        categoria = request.form['categoria']
        data = datetime.strptime(request.form['data'], '%Y-%m-%d')
        parcelas = int(request.form.get('parcelas', 1))

        # Captura o cartao_id apenas se categoria for 'Cartao'
        cartao_id = None
        if categoria == 'Cartao':
            cartao_id = int(request.form['cartao'])

        valor_parcela = valor / parcelas
        for i in range(parcelas):
            data_parcela = data + relativedelta(months=i)
            gasto = Gasto(
                tipo_id=tipo_id,
                valor=valor_parcela,
                categoria=categoria,
                cartao_id=cartao_id,
                data=data_parcela,
                parcela=i + 1,
                total_parcelas=parcelas
            )
            db.session.add(gasto)
        db.session.commit()
        return redirect('/')
    
    return render_template('novo_gasto.html', cartoes=cartoes, tipos=tipos)

if __name__ == '__main__':
    app.run(debug=True)
