
import os
import flask
import bcrypt
import database
import flask_login
from datetime import datetime, timedelta
from flask import request, jsonify, redirect, url_for, send_file,render_template, abort,  Response, flash
from functools import wraps
from dateutil.relativedelta import *
from decimal import Decimal
from flask_login import login_required, current_user
import pandas as pd
import csv
import json
import io
import csv

######################################################## INIT ########################################################
class User(flask_login.UserMixin):
    pass

#Flask configuration
versao=''
app = flask.Flask(__name__)
app.secret_key = 'key'

#Flask-Login configuration
login_manager = flask_login.LoginManager()
login_manager.init_app(app)

#Database configuration
databaseOBJ=database.postgresDatabase(host='localhost')

################################################## AUTHENTICATION ####################################################

#Create class that extends default flask_login User Class
class User(flask_login.UserMixin):
    def __init__(self):
        super(User, self).__init__()
        self.name = ''
        self.privileges = 1

@login_manager.user_loader
def load_user(userid):

    try:
        userid = int(userid)
    except:
        return None

    credentials = databaseOBJ.readRaw(
        """
        SELECT id, usuario, privilegio, setor
        FROM usuarios
        WHERE id = %s
        """,
        params=(userid,),
        realdict=True
    )

    if credentials:

        user = User()
        user.id = credentials[0]['id']
        user.usuario = credentials[0]['usuario']
        user.privileges = credentials[0]['privilegio']
        user.setor = credentials[0]['setor']

        return user

#Callback to manage unauthorized acess
@login_manager.unauthorized_handler
def unauth_handler():
    #Redirect to index when user try to access protected resources without an authentication
    return flask.redirect(flask.url_for('autenticacao'))

@app.route('/login', methods=['POST'])
def login():

    user = flask.request.form.get('user')
    password = flask.request.form.get('password')

    if not user or not password:
        return flask.abort(400)

    credentials = databaseOBJ.readRaw(
        """
        SELECT id, usuario, privilegio, senha, setor
        FROM usuarios
        WHERE usuario = %s
        """,
        params=(user,),
        realdict=False
    )

    if credentials:

        senha_hash = credentials[0][3]

        if bcrypt.checkpw(password.encode(), senha_hash.encode()):

            usuario_logado = User()
            usuario_logado.id = credentials[0][0]
            usuario_logado.usuario = credentials[0][1]
            usuario_logado.privileges = credentials[0][2]
            usuario_logado.setor = credentials[0][4]

            flask_login.login_user(usuario_logado)

            return flask.make_response({'Login': True})

    return flask.make_response({'Login': False})

@app.route('/logout', methods=['GET'])
def logout():
    #Logout current user
    flask_login.logout_user()
    return flask.make_response({'Logout': True})

def privilege_required(level):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):

            if not current_user.is_authenticated:
                return redirect(url_for('login'))

            if current_user.privileges < level:
                flash("Você não tem permissão para acessar esta página.")
                return redirect(url_for('monitoramento_OP'))

            return f(*args, **kwargs)

        return decorated_function
    return decorator
######################################################## CRUD RESOURCES ####################################################

@app.route('/usuarios', methods=['GET', 'DELETE', 'PUT', 'POST'])
@flask_login.login_required
@privilege_required(3)
def usuarios():

    form = flask.request.form

    # ==========================
    # GET - LISTAR USUÁRIOS
    # ==========================
    if flask.request.method == 'GET':

        users = databaseOBJ.readRaw(
            """
            SELECT 
                usuarios.id,
                usuarios.usuario,
                usuarios.setor,
                usuarios.privilegio
            FROM usuarios
            ORDER BY usuarios.id DESC;
            """,
            realdict=True
        )

        return flask.jsonify({'users': users})

    # ==========================
    # DELETE - EXCLUIR USUÁRIO
    # ==========================
    elif flask.request.method == 'DELETE':

        userid = flask.request.form.get('id')

        if not userid:
            flask.abort(400)

        # trava para impedir auto exclusão
        if int(userid) == current_user.id:
            return jsonify({"deleted": False, "error": "auto_delete"})

        databaseOBJ.writeRaw(
            "DELETE FROM usuarios WHERE id = %s;",
            params=(userid,)
        )

        return jsonify({"deleted": True})

    # ==========================
    # PUT - ATUALIZAR USUÁRIO
    # ==========================
    elif flask.request.method == 'PUT':

        userid = form.get('id')
        userlogin = form.get('usuario')
        usersector = form.get('setor')
        userprivileges = form.get('privilegios')
        novaSenha = form.get('novaSenha')

        if not (userid and userlogin and userprivileges):
            return flask.jsonify({
                "success": False,
                "error": "Dados obrigatórios não informados."
            })

        userprivileges = int(userprivileges)

        if userprivileges == 1 and not usersector:
            return flask.jsonify({
                "success": False,
                "error": "Selecione um setor para o usuário."
            })

        if userprivileges != 1:
            usersector = None


        # 🔎 verifica se já existe outro usuário com o mesmo login
        existe = databaseOBJ.readRaw("""
            SELECT 1
            FROM usuarios
            WHERE usuario = %s
            AND id <> %s
        """, (userlogin, userid), realdict=True)

        if existe:
            return flask.jsonify({
                "success": False,
                "error": "Já existe um usuário com este login."
            })


        try:

            # Se veio nova senha
            if novaSenha and novaSenha.strip() != '':

                # valida tamanho da senha
                if len(novaSenha) < 6:
                    return flask.jsonify({
                        'success': False,
                        'error': 'Senha deve ter pelo menos 6 caracteres'
                    })

                senha_hash = bcrypt.hashpw(
                    novaSenha.encode(),
                    bcrypt.gensalt()
                ).decode()

                databaseOBJ.writeRaw(
                    """
                    UPDATE usuarios
                    SET usuario = %s,
                        setor = %s,
                        privilegio = %s,
                        senha = %s
                    WHERE id = %s
                    """,
                    params=(userlogin, usersector, userprivileges, senha_hash, userid)
                )

            else:

                databaseOBJ.writeRaw(
                    """
                    UPDATE usuarios
                    SET usuario = %s,
                        setor = %s,
                        privilegio = %s
                    WHERE id = %s
                    """,
                    params=(userlogin, usersector, userprivileges, userid)
                )

            return flask.jsonify({
                "success": True
            })

        except Exception as e:

            print("Erro ao atualizar usuário:", e)

            return flask.jsonify({
                "success": False,
                "error": "Erro ao atualizar usuário."
            })

    # ==========================
    # POST - CRIAR USUÁRIO
    # ==========================
    elif flask.request.method == 'POST':

        userlogin = form.get('usuario')
        usersector = form.get('setor')
        userprivileges = form.get('privilegios')

        if not (userlogin and usersector and userprivileges):
            flask.abort(400)

        if userprivileges == '1' and not usersector:
            flask.abort(400)
        
        if userprivileges != '1':
            usersector = None

        senha_hash = bcrypt.hashpw(
            userlogin.lower().encode(),
            bcrypt.gensalt()
        ).decode()

        databaseOBJ.writeRaw(
            """
            INSERT INTO usuarios (usuario, setor, senha, privilegio)
            VALUES (%s, %s, %s, %s)
            """,
            params=(userlogin, usersector, senha_hash, userprivileges)
        )

        return flask.make_response({'created': 1})

    else:
        flask.abort(405)

