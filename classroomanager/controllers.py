from datetime import datetime
from .classroom_utils import get_classroom_service, CourseState
from .firestore_utils import get_firestore_client, get_firestore_timestamp
from .login_utils import login_required, is_loggedin
from .models import Course
from googleapiclient import errors, http
import simplejson
from .classroom_operacoes import *
from flask import render_template, request, redirect, flash, jsonify, session
from classroomanager import app

# app is created on __init__.py

# service = get_classroom_service()
firestore = get_firestore_client()


@app.route('/sync_all')
@login_required
def sync_all_to_firestore():
    """
        Data model: 
        * classroom object + user(profile_email) + timestamp
        * id on firestore is classroom_id-profile_email
    """
    profile_email = session.get('profile').get('email')
    disciplinas = obter_disciplinas(get_classroom_service())

    # limite de 500 por request - timestamp, increment and ArrayUnion is like 1
    PER_REQUEST = 250
    batch_slots = len(disciplinas) // PER_REQUEST
    if len(disciplinas) % PER_REQUEST > 0:
        batch_slots += 1

    for i in range(batch_slots):
        batch = firestore.batch()
        start = i * PER_REQUEST
        end = start + PER_REQUEST
        for disc in disciplinas[start:end]:
            id = f"{disc['id']}-{profile_email}"
            disc['user'] = profile_email
            disc['timestamp'] = get_firestore_timestamp()

            ref = firestore.collection('courses').document(id)
            batch.set(ref, disc)

        try:
            batch.commit()
            flash(f'{len(disciplinas)} Courses synchronized successfully!')
        except Exception as e:
            flash(f'Erro ao sincronizar: {e}!')

    return redirect('/disciplinas')


@app.route('/')
@login_required
def index():
    return render_template('index.html')


@app.route('/disciplinas')
@login_required
def disciplinas():

    # TODO: create a Repository to encapsulate query like this
    profile_email = session.get('profile').get('email')
    courses_ref = firestore.collection('courses')

    courses_ref = courses_ref.where('user', '==', profile_email)
    courses_ref = courses_ref.where(
        'courseState', '==', CourseState.ACTIVE.value)

    docs = courses_ref.stream()

    lista = []
    for doc in docs:
        lista.append(doc.to_dict())

    return render_template('disciplinas.html', disciplinas=lista)


@app.route('/disciplina', methods=['POST', 'GET'])
@login_required
def disciplina():

    if request.method == 'GET':
        return render_template('form_disciplina.html')
    else:
        dados_disciplina = extrair_da_request(request)
        try:
            disciplina = criar_disciplina(
                service,
                *dados_disciplina
            )
            flash('Disciplinas criada com sucesso!')
        except errors.HttpError as e:
            # Error attr: code - status - message
            error = simplejson.loads(e.content).get('error')
            show_error(error)
            flash(f'Error: {error.get("code")} - {error.get("message")}')
        return redirect('/disciplinas')


@app.route('/disciplinas_lote', methods=['POST', 'GET'])
@login_required
def disciplina_lote():
    if request.method == 'GET':
        return render_template('form_disciplina_lote.html')
    else:
        if 'file' not in request.files:
            flash('Nenhum aquivo recebido')
            return redirect(request.url)
        file = request.files['file']
        disciplinas = extrair_de_arquivo(file)
        try:
            disciplinas_criadas = []
            disciplinas_nao_criadas = []
            criar_disciplinas_lote_one_by_one(
                service, disciplinas, disciplinas_criadas,
                disciplinas_nao_criadas)
        except Exception as e:
            print('Exception:', e)
            flash(f"Não foi possível criar as disciplinas")
            return redirect('/disciplinas')

        qtd = len(disciplinas_criadas)
        salvar_em_arquivo(disciplinas_criadas)
        flash(f'Disciplinas Criadas ({qtd}) em lote!!!')

        if disciplinas_nao_criadas:
            salvar_em_arquivo_nao_criadas(disciplinas_nao_criadas)
            flash(f'ATENÇÃO: Algumas disciplinas não foram criadas!')

        return redirect('/disciplinas')


