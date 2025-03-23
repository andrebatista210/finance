from flask import Flask, render_template, request, redirect
from models import db, Cartao, TipoGasto, Gasto
from datetime import datetime
from dateutil.relativedelta import relativedelta
from sqlalchemy import extract, func

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

with app.app_context():
    db.create_all()

# Página inicial com análise de gastos
@app.route('/', methods=['GET', 'POST'])
def analise():
    cartoes = Cartao.query.all()
    tipos = TipoGasto.query.all()
    filtro_categoria = request.form.get('categoria', 'Todos')
    filtro_cartao_id = request.form.get('cartao_id', '')

    query = Gasto.query
    if filtro_categoria == 'Dinheiro':
        query = query.filter(Gasto.categoria == 'Dinheiro')
    elif filtro_categoria == 'Cartao':
        query = query.filter(Gasto.categoria == 'Cartao')
        if filtro_cartao_id:
            query = query.filter(Gasto.cartao_id == int(filtro_cartao_id))

    gastos_filtrados = query.all()
    total_gastos = sum(g.valor for g in gastos_filtrados)

    # Agrupamento por mês (usando data_fatura!)
    gastos_por_mes_query = db.session.query(
        extract('year', Gasto.data_fatura).label('ano'),
        extract('month', Gasto.data_fatura).label('mes'),
        func.sum(Gasto.valor).label('total')
    ).filter(Gasto.id.in_([g.id for g in gastos_filtrados])
    ).group_by('ano', 'mes').all()

    gastos_por_mes = [
        {'ano': int(row.ano), 'mes': int(row.mes), 'total': float(row.total)}
        for row in gastos_por_mes_query
    ]

    # Agrupamento por tipo
    gastos_por_tipo_query = db.session.query(
        TipoGasto.nome,
        func.sum(Gasto.valor)
    ).join(TipoGasto).filter(Gasto.id.in_([g.id for g in gastos_filtrados])
    ).group_by(TipoGasto.nome).all()

    gastos_por_tipo = [
        {'tipo': row[0], 'total': float(row[1])}
        for row in gastos_por_tipo_query
    ]

    return render_template('analise.html',
                           gastos=gastos_filtrados,
                           cartoes=cartoes,
                           tipos=tipos,
                           filtro_categoria=filtro_categoria,
                           filtro_cartao_id=filtro_cartao_id,
                           gastos_por_mes=gastos_por_mes,
                           gastos_por_tipo=gastos_por_tipo,
                           total_gastos=total_gastos)

# Lista geral dos gastos
@app.route('/gastos')
def gastos():
    gastos = Gasto.query.order_by(Gasto.data.desc()).all()
    return render_template('gastos.html', gastos=gastos)

# Novo gasto
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
        descricao = request.form.get('descricao')
        cartao_id = int(request.form['cartao']) if categoria == 'Cartao' else None
        fatura_mes_anterior = request.form.get('fatura_proxima') == 'on'

        valor_parcela = valor / parcelas

        for i in range(parcelas):
            data_parcela = data + relativedelta(months=i)
            data_fatura = data_parcela - relativedelta(months=1) if fatura_mes_anterior else data_parcela

            gasto = Gasto(
                tipo_id=tipo_id,
                valor=valor_parcela,
                categoria=categoria,
                cartao_id=cartao_id,
                data=data_parcela,           # data real da compra
                data_fatura=data_fatura,     # usada na análise mensal
                parcela=i + 1,
                total_parcelas=parcelas,
                descricao=descricao
            )
            db.session.add(gasto)
        db.session.commit()
        return redirect('/')
    
    return render_template('novo_gasto.html', cartoes=cartoes, tipos=tipos)

# Detalhamento por mês
@app.route('/detalhes')
def detalhes_mes():
    ano = int(request.args.get('ano'))
    mes = int(request.args.get('mes'))
    gastos = Gasto.query.filter(
        extract('year', Gasto.data_fatura) == ano,
        extract('month', Gasto.data_fatura) == mes
    ).order_by(Gasto.data.asc()).all()
    return render_template('detalhes_mes.html', gastos=gastos, ano=ano, mes=mes)

# Editar gasto
@app.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar_gasto(id):
    gasto = Gasto.query.get_or_404(id)
    cartoes = Cartao.query.all()
    tipos = TipoGasto.query.all()

    if request.method == 'POST':
        gasto.tipo_id = int(request.form['tipo'])
        gasto.valor = float(request.form['valor'])
        gasto.categoria = request.form['categoria']
        gasto.data = datetime.strptime(request.form['data'], '%Y-%m-%d')
        gasto.parcela = int(request.form.get('parcela', 1))
        gasto.total_parcelas = int(request.form.get('total_parcelas', 1))
        gasto.descricao = request.form.get('descricao')
        gasto.cartao_id = int(request.form['cartao']) if gasto.categoria == 'Cartao' else None
        gasto.data_fatura = gasto.data  # ajuste manual se quiser permitir isso depois

        db.session.commit()
        return redirect('/gastos')

    return render_template('editar_gasto.html', gasto=gasto, cartoes=cartoes, tipos=tipos)

# Deletar gasto
@app.route('/deletar/<int:id>', methods=['POST'])
def deletar_gasto(id):
    gasto = Gasto.query.get_or_404(id)
    db.session.delete(gasto)
    db.session.commit()
    return redirect('/gastos')

# Cadastrar cartão
@app.route('/cadastrar-cartao', methods=['GET', 'POST'])
def cadastrar_cartao():
    if request.method == 'POST':
        nome = request.form['nome']
        bandeira = request.form['bandeira']
        limite = float(request.form['limite'])
        db.session.add(Cartao(nome=nome, bandeira=bandeira, limite=limite))
        db.session.commit()
        return redirect('/cadastrar-cartao')
    
    cartoes = Cartao.query.order_by(Cartao.nome).all()
    return render_template('cadastrar_cartao.html', cartoes=cartoes)

# Cadastrar tipo de gasto
@app.route('/cadastrar-tipo', methods=['GET', 'POST'])
def cadastrar_tipo():
    if request.method == 'POST':
        nome = request.form['nome']
        db.session.add(TipoGasto(nome=nome))
        db.session.commit()
        return redirect('/cadastrar-tipo')

    tipos = TipoGasto.query.order_by(TipoGasto.nome).all()
    return render_template('cadastrar_tipo.html', tipos=tipos)

# Rodar app
if __name__ == '__main__':
    app.run(debug=True)