@app.context_processor
def inject_now():
    return {'now': datetime.now()}

@app.route('/buscar_ordens_finalizar')
@flask_login.login_required
def buscar_ordens_finalizar():

    privilegio = flask_login.current_user.privileges
    setor_usuario = flask_login.current_user.setor

    MAPA_PROCESSOS = {
        "materia_prima": 1,
        "estamparia": 2,
        "solda": 3,
        "retifica": 4,
        "envio_terceiros": 5,
        "recebimento_terceiros": 6,
        "inspecao_final": 7,
        "expedicao": 8
    }

    sql = """
        SELECT o.numero_op
        FROM ordem_de_producao o
        WHERE o.status_id = 2
    """

    params = []

    # operador só vê o setor dele
    if privilegio == 1:

        id_processo = MAPA_PROCESSOS.get(setor_usuario.lower().strip())

        if not id_processo:
            return flask.jsonify([])

        sql += """
            AND EXISTS (
                SELECT 1
                FROM producao p
                WHERE p.id_ordem_de_producao = o.id
                AND p.id_processo = %s
            )
        """

        params.append(id_processo)

    sql += " ORDER BY o.numero_op DESC "

    ordens = databaseOBJ.readRaw(sql, tuple(params), realdict=True)

    return flask.jsonify(ordens)

@app.route('/buscar_ordens_iniciar')
@flask_login.login_required
def buscar_ordens_iniciar():

    filtro_iniciar = "o.status_id IN (1,2)"

    ordens = databaseOBJ.readRaw(f"""
        SELECT numero_op
        FROM ordem_de_producao o
        WHERE {filtro_iniciar}
        ORDER BY numero_op DESC
    """, realdict=True)

    return flask.jsonify(ordens)

@app.route('/usuariodisponivel', methods=['GET'])
@flask_login.login_required
def usuariodisponivel():
    global databaseOBJ

    args = flask.request.args
    userlogin = str(args.get('usuario', default=''))

    if 'userlogin' != '': 
        query = databaseOBJ.readRaw("select * from usuarios where usuario='" + userlogin + "';")
        if len(query) == 0:
            return flask.make_response({'available': True})
        else:
            return flask.make_response({'available': False})
    else:
        return flask.abort(400)

@app.route('/mudarsenha', methods=['GET','PUT'])
@flask_login.login_required
def mudarsenha():
    global databaseOBJ
    form = flask.request.form
    userid = flask_login.current_user.get_id()
    currentPassword = form['currentPassword']
    newPassword = form['newPassword']

    if flask.request.method == 'GET' or flask.request.method == 'PUT':
        if currentPassword != None and newPassword != None:
            #Check if user typed right password
            password = databaseOBJ.readRaw("select senha from usuarios where id=" + userid + ";")[0][0]
            if bcrypt.checkpw(currentPassword.encode(), password.encode()):
                #Update user password
                newPassword = bcrypt.hashpw(newPassword.encode(), bcrypt.gensalt())
                print("Updating password from userid: " + userid)
                databaseOBJ.writeRaw("update usuarios set (senha) = row('" + newPassword.decode() + "') where id=" + userid + ";")
                return flask.make_response({'changeUserPassword': True})
            else:
                return flask.make_response({'changeUserPassword': False})
        else:
            flask.abort(400)
    else:
        flask.abort(405)

###########################################################################################

@app.route('/adm/produtos')
@flask_login.login_required
@privilege_required(2)
def adm_produtos():
    return render_template('adm_produtos.html')

@app.route('/produtos', methods=['GET', 'POST', 'PUT', 'DELETE'])
def produtos():

    # 🔎 LISTAR
    if flask.request.method == 'GET':

        produtos = databaseOBJ.readRaw("""
            SELECT id, nome, codigo
            FROM produtos
            ORDER BY nome
        """, realdict=True)

        return flask.jsonify({"produtos": produtos})


    # ➕ ADICIONAR
    if flask.request.method == 'POST':

        nome = flask.request.values.get('nome')
        codigo = flask.request.values.get('codigo')

        existe = databaseOBJ.readRaw("""
            SELECT 1
            FROM produtos
            WHERE codigo = %s
            OR LOWER(nome) = LOWER(%s)
        """,(codigo,nome), realdict=True)

        if existe:
            return flask.jsonify({
                "success": False,
                "error": "Já existe um produto com este código ou nome."
            })

        databaseOBJ.writeRaw("""
            INSERT INTO produtos (nome, codigo)
            VALUES (%s, %s)
        """, (nome, codigo))

        return flask.jsonify({"success": True})


    # ✏️ EDITAR
    if flask.request.method == 'PUT':

        id_produto = flask.request.values.get('id')
        nome = flask.request.values.get('nome')
        codigo = flask.request.values.get('codigo')

        existe = databaseOBJ.readRaw("""
            SELECT 1
            FROM produtos
            WHERE (codigo = %s OR LOWER(nome) = LOWER(%s))
            AND id <> %s
        """,(codigo,nome,id_produto), realdict=True)

        if existe:
            return flask.jsonify({
                "success": False,
                "error": "Já existe um produto com este código ou nome."
            })

        databaseOBJ.writeRaw("""
            UPDATE produtos
            SET nome = %s,
                codigo = %s
            WHERE id = %s
        """, (nome, codigo, id_produto))

        return flask.jsonify({"success": True})


    # 🗑 EXCLUIR
    if flask.request.method == 'DELETE':

        id_produto = flask.request.values.get('id')

        databaseOBJ.writeRaw("""
            DELETE FROM produtos
            WHERE id = %s
        """, (id_produto,))

        return flask.jsonify({"success": True})

@app.route('/adicionar_produto', methods=['POST'])
@privilege_required(2)
def adicionar_produto():

    nome = flask.request.form['nome']
    codigo = flask.request.form['codigo']

    existe = databaseOBJ.readRaw("""
        SELECT id FROM produtos WHERE codigo = %s
    """, (codigo,))

    if existe:
        return flask.jsonify({'success': False, 'error': 'Código já cadastrado'})

    sucesso = databaseOBJ.writeRaw("""
        INSERT INTO produtos (nome, codigo)
        VALUES (%s, %s)
    """, (nome, codigo))

    if sucesso:
        return flask.jsonify({'success': True})
    else:
        return flask.jsonify({'success': False, 'error': str(databaseOBJ.lastError)})    

