import itertools
from datetime import datetime
from .classroom_utils import get_classroom_service, CourseState
from .firestore_utils import get_firestore_client, get_firestore_timestamp, save_batch
from classroomanager.auth.login_utils import login_required, is_loggedin
from .models import Course
from classroomanager.repository import FirestoreRepository
from googleapiclient import errors, http
import google
import simplejson
from .classroom_operacoes import *
from flask import (render_template, request,
                   redirect, flash, jsonify,
                   session, Blueprint, url_for)

# app is created on __init__.py
core = Blueprint('core', __name__,
                 url_prefix='/core',
                 template_folder='templates',
                 static_folder='static')

# service = get_classroom_service()
firestore = get_firestore_client()


@core.route('/sync_all')
@login_required
def sync_all_to_firestore():
    """
        Data model:
        * classroom object + user(profile_email) + timestamp
        * id on firestore is classroom_id-profile_email
    """
    profile_email = session.get('profile').get('email')
    disciplinas = obter_disciplinas(get_classroom_service())
    errors = []
    try:
        save_batch(disciplinas, errors, profile_email)
        flash(f'{len(disciplinas)-len(errors)} Courses synchronized successfully!')
        if errors:
            flash(f'{len(errors)} Courses NOT synchronized!')
    except Exception as e:
        print(e)
        flash(f'Fail to sync courses.')

    return redirect(url_for('core.courses'))


@core.route('/courses')
@login_required
def courses():
    courses_repository = FirestoreRepository('courses', Course)
    courses = courses_repository.list()

    # Temp:
    # courses = obter_disciplinas(get_classroom_service())
    # courses = filter(lambda x: 'CACAM' in (x.get('section') or ''), courses)

    return render_template('courses.html', courses=courses)


@core.route('/course/<int:id>')
def course(id):
    courses_repository = FirestoreRepository('courses', Course)
    try:
        course = courses_repository.get(id)
    except google.cloud.exceptions.NotFound as e:
        flash('Course not found!')
        return redirect(url_for('index'))

    return jsonify(course.to_dict())


@core.route('/form_disciplina', methods=['POST', 'GET'])
@login_required
def form_disciplina():

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
        return redirect(url_for('.index'))


@core.route('/disciplinas_lote', methods=['POST', 'GET'])
@login_required
def disciplinas_lote():
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
                get_classroom_service(), disciplinas, CourseState.PROVISIONED, disciplinas_criadas,
                disciplinas_nao_criadas)
        except Exception as e:
            print('Exception:', e)
            flash(f"Não foi possível criar as disciplinas")
            return redirect(url_for('core.courses'))

        qtd = len(disciplinas_criadas)

        # Log created courses
        salvar_em_arquivo(disciplinas_criadas)
        flash(f'Disciplinas Criadas ({qtd}) em lote!!!')

        # Save to Cache BD
        errors = []
        try:
            profile_email = session.get('profile').get('email')
            save_batch(disciplinas_criadas, errors, profile_email)
            flash(
                f'{len(disciplinas_criadas)-len(errors)} Courses synchronized successfully!')
            if errors:
                flash(f'{len(errors)} Courses NOT synchronized!')
        except Exception as e:
            print(e)
            flash(f'Fail to sync courses.')

        # Log not created courses
        if disciplinas_nao_criadas:
            salvar_em_arquivo_nao_criadas(disciplinas_nao_criadas)
            error_msgs = ''.join(set([d['error']
                                      for d in disciplinas_nao_criadas]))
            flash(f'ATENÇÃO: Algumas disciplinas não foram criadas!')
            flash(f'errors: {error_msgs}')

        return redirect(url_for('core.courses'))


@core.route('/disciplina/<int:id>/arquivar')
@login_required
def arquivar_disciplina_req(id):
    if arquivar_disciplina(get_classroom_service(), id):
        flash('Disciplina arquivada com sucesso!')
    else:
        flash('Não foi possível arquivar!')
    return redirect(url_for('core.courses'))


@core.route('/disciplina/<int:id>/associar_professor/<email>')
@login_required
def associar_professor_req(id, email):
    if associar_professor(service, id, email):
        flash('Disciplina arquivada com sucesso!')
    else:
        flash('Não foi possível arquivar!')
    return redirect(url_for('index'))


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