@app.route('/disciplina/<int:id>/arquivar')
@login_required
def arquivar_disciplina_req(id):
    if arquivar_disciplina(service, id):
        flash('Disciplina arquivada com sucesso!')
    else:
        flash('Não foi possível arquivar!')
    return redirect('/disciplinas')


@app.route('/disciplina/<int:id>/associar_professor/<email>')
@login_required
def associar_professor_req(id, email):
    if associar_professor(service, id, email):
        flash('Disciplina arquivada com sucesso!')
        return 'Professor associado'
    else:
        flash('Não foi possível arquivar!')
        return 'Não foi possível associar'


def extrair_da_request(request):
    disciplina = []
    disciplina.append(request.form.get('nome'))
    disciplina.append(request.form.get('curso'))
    disciplina.append(request.form.get('turma'))
    disciplina.append(request.form.get('ano_periodo'))
    disciplina.append(request.form.get('dept'))
    disciplina.append(request.form.get('campus'))
    disciplina.append(request.form.get('professor') or 'me')
    return tuple(disciplina)


def extrair_de_arquivo(file):
    disciplinas = []
    for line in file:
        disciplinas.append(line.decode('utf-8').strip().split(';'))

    return disciplinas


def salvar_em_arquivo(disciplinas):
    sufixo = datetime.now().isoformat()[: 19].replace('-', '').replace(':', '')
    nome = 'log/disciplinas_criadas_'+sufixo+'.txt'
    arquivo = open(nome, 'w')

    for d in disciplinas:
        try:
            section = d['section']
            dados1 = section.split('/')
            campus = dados1[-1]
            dept = dados1[-2]
            dados2 = dados1[0].split('-')
            curso = dados2[0]
            turma = dados2[1]
            linha = f"{d['name']};{campus};{dept};{curso};{turma}\
                ;{d['enrollmentCode']}\n"
            arquivo.write(linha)
        except Exception as e:
            print(f"{d['name']} - {d['section']} - {d['room']}")

    arquivo.close()


def salvar_em_arquivo_nao_criadas(disciplinas):
    sufixo = datetime.now().isoformat()[: 19].replace('-', '').replace(':', '')
    nome = 'log/disciplinas_NAO_criadas_'+sufixo+'.txt'
    arquivo = open(nome, 'w')

    for d in disciplinas:
        linha = f"{d['name']};{d['section']};\
            {d['ownerId']};{d['error']}\n"
        arquivo.write(linha)

    arquivo.close()


def obter_disciplinas_ativas():
    disciplinas = obter_disciplinas(get_classroom_service())

    # somente ATIVAS
    disciplinas = filter(lambda d: d['courseState'] in [CourseState.ACTIVE.value],
                         disciplinas)

    # somente do IFPI - Remote
    def is_ifpi_remote(d):
        sala = d.get('room') or ''
        return 'remote' in sala

    # disciplinas = filter(is_ifpi_remote, disciplinas)

    def order_by_tudo(d):
        nome = d.get('name')
        try:
            section = d['section']
            dados1 = section.split('/')
            campus = dados1[-1]
        except Exception as e:
            campus = ''
        # dept = dados1[-2]
        # dados2 = dados1[0].split('-')
        # curso = dados2[0]
        # turma = dados2[1]
        # return campus+dept+curso+turma+nome

        # for d in disciplinas:
        #     nome = d['name']
        #     section = d['section']
        #     sala = d['room']

        #     try:
        #         curso, turma, *_ = section.split('-')
        #     except Exception:
        #         curso = section
        #         turma = section

        #     try:
        #         flag = ' '
        #         if '#' in sala:
        #             flag = '#'
        #         elif '-' in sala:
        #             flash = '-'

        #         dept, campus, *_ = sala.split(flag)

        #         linhas += f'{nome};{curso};{turma};{dept};{campus}\n'
        #     except Exception:
        #         erros += f'{nome};{section};{sala}\n'
        # resultado = 'DISCIPLINAS:\n'+linhas+'\nERROS:\n'+erros
        return campus+nome

    disciplinas = sorted(disciplinas, key=order_by_tudo)
    return disciplinas