@app.route('/adm/clientes')
@flask_login.login_required
@privilege_required(2)
def adm_clientes():
    return render_template('adm_clientes.html')

@app.route('/clientes', methods=['GET', 'POST', 'PUT', 'DELETE'])
def clientes():

    # LISTAR
    if flask.request.method == 'GET':

        clientes = databaseOBJ.readRaw("""
            SELECT id, nome, codigo
            FROM clientes
            ORDER BY nome
        """, realdict=True)

        return flask.jsonify({"clientes": clientes})


    # ADICIONAR
    if flask.request.method == 'POST':

        nome = flask.request.form['nome']
        codigo = flask.request.form['codigo']

        # 🔎 verifica se já existe
        existe = databaseOBJ.readRaw("""
            SELECT 1
            FROM clientes
            WHERE codigo = %s
        """, (codigo,), realdict=True)

        if existe:
            return flask.jsonify({
                "success": False,
                "error": "Código já cadastrado."
            })

        databaseOBJ.writeRaw("""
            INSERT INTO clientes (nome, codigo)
            VALUES (%s, %s)
        """, (nome, codigo))

        return flask.jsonify({"success": True})


    # EDITAR
    if flask.request.method == 'PUT':

        id = flask.request.form['id']
        nome = flask.request.form['nome']
        codigo = flask.request.form['codigo']

        existe = databaseOBJ.readRaw("""
            SELECT 1
            FROM clientes
            WHERE codigo = %s
            AND id <> %s
        """, (codigo, id), realdict=True)

        if existe:
            return flask.jsonify({
                "success": False,
                "error": "Código já cadastrado."
            })

        databaseOBJ.writeRaw("""
            UPDATE clientes
            SET nome = %s,
                codigo = %s
            WHERE id = %s
        """, (nome, codigo, id))

        return flask.jsonify({"success": True})


    # EXCLUIR
    if flask.request.method == 'DELETE':

        id = flask.request.form['id']

        databaseOBJ.writeRaw("""
            DELETE FROM clientes
            WHERE id = %s
        """, (id,))

        return flask.jsonify({"success": True})

@app.route('/dados_producao/<processo>')
@flask_login.login_required
def dados_producao(processo):

    params = []
    filtro = ""

    # Mapa fixo URL -> ID do processo
    MAPA_PROCESSOS = {
        "materia_prima": 1,
        "estamparia": 2,
        "solda": 3,
        "retifica": 4,
        "envio_terceiros": 5,
        "recebimento_terceiros": 6,
        "inspecao_final": 7,
        "expedicao": 8
    }

    if processo.lower() != "geral":

        id_processo = MAPA_PROCESSOS.get(processo.lower())

        if id_processo:
            filtro = " AND producao.id_processo = %s "
            params.append(id_processo)
        else:
            print("Processo inválido recebido na URL:", processo)

    sql = f"""
        SELECT 
            operador.nome as operador,
            operador.codigo as numero_chapa,
            clientes.nome as cliente,
            processos.nome as processo,
            producao.id_processo as operacao,  
            material.codigo as material,
            ordem_de_producao.numero_qualidade as numero_qualidade,
            tratamentos.nome as tratamento,
            ordem_de_producao.id_tratamento as id_tratamento,
            producao.qtde_produzida as quantidade_produzida,

            CASE 
                WHEN producao.status = 1 THEN 'Em operação'
                WHEN producao.status = 2 THEN 'Finalizado'
                ELSE 'Aguardando'
            END as status,

            ordem_de_producao.numero_op as numero_op,
            ordem_de_producao.quantidade as quantidade_total_ordem,
            produtos.nome as produto,
            produtos.codigo as codigo,

            TO_CHAR(producao.dt_inicio, 'DD/MM/YYYY HH24:MI') as iniciado_em,
            TO_CHAR(producao.dt_fim, 'DD/MM/YYYY HH24:MI') as finalizado_em,
            TO_CHAR(ordem_de_producao.data_entrega, 'DD/MM/YYYY') as data_entrega

        FROM producao

        INNER JOIN processos 
            ON producao.id_processo = processos.id

        LEFT JOIN operador
            ON producao.id_operador = operador.id

        INNER JOIN ordem_de_producao
            ON producao.id_ordem_de_producao = ordem_de_producao.id

        LEFT JOIN tratamentos 
            ON ordem_de_producao.id_tratamento = tratamentos.id

        LEFT JOIN clientes 
            ON ordem_de_producao.id_cliente = clientes.id

        LEFT JOIN material 
            ON ordem_de_producao.id_material = material.id

        LEFT JOIN produtos
            ON ordem_de_producao.id_produto = produtos.id

        WHERE producao.status = 1
        AND ordem_de_producao.status_id <> 4
        {filtro}

        ORDER BY producao.dt_inicio DESC
    """

    print("Processo recebido:", processo)
    print("Params:", params)
    print("SQL gerado:\n", sql)

    valores = databaseOBJ.readRaw(sql, params=tuple(params), realdict=True)

    return flask.jsonify(valores)

@app.route('/dados_ordens', methods=['GET'])
def dados_ordens():

    valores = databaseOBJ.readRaw("""
        SELECT
            op.id,
            op.numero_op,
            op.quantidade AS quantidade_total_ordem,
            TO_CHAR(op.data_entrega, 'DD/MM/YYYY') AS data_entrega,
            TO_CHAR(op.data_entrega, 'YYYY-MM-DD') AS data_entrega_iso,
            op.numero_qualidade,
            op.id_tratamento,
            op.status_id,
            op.id_cliente,
            op.id_material,
            op.data_criacao AS data_criacao_real,
            TO_CHAR(op.data_criacao, 'YYYY-MM-DD HH24:MI:SS') AS data_criacao_iso,
            TO_CHAR(op.data_criacao, 'DD/MM/YYYY HH24:MI') AS data_criacao,
            op.id_produto as id_produto,

            p.nome AS produto,
            p.codigo AS codigo,

            c.nome AS cliente,

            m.codigo AS material,
            m.descricao AS material_descricao,

            s.nome AS status_ordem

        FROM ordem_de_producao op

        INNER JOIN produtos p
            ON op.id_produto = p.id

        INNER JOIN clientes c
            ON op.id_cliente = c.id

        INNER JOIN material m
            ON op.id_material = m.id

        LEFT JOIN status s
            ON op.status_id = s.id

        ORDER BY op.data_criacao DESC
    """, realdict=True)

    return flask.jsonify(valores)

######################################################## VIEWS ########################################################

