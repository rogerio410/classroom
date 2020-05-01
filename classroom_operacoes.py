import simplejson
from googleapiclient import errors
from httplib2 import Http
# https://developers.google.com/resources/api-libraries/documentation/classroom/v1/python/latest/classroom_v1.courses.html
# https://developers.google.com/classroom/guides/batch


def criar_disciplina(service, nome, curso,
                     turma, ano_periodo,
                     dept, campus, professor='me'):
    course = {
        'name': nome,
        'section': f'{curso} - {turma} - {ano_periodo}/{dept}/{campus} ',
        'descriptionHeading': '',
        'description': """ IFPI - Atividades Remotas """,
        'room': f'{dept} @ {campus}',
        'ownerId': professor,
        'courseState': 'ACTIVE'
    }

    course = service.courses().create(body=course).execute()
    return course


def obter_disciplina(service, course_id):
    try:
        course = service.courses().get(id=course_id).execute()
        nome = course.get('name')
        print(f'Course "{nome}" found.')
        return course
    except errors.HttpError as e:
        error = simplejson.loads(e.content).get('error')
        if(error.get('code') == 404):
            raise Exception(f'Course with ID "{course_id}" not found.')
        else:
            raise Exception(f'Erro no classroom')


def obter_disciplinas(service):
    courses = []
    page_token = None

    while True:
        response = service.courses().list(pageToken=page_token,
                                          pageSize=100).execute()
        courses.extend(response.get('courses', []))
        page_token = response.get('nextPageToken', None)
        if not page_token:
            break

    return courses


def criar_disciplinas_lote(service, disciplinas):

    def callback(request_id, response, exception):
        if exception is not None:
            print(
                f'Error adding course "{request_id}" to\
                the course course: {exception}')
        else:
            print(f'Course "{request_id}" criado')

    batch = service.new_batch_http_request(callback=callback)

    for d in disciplinas:
        nome, curso, turma, ano_periodo, dept, campus, professor = d
        course = {
            'name': nome,
            'section': f'{curso} - {turma} - {ano_periodo}/{dept}/{campus} ',
            'descriptionHeading': '',
            'description': """ IFPI - Atividades Remotas """,
            'room': f'{dept} @ {campus}',
            'ownerId': professor,
            'courseState': 'ACTIVE'
        }

        request = service.courses().create(body=course)
        request_id = f'{nome} - {curso} - {turma} - {ano_periodo}/{dept}/{campus} '
        batch.add(request, request_id=request_id)

    http = Http()
    batch.execute(http=http)


def associar_professor(service, disciplina_id, email):
    course_id = disciplina_id
    teacher_email = email
    teacher = {
        'userId': teacher_email
    }
    try:
        teacher = service.courses().teachers().create(courseId=course_id,
                                                      body=teacher).execute()
        return teacher
    except errors.HttpError as e:
        error = simplejson.loads(e.content).get('error')
        if(error.get('code') == 409):
            print(
                f'User "{teacher_email}" is already a member of this course.')
        else:
            print(f'Code: {error["code"]} - Status: {error["status"]}')
            return None, error


def associar_aluno(service, disciplina_id, disciplina_code, email):
    course_id = disciplina_id
    enrollment_code = disciplina_code
    student = {
        'userId': email
    }

    try:
        student = service.courses().students().create(
            courseId=course_id,
            enrollmentCode=enrollment_code,
            body=student).execute()
        return student
    except errors.HttpError as e:
        error = simplejson.loads(e.content).get('error')
        if(error.get('code') == 409):
            print(
                f'User "{email}" is already a member of this course.')
        else:
            print(f'Code: {error["code"]} - Status: {error["status"]}')
            return None, error


def convidar_professor(service, disciplina_id, email):
    teacher_email = email
    invitation = {
        "userId": teacher_email,
        "courseId": disciplina_id,
        "role": 'TEACHER'
    }

    try:
        # teacher = service.courses().teachers().create(courseId=disciplina_id,
        #                                               body=teacher).execute()
        invitation = service.invitations().create(body=invitation).execute()

        return invitation
    except errors.HttpError as e:
        error = simplejson.loads(e.content).get('error')
        print(error)
        if(error.get('code') == 409):
            print(
                f'User "{teacher_email}" is already a member of this course.')
        else:
            print(simplejson.loads(e.content))
            raise


'''
{
  "error": {
    "code": 403,
      "message": "@ClassroomApiDisabled The user is not permitted to access
                the Classroom API.",
      "errors": [
        {
          "message": "@ClassroomApiDisabled The user is not permitted to
                    access the Classroom API.",
          "domain": "global",
          "reason": "forbidden"
        }
      ],
      "status": "PERMISSION_DENIED"
  }
}
'''
