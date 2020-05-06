from datetime import datetime
from classroom_utils import get_classroom_service, StatusTurma
from googleapiclient import errors, http
import simplejson
from classroom_operacoes import criar_disciplina, obter_disciplina, \
    obter_disciplinas, convidar_professor, associar_aluno, \
    criar_disciplinas_lote, arquivar_disciplina, criar_disciplinas_lote_one_by_one
from flask import Flask, render_template, request, redirect, flash


app = Flask(__name__)

app.secret_key = 'HELLO-BATMAN...'

# on terminal:
# export FLASK_APP=app.py
# export FLASK_ENV=development
# flask run

service = get_classroom_service()


@app.route('/disciplina', methods=['POST', 'GET'])
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
def disciplina_lote():
    if request.method == 'GET':
        return render_template('form_disciplina_lote.html')
    else:
        if 'file' not in request.files:
            flash('Nenhum aquivo recebido')
            return redirect(request.url)
        file = request.files['file']
        disciplinas = extrair_de_arquivo(file)
        # disciplinas = criar_disciplinas_lote(service, disciplinas)
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


@app.route('/disciplinas')
def disciplinas():
    disciplinas = obter_disciplinas(service)
    # somente ATIVAS
    disciplinas = filter(lambda d: d['courseState'] in [StatusTurma.ACTIVE.value],
                         disciplinas)

    # somente do IFPI - Remote
    def is_ifpi_remote(d):
        sala = d.get('room') or ''
        return 'remote' in sala

    disciplinas = filter(is_ifpi_remote, disciplinas)

    def order_by_tudo(d):
        nome = d.get('name')
        detalhes = d.get('section')
        curso, turma, outros = detalhes.split(' - ')
        ano_periodo, dept, campus = outros.split('/')
        return campus+dept+curso+turma+nome

    disciplinas = sorted(disciplinas, key=order_by_tudo)
    # to csv
    salvar_em_arquivo(disciplinas)

    # print('Disciplinas 0', disciplinas[0])
    return render_template('disciplinas.html', disciplinas=disciplinas)


@app.route('/disciplina/<int:id>/arquivar')
def arquivar_disciplina_req(id):
    if arquivar_disciplina(service, id):
        flash('Disciplina arquivada com sucesso!')
    else:
        flash('Não foi possível arquivar!')
    return redirect('/disciplinas')


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