@app.route('/autenticacao', methods=['GET', 'POST'])
@app.route('/', methods=['GET', 'POST'])
def autenticacao():

    print("AUTH:", flask_login.current_user.is_authenticated)
    print("USER:", flask_login.current_user)
    print("PRIV:", getattr(flask_login.current_user, 'privileges', 'SEM privileges'))
    print("SETOR:", getattr(flask_login.current_user, 'setor', 'SEM setor'))

    if flask_login.current_user.is_authenticated:

        privilegio = flask_login.current_user.privileges

        # Nível 1 → monitoramento do próprio setor
        if privilegio == 1:

            setor = flask_login.current_user.setor

            if setor:
                return flask.redirect(
                    flask.url_for('monitoramento_OP', processo=setor)
                )
            else:
                # Se por algum motivo não tiver setor definido
                return flask.redirect(
                    flask.url_for('monitoramento_OP', processo='geral')
                )

        # Nível 2 (PCP) ou 3 (ADM) → visão geral
        elif privilegio in [2,3]:

            return flask.redirect(
                flask.url_for('monitoramento_OP', processo='geral')
            )

    return flask.render_template('autenticacao.html')

@app.route('/dados_historico')
@flask_login.login_required
def dados_historico():

    privilegio = flask_login.current_user.privileges
    setor_usuario = flask_login.current_user.setor

    data_inicio = flask.request.args.get('data_inicio')
    data_fim = flask.request.args.get('data_fim')

    params = []
    filtros = []

    # filtro por data
    if data_inicio and data_fim:
        filtros.append("producao.dt_fim BETWEEN %s AND %s")
        params.append(data_inicio + " 00:00:00")
        params.append(data_fim + " 23:59:59")

    # 🔐 restrição por setor
    if privilegio == 1 and setor_usuario:

        MAPA_PROCESSOS = {
            "materia_prima": 1,
            "estamparia": 2,
            "solda": 3,
            "retifica": 4,
            "envio_terceiros": 5,
            "recebimento_terceiros": 6,
            "inspecao_final": 7,
            "expedicao": 8
        }

        id_processo = MAPA_PROCESSOS.get(setor_usuario)

        if id_processo:
            filtros.append("producao.id_processo = %s")
            params.append(id_processo)
        else:
            flask.abort(403)

    # monta where dinâmico
    filtro_sql = ""
    if filtros:
        filtro_sql = " AND " + " AND ".join(filtros)

    sql = f"""
        SELECT 
            operador.nome as operador,
            operador.codigo as numero_chapa,
            clientes.nome as cliente,
            processos.nome as processo,
            producao.id_processo as operacao,  
            material.codigo as material,
            ordem_de_producao.numero_qualidade as numero_qualidade,
            tratamentos.nome as tratamento,
            ordem_de_producao.id_tratamento as id_tratamento,
            producao.qtde_produzida as quantidade_produzida,
            operador_fim.nome AS operador_fim,
            operador_fim.codigo AS chapa_fim,

            CASE 
                WHEN producao.status = 1 THEN 'Em operação'
                WHEN producao.status = 2 THEN 'Finalizado'
                ELSE 'Aguardando'
            END as status,

            ordem_de_producao.numero_op as numero_op,
            ordem_de_producao.quantidade as quantidade_total_ordem,
            produtos.nome as produto,
            produtos.codigo as codigo,

            TO_CHAR(producao.dt_inicio, 'DD/MM/YYYY HH24:MI') as iniciado_em,
            TO_CHAR(producao.dt_fim, 'DD/MM/YYYY HH24:MI') as finalizado_em,
            TO_CHAR(ordem_de_producao.data_entrega, 'DD/MM/YYYY') as data_entrega

        FROM producao

        INNER JOIN ordem_de_producao 
            ON producao.id_ordem_de_producao = ordem_de_producao.id

        INNER JOIN produtos 
            ON ordem_de_producao.id_produto = produtos.id

        LEFT JOIN operador
            ON producao.id_operador = operador.id

        INNER JOIN processos 
            ON producao.id_processo = processos.id

        LEFT JOIN tratamentos 
            ON ordem_de_producao.id_tratamento = tratamentos.id

        LEFT JOIN clientes 
            ON ordem_de_producao.id_cliente = clientes.id

        LEFT JOIN material 
            ON ordem_de_producao.id_material = material.id

        LEFT JOIN operador operador_fim
            ON producao.id_operador_fim = operador_fim.id

        WHERE producao.status = 2
        {filtro_sql}

        ORDER BY producao.dt_fim DESC
    """

    valores = databaseOBJ.readRaw(sql, params=tuple(params), realdict=True)

    return flask.jsonify(valores)

@app.route('/exportar_historico_csv')
@flask_login.login_required
def exportar_csv():

    privilegio = flask_login.current_user.privileges
    setor_usuario = flask_login.current_user.setor

    data_inicio = flask.request.args.get('data_inicio')
    data_fim = flask.request.args.get('data_fim')

    params = []
    filtros = []

    if data_inicio and data_fim:
        filtros.append("producao.dt_fim BETWEEN %s AND %s")
        params.append(data_inicio + " 00:00:00")
        params.append(data_fim + " 23:59:59")

    # filtro por setor
    if privilegio == 1 and setor_usuario:

        MAPA_PROCESSOS = {
            "materia_prima": 1,
            "estamparia": 2,
            "solda": 3,
            "retifica": 4,
            "envio_terceiros": 5,
            "recebimento_terceiros": 6,
            "inspecao_final": 7,
            "expedicao": 8
        }

        setor_normalizado = setor_usuario.lower().strip()
        id_processo = MAPA_PROCESSOS.get(setor_normalizado)

        if not id_processo:
            return flask.abort(403)

        filtros.append("producao.id_processo = %s")
        params.append(id_processo)

    filtro_sql = ""
    if filtros:
        filtro_sql = " AND " + " AND ".join(filtros)

    sql = f"""
        SELECT 
            operador.nome as operador,
            operador.codigo as numero_chapa,
            clientes.nome as cliente,
            processos.nome as processo,
            producao.id_processo as operacao,
            material.codigo as material,
            ordem_de_producao.numero_qualidade as numero_qualidade,
            tratamentos.nome as tratamento,
            producao.qtde_produzida as quantidade_produzida,
            operador_fim.nome AS operador_fim,
            operador_fim.codigo AS chapa_fim,

            CASE 
                WHEN producao.status = 1 THEN 'Em operação'
                WHEN producao.status = 2 THEN 'Finalizado'
                ELSE 'Aguardando'
            END as status,

            ordem_de_producao.numero_op as numero_op,
            ordem_de_producao.quantidade as quantidade_total_ordem,
            produtos.nome as produto,
            produtos.codigo as codigo,

            TO_CHAR(producao.dt_inicio, 'DD/MM/YYYY HH24:MI') as iniciado_em,
            TO_CHAR(producao.dt_fim, 'DD/MM/YYYY HH24:MI') as finalizado_em,
            TO_CHAR(ordem_de_producao.data_entrega, 'DD/MM/YYYY') as data_entrega

        FROM producao

        INNER JOIN ordem_de_producao 
            ON producao.id_ordem_de_producao = ordem_de_producao.id

        INNER JOIN produtos 
            ON ordem_de_producao.id_produto = produtos.id

        LEFT JOIN operador
            ON producao.id_operador = operador.id

        INNER JOIN processos 
            ON producao.id_processo = processos.id

        LEFT JOIN tratamentos 
            ON ordem_de_producao.id_tratamento = tratamentos.id

        LEFT JOIN clientes 
            ON ordem_de_producao.id_cliente = clientes.id

        LEFT JOIN material 
            ON ordem_de_producao.id_material = material.id

        LEFT JOIN operador operador_fim
            ON producao.id_operador_fim = operador_fim.id

        WHERE producao.status = 2
        {filtro_sql}

        ORDER BY producao.dt_fim DESC
    """

    dados = databaseOBJ.readRaw(sql, params=tuple(params), realdict=True)

    output = io.StringIO(newline="")
    writer = csv.writer(output, delimiter=';')

    writer.writerow([
        "OP",
        "Denominacao",
        "Peca Numero",
        "Quantidade",
        "Cliente",
        "Entrega",
        "Material",
        "A.Q.",
        "Processo",
        "Status",
        "Chapa",
        "Iniciado",
        "Chapa Fim",
        "Finalizado",
        "Producao"
    ])

    for row in dados:
        writer.writerow([
            row["numero_op"],
            row["produto"],
            row["codigo"],
            row["quantidade_total_ordem"],
            row["cliente"],
            row["data_entrega"],
            row["material"],
            row["numero_qualidade"],
            row["processo"],
            row["status"],
            row["numero_chapa"],
            row["iniciado_em"],
            row["chapa_fim"] or "-",
            row["finalizado_em"],
            row["quantidade_produzida"] or 0
        ])

    output.seek(0)

    return flask.Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=historico_producao.csv"
        }
    )

