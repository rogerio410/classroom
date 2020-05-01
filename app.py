from classroom_utils import get_classroom_service, StatusTurma
from googleapiclient import errors, http
import simplejson
from classroom_operacoes import criar_disciplina, obter_disciplina, \
    obter_disciplinas, convidar_professor, associar_aluno, criar_disciplinas_lote
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
        criar_disciplinas_lote(service, disciplinas)
        flash('Disciplinas Criadas em lote!!!')
        return redirect('/disciplinas')


@app.route('/disciplinas')
def disciplinas():
    disciplinas = obter_disciplinas(service)
    disciplinas = filter(lambda d: d['courseState'] in [StatusTurma.ACTIVE.value],
                         disciplinas)
    return render_template('disciplinas.html', disciplinas=disciplinas)


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
        disciplinas.append(line.decode('utf-8').split('#'))

    return disciplinas