@app.route('/historico')
@flask_login.login_required
def historico():
    machine_names = databaseOBJ.readRaw(
        "select id, bancada, setor, empresa from maquina order by id asc;"
    )

    return flask.render_template(
        'historico_producao.html',
        machine_names=machine_names
    )

@app.route('/cancelar_ordem', methods=['POST'])
@flask_login.login_required
@privilege_required(2)
def cancelar_ordem():

    id_ordem = flask.request.form.get('id')

    if not id_ordem:
        return flask.jsonify({"success": False, "error": "Ordem inválida"}), 400

    databaseOBJ.writeRaw("""
        UPDATE ordem_de_producao
        SET status_id = 4
        WHERE id = %s
    """, (id_ordem,))

    return flask.jsonify({"success": True})

@app.route('/ordens', methods=['PUT'])
@flask_login.login_required
def atualizar_ordem():

    id = flask.request.form.get('id')
    numero_op = flask.request.form.get('numero_op')
    id_produto = flask.request.form.get('id_produto')
    numero_qualidade = flask.request.form.get('numero_qualidade')
    id_cliente = flask.request.form.get('id_cliente')
    id_material = flask.request.form.get('id_material')
    id_tratamento = flask.request.form.get('id_tratamento')
    quantidade = flask.request.form.get('quantidade')
    data_entrega = flask.request.form.get('data_entrega')
    status_id = flask.request.form.get('status_id')

    # 🔎 1️⃣ Buscar numero_op atual
    ordem_atual = databaseOBJ.readRaw("""
        SELECT numero_op
        FROM ordem_de_producao
        WHERE id = %s
    """, (id,), realdict=True)

    if not ordem_atual:
        return flask.jsonify({
            "success": False,
            "error": "Ordem não encontrada."
        }), 404

    numero_op = str(numero_op)
    numero_op_atual = str(ordem_atual[0]["numero_op"])

    if numero_op != numero_op_atual:

        existe_numero = databaseOBJ.readRaw("""
            SELECT 1
            FROM ordem_de_producao
            WHERE numero_op = %s
            AND id <> %s
            LIMIT 1
        """, (numero_op, id), realdict=True)

        if existe_numero:
            return flask.jsonify({
                "success": False,
                "error": "Já existe uma OP com esse número."
            }), 400

    # 🔥 3️⃣ UPDATE protegido
    try:
        databaseOBJ.writeRaw("""
            UPDATE ordem_de_producao
            SET numero_op = %s,
                id_produto = %s,
                numero_qualidade = %s,
                id_cliente = %s,
                id_material = %s,
                id_tratamento = %s,
                quantidade = %s,
                data_entrega = %s,
                status_id = %s
            WHERE id = %s
        """, (
            numero_op,
            id_produto,
            numero_qualidade,
            id_cliente,
            id_material,
            id_tratamento,
            quantidade,
            data_entrega,
            status_id,
            id
        ))

    except Exception as e:
        print("Erro:", e)
        return flask.jsonify({
            "success": False,
            "error": "Já existe uma OP com esse número."
        }), 400

    return flask.jsonify({"success": True})

@app.route('/produto_info')
def produto_info():

    id_produto = flask.request.args.get('id_produto')

    produto = databaseOBJ.readRaw("""
        SELECT nome
        FROM produtos
        WHERE id = %s
    """, (id_produto,), realdict=True)

    if produto:
        return flask.jsonify({
            "success": True,
            "nome": produto[0]["nome"]
        })

    return flask.jsonify({"success": False})

@app.route('/monitoramento_OP/<processo>')
@flask_login.login_required
def monitoramento_OP(processo):

    MAPA_PROCESSOS = {
        "materia_prima": 1,
        "estamparia": 2,
        "solda": 3,
        "retifica": 4,
        "envio_terceiros": 5,
        "recebimento_terceiros": 6,
        "inspecao_final": 7,
        "expedicao": 8
    }

    # 🔎 Valida processo
    id_processo = MAPA_PROCESSOS.get(processo)

    if processo == "geral":
        id_processo = None
    else:
        id_processo = MAPA_PROCESSOS.get(processo)

        if not id_processo:
            flask.abort(404)

    privilegio = int(flask_login.current_user.privileges)
    setor_usuario = flask_login.current_user.setor

    # 🔐 Usuário nível 1 só acessa o próprio setor
    if privilegio == 1 and processo != setor_usuario:
        flask.abort(403)

    # 🔎 Nome amigável do processo
    nomes = {
        "materia_prima": "Matéria-Prima",
        "estamparia": "Estamparia",
        "solda": "Solda",
        "retifica": "Retífica",
        "envio_terceiros": "Envio para Terceiros",
        "recebimento_terceiros": "Recebimento (Terceiros)",
        "inspecao_final": "Inspeção Final",
        "expedicao": "Expedição",
        "geral": "Geral"
    }

    nome_processo = nomes.get(processo, "Processo desconhecido")

    # filtros de status
    filtro_finalizar = "o.status_id = 2"
    filtro_iniciar = "o.status_id IN (1,2)"

    # 🔎 Ordens disponíveis para ESTE setor
    if processo == "geral":

        ordens = databaseOBJ.readRaw(f"""
            SELECT o.numero_op
            FROM ordem_de_producao o
            WHERE {filtro_finalizar}
            ORDER BY o.numero_op DESC
        """, realdict=True)

        ordens_iniciar_producao = databaseOBJ.readRaw(f"""
            SELECT o.numero_op
            FROM ordem_de_producao o
            WHERE {filtro_iniciar}
            ORDER BY o.numero_op DESC
        """, realdict=True)

    else:

        ordens = databaseOBJ.readRaw(f"""
            SELECT o.numero_op
            FROM ordem_de_producao o
            WHERE {filtro_finalizar}
            AND NOT EXISTS (
                SELECT 1
                FROM producao p
                WHERE p.id_ordem_de_producao = o.id
                AND p.id_processo = %s
                AND p.status = 2
            )
            ORDER BY o.numero_op DESC
        """, (id_processo,), realdict=True)

        ordens_iniciar_producao = databaseOBJ.readRaw(f"""
            SELECT o.numero_op
            FROM ordem_de_producao o
            WHERE {filtro_iniciar}
            AND NOT EXISTS (
                SELECT 1
                FROM producao p
                WHERE p.id_ordem_de_producao = o.id
                AND p.id_processo = %s
                AND p.status = 2
            )
            ORDER BY o.numero_op DESC
        """, (id_processo,), realdict=True)

    # 🔎 Operadores
    operadores = databaseOBJ.readRaw("""
        SELECT id, codigo, nome
        FROM operador
        ORDER BY nome ASC
    """, realdict=True)

    # 🔎 Máquinas
    machine_names = databaseOBJ.readRaw("""
        SELECT id, bancada, setor, empresa
        FROM maquina
        ORDER BY id ASC
    """, realdict=True)

    return flask.render_template(
        'monitoramento_tabela.html',
        machine_names=machine_names,
        processo=processo,
        ordens=ordens,
        ordens_iniciar_producao=ordens_iniciar_producao,
        operadores=operadores,
        nome_processo=nome_processo
    )

@app.route('/buscar_produtos')
def buscar_produtos():

    search = flask.request.args.get('search','')

    produtos = databaseOBJ.readRaw("""
        SELECT id, codigo, nome
        FROM produtos
        WHERE codigo ILIKE %s
        ORDER BY codigo
        LIMIT 20
    """, (f"%{search}%",), realdict=True)

    return flask.jsonify(produtos)

@app.route('/processos_por_ordem')
@flask_login.login_required
def processos_por_ordem():

    numero_op = request.args.get("numero_op")

    if not numero_op:
        return flask.jsonify([])

    sql = """
        SELECT DISTINCT pr.id, pr.nome
        FROM producao p
        INNER JOIN processos pr
            ON p.id_processo = pr.id
        INNER JOIN ordem_de_producao o
            ON p.id_ordem_de_producao = o.id
        WHERE o.numero_op = %s
        AND p.status != 2
        ORDER BY pr.id
    """

    valores = databaseOBJ.readRaw(sql, (numero_op,), realdict=True)

    return flask.jsonify(valores)

@app.route('/setup_pcp')
@flask_login.login_required
def setup_pcp():

    machine_names = databaseOBJ.readRaw(
        "select id, bancada, setor, empresa from maquina order by id asc;"
    )

    user = databaseOBJ.readRaw(
        "select id, nome from usuarios where privilegio = 1 order by id DESC;"
    )

    produtos = databaseOBJ.readRaw(
        "select id, nome from produtos order by nome asc;",
        realdict=True
    )
    print("PRODUTOS:", produtos)

    clientes = databaseOBJ.readRaw(
        "SELECT id, nome FROM clientes ORDER BY nome ASC;",
        realdict=True
    )

    materiais = databaseOBJ.readRaw(
        "SELECT id, codigo, descricao FROM material ORDER BY codigo ASC;",
        realdict=True
    )

    print("MATERIAIS:", materiais)
    print("CLIENTES:", clientes)

    status_ordens = databaseOBJ.readRaw("""
        SELECT id, nome
        FROM status
        ORDER BY id
    """, realdict=True)

    produtos = databaseOBJ.readRaw("""
        SELECT id, codigo, nome
        FROM produtos
        ORDER BY codigo
    """, realdict=True)

    return render_template(
        'setup.html',
        machine_names=machine_names,
        user=user,
        materiais=materiais,
        status_ordens=status_ordens,
        produtos=produtos,
        clientes=clientes
    )

@app.route('/cadastro_usuarios', methods=['GET'])
@flask_login.login_required
@privilege_required(2)
def cadastro_usuarios():
    global databaseOBJ

    machine_names = databaseOBJ.readRaw(
        "SELECT id, bancada FROM maquina ORDER BY id ASC;"
    )

    return flask.render_template(
        'usuarios.html',
        machine_names=machine_names
    )

@app.route('/adicionar_usuario', methods=['POST'])
@flask_login.login_required
@privilege_required(2)
def adicionar_usuario():

    global databaseOBJ
    import bcrypt

    print("FORM RECEBIDO:", flask.request.form)

    usuario = flask.request.form['usuario']
    senha = flask.request.form['senha']
    confirmar_senha = flask.request.form['confirmar_senha']
    setor = flask.request.form['setor']
    privilegio = int(flask.request.form['privilegios'])

    # validar senha
    if senha != confirmar_senha:
        return flask.jsonify({
            'success': False,
            'error': 'As senhas não conferem'
        })

    if len(senha) < 6:
        return flask.jsonify({
            'success': False,
            'error': 'Senha deve ter pelo menos 6 caracteres'
        })

    # Proteção contra escalada de privilégio
    if privilegio > flask_login.current_user.privileges:
        return flask.jsonify({'success': False, 'error': 'Permissão inválida'})

    # Verifica se já existe
    existe = databaseOBJ.readRaw(
        "SELECT id FROM usuarios WHERE usuario=%s;",
        (usuario,)
    )

    if existe:
        return flask.jsonify({'success': False, 'error': 'Usuário já existe'})

    # Hash bcrypt
    senha_hash = bcrypt.hashpw(senha.encode(), bcrypt.gensalt()).decode()

    databaseOBJ.writeRaw(
        """
        INSERT INTO usuarios(usuario, senha, setor, privilegio)
        VALUES (%s,%s,%s,%s)
        """,
        (usuario, senha_hash, setor, privilegio)
    )

    return flask.jsonify({'success': True})

@app.route('/adm_operadores')
@flask_login.login_required
@privilege_required(2)
def adm_operadores():
    return flask.render_template('adm_operador.html')

@app.route('/dados_operadores', methods=['GET','POST','PUT','DELETE'])
@flask_login.login_required
def dados_operadores():

    # LISTAR
    if flask.request.method == 'GET':

        resultado = databaseOBJ.readRaw("""
            SELECT id, nome, codigo
            FROM operador
            ORDER BY nome
        """, realdict=True)

        return flask.jsonify({"operadores": resultado})


    # ADICIONAR
    elif flask.request.method == 'POST':

        nome = flask.request.form.get('nome')
        codigo = flask.request.form.get('codigo')

        # 🔎 verifica se já existe a chapa
        existe = databaseOBJ.readRaw("""
            SELECT 1
            FROM operador
            WHERE codigo = %s
        """,(codigo,), realdict=True)

        if existe:
            return flask.jsonify({
                "success": False,
                "error": "Chapa já cadastrada."
            })

        # ➜ se não existir, insere
        databaseOBJ.writeRaw("""
            INSERT INTO operador (nome, codigo)
            VALUES (%s,%s)
        """,(nome,codigo))

        return flask.jsonify({"success":True})

    # EDITAR
    elif flask.request.method == 'PUT':

        id_operador = flask.request.form.get('id')
        nome = flask.request.form.get('nome')
        codigo = flask.request.form.get('codigo')

        # 🔎 verifica se já existe outra chapa com o mesmo código
        existe = databaseOBJ.readRaw("""
            SELECT 1
            FROM operador
            WHERE codigo = %s
            AND id <> %s
        """,(codigo,id_operador), realdict=True)

        if existe:
            return flask.jsonify({
                "success": False,
                "error": "Chapa já cadastrada."
            })

        # ➜ atualiza
        databaseOBJ.writeRaw("""
            UPDATE operador
            SET nome=%s,
                codigo=%s
            WHERE id=%s
        """,(nome,codigo,id_operador))

        return flask.jsonify({"success":True})


    # EXCLUIR
    elif flask.request.method == 'DELETE':

        id_operador = flask.request.form.get('id')

        databaseOBJ.writeRaw("""
            DELETE FROM operador
            WHERE id = %s
        """, (id_operador,))

        return flask.jsonify({"success": True})

@app.route('/adicionar_ordem', methods=['POST'])
@flask_login.login_required
@privilege_required(2)
def adicionar_ordem():
    global databaseOBJ
    from datetime import datetime

    print("===== INICIO ADICIONAR ORDEM =====")
    print("FORM RECEBIDO:", flask.request.form) 

    try:
        numero_op = flask.request.form['numero_op'].strip()

        id_produto = int(flask.request.form['id_produto'])
        id_cliente = int(flask.request.form['id_cliente'])
        id_material = int(flask.request.form['id_material'])
        id_tratamento = int(flask.request.form['id_tratamento'])
        

        quantidade_total_ordem = int(flask.request.form['quantidade_total_ordem'])

        data_entrega = flask.request.form['data_entrega'].strip()

        

        numero_qualidade = flask.request.form.get('numero_qualidade', '').strip()

        print("DADOS RECEBIDOS:")
        print("OP:", numero_op)
        print("ID Produto:", id_produto)
        print("Quantidade:", quantidade_total_ordem)

    except (KeyError, ValueError) as e:
        print("ERRO AO RECEBER DADOS:", e)
        return flask.jsonify({'success': False, 'error': 'Dados inválidos'})

    # Validações
    if not numero_op or id_produto <= 0 or id_cliente <= 0:
        print("CAMPOS OBRIGATORIOS FALTANDO")
        return flask.jsonify({'success': False, 'error': 'Campos obrigatórios não preenchidos'})

    if quantidade_total_ordem <= 0:
        print("QUANTIDADE INVALIDA")
        return flask.jsonify({'success': False, 'error': 'Quantidade deve ser maior que zero'})

    try:
        datetime.strptime(data_entrega, '%Y-%m-%d')
    except ValueError:
        print("DATA INVALIDA")
        return flask.jsonify({'success': False, 'error': 'Data inválida'})

    # Verifica banco atual
    banco_atual = databaseOBJ.readRaw("SELECT current_database();")
    print("BANCO CONECTADO:", banco_atual)

    if quantidade_total_ordem <= 0:
        print("QUANTIDADE INVALIDA")
        return flask.jsonify({'success': False, 'error': 'Quantidade deve ser maior que zero'})

    # Verifica se já existe
    existe = databaseOBJ.readRaw(
        "SELECT id FROM ordem_de_producao WHERE numero_op='%s';" % numero_op
    )

    print("RESULTADO EXISTE:", existe)

    if existe:
        print("ORDEM JA EXISTE")
        return flask.jsonify({'success': False, 'error': 'Ordem já existe'})

    print("ANTES DO INSERT")

    databaseOBJ.writeRaw(
        """
        INSERT INTO ordem_de_producao (
            numero_op,
            id_produto,
            id_cliente,
            quantidade,
            data_entrega,
            id_tratamento,
            id_material,
            numero_qualidade
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (
            numero_op,
            id_produto,
            id_cliente,
            quantidade_total_ordem,
            data_entrega,
            id_tratamento,
            id_material,
            numero_qualidade
        )
    )

    print("DEPOIS DO INSERT")

    # Verificação imediata
    teste = databaseOBJ.readRaw(
        "SELECT id, numero_op FROM ordem_de_producao WHERE numero_op='%s';" % numero_op
    )

    print("VERIFICACAO APOS INSERT:", teste)

    print("===== FIM ADICIONAR ORDEM =====")

    return flask.jsonify({'success': True})

@app.route('/iniciar_producao', methods=['POST'])
@flask_login.login_required
def iniciar_producao():

    from datetime import datetime

    numero_op = flask.request.form['id_ordem']
    id_operador = int(flask.request.form['id_operador'])
    privilegio = flask_login.current_user.privileges
    setor_usuario = flask_login.current_user.setor

    MAPA_PROCESSOS = {
        "materia_prima": 1,
        "estamparia": 2,
        "solda": 3,
        "retifica": 4,
        "envio_terceiros": 5,
        "recebimento_terceiros": 6,
        "inspecao_final": 7,
        "expedicao": 8
    }

    # 🔎 Busca a ordem
    ordens = databaseOBJ.readRaw("""
        SELECT id
        FROM ordem_de_producao
        WHERE numero_op = %s
    """, (numero_op,))

    if not ordens:
        return flask.jsonify({"success": False, "erro": "Ordem não encontrada"}), 400

    id_ordem = ordens[0][0]

    # 👑 ADMIN (privilegio 3) pode escolher
    if privilegio == 3:
        id_processo = int(flask.request.form['id_processo'])

    # 👷 Usuário comum fica preso ao setor dele
    else:
        id_processo = MAPA_PROCESSOS.get(setor_usuario)

        if not id_processo:
            return flask.jsonify({
                "success": False,
                "erro": "Setor inválido para este usuário."
            }), 403

    # 🚫 Verifica se já existe produção ativa para essa OP nesse processo
    existe = databaseOBJ.readRaw("""
        SELECT 1
        FROM producao
        WHERE id_ordem_de_producao = %s
          AND id_processo = %s
          AND status = 1
    """, (id_ordem, id_processo))

    if existe:
        return flask.jsonify({
            "success": False,
            "erro": "Esta OP já está em produção neste processo."
        }), 400

    # ✅ Inserção
    databaseOBJ.writeRaw("""
        INSERT INTO producao (
            dt_inicio,
            status,
            qtde_produzida,
            id_operador,
            id_ordem_de_producao,
            id_processo
        )
        VALUES (%s,%s,%s,%s,%s,%s)
    """, (
        datetime.now(),
        1,
        0,
        id_operador,
        id_ordem,
        id_processo
    ))

    databaseOBJ.writeRaw("""
        UPDATE ordem_de_producao
        SET status_id = 2
        WHERE id = %s
    """, (id_ordem,))

    return flask.jsonify({"success": True})

@app.route('/finalizar_producao', methods=['POST'])
@flask_login.login_required
def finalizar_producao():

    from datetime import datetime

    numero_op = flask.request.form.get('id_ordem')
    id_operador_fim = request.form.get("id_operador_fim")
    quantidade = flask.request.form.get('quantidade')

    privilegio = flask_login.current_user.privileges
    setor_usuario = flask_login.current_user.setor

    MAPA_PROCESSOS = {
        "materia_prima": 1,
        "estamparia": 2,
        "solda": 3,
        "retifica": 4,
        "envio_terceiros": 5,
        "recebimento_terceiros": 6,
        "inspecao_final": 7,
        "expedicao": 8
    }

    # 👑 ADMIN precisa escolher setor
    if privilegio == 3:
        id_processo = flask.request.form.get('id_processo')

        if not id_processo:
            return flask.jsonify({
                "success": False,
                "erro": "Selecione o setor."
            }), 400

        id_processo = int(id_processo)

    else:
        id_processo = MAPA_PROCESSOS.get(setor_usuario)

        if not id_processo:
            return flask.jsonify({
                "success": False,
                "erro": "Setor inválido."
            }), 403

    # 🔎 Busca OP
    ordem = databaseOBJ.readRaw("""
        SELECT id
        FROM ordem_de_producao
        WHERE numero_op = %s
    """, (numero_op,))

    if not ordem:
        return flask.jsonify({"success": False, "erro": "Ordem não encontrada."}), 400

    id_ordem = ordem[0][0]

    # 🔎 Busca produção ativa daquele processo
    producao = databaseOBJ.readRaw("""
        SELECT id
        FROM producao
        WHERE id_ordem_de_producao = %s
          AND id_processo = %s
          AND status = 1
    """, (id_ordem, id_processo))

    if not producao:
        return flask.jsonify({
            "success": False,
            "erro": "Não existe produção ativa para este setor."
        }), 400

    id_producao = producao[0][0]

    # ✅ Finaliza somente aquela linha
    databaseOBJ.writeRaw("""
        UPDATE producao
        SET status = 2,
            dt_fim = %s,
            qtde_produzida = %s,
            id_operador_fim = %s
        WHERE id = %s
    """, (datetime.now(), quantidade, id_operador_fim, id_producao))

    # 🎯 Se for EXPEDIÇÃO, finaliza OP inteira
    if id_processo == 8:
        # Expedição finaliza geral
        databaseOBJ.writeRaw("""
            UPDATE ordem_de_producao
            SET status_id = 3
            WHERE id = %s
        """, (id_ordem,))
    else:
        # Só volta para aguardando se não houver mais setores produzindo
        databaseOBJ.writeRaw("""
            UPDATE ordem_de_producao
            SET status_id = 1
            WHERE id = %s
            AND NOT EXISTS (
                SELECT 1
                FROM producao
                WHERE id_ordem_de_producao = %s
                AND dt_fim IS NULL
            )
        """, (id_ordem, id_ordem))

    return flask.jsonify({"success": True})

@app.route('/produto_por_codigo', methods=['GET'])
@flask_login.login_required
def produto_por_codigo():

    codigo = flask.request.args.get('codigo')

    produto = databaseOBJ.readRaw(
        "SELECT id, nome FROM produtos WHERE codigo='%s';" % codigo,
        realdict=True
    )

    if not produto:
        return flask.jsonify({'success': False})

    return flask.jsonify({
        'success': True,
        'id_produto': produto[0]['id'],
        'nome': produto[0]['nome'].strip()
    })   

@app.route('/ordemdisponivel', methods=['GET'])
@flask_login.login_required
def ordem_disponivel():
    numero_op = flask.request.args.get('numero_op')

    existe = databaseOBJ.read(
        "SELECT id FROM ordem_de_producao WHERE numero_op = %s",
        (numero_op,)
    )

    return flask.jsonify({'available': not bool(existe)})

@app.route('/dados')
@flask_login.login_required
def dados():
    # Substitua "sua_tabela" pelo nome real da tabela que você está consultando
    sql_query = """
        SELECT 
            OP.K19_001_C AS OP,
            CONVERT(VARCHAR(10), OP.K19_002_D, 103) AS EMISSAO,
            D04.D04_001_C AS CODITEM,
            D04.D04QT_004_C AS PECA,
            OP.UKEY AS CHAVE,
            OP.K19_009_B AS PLANEJADO,
            OP.K19_010_B AS APONTADO,
            (OP.K19_009_B - OP.K19_010_B) AS EMABERTO
        FROM K19 OP
            INNER JOIN K01 AS MATERIAIS ON OP.K01_UKEY = MATERIAIS.UKEY
            INNER JOIN D04 ON D04.UKEY = MATERIAIS.D04_UKEY
        WHERE
            OP.ARRAY_296 = 8 
            AND OP.CIA_UKEY = 'WLKLF'
        -- 8 =Aberto
        -- """
    
    try:
        # Execute a consulta no SQL Server
        result_sqlserver = database_OBJ_sqlserver.read_raw(sql_query)

        # Renderize o template com os dados
        return render_template('dados.html', dados=result_sqlserver)

    except Exception as e:
        # Retorne uma mensagem de erro
        return f"Erro ao obter dados: {str(e)}"
    
#app.run(debug=True)

#app.run(host='0.0.0.0', port=5000, debug=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
