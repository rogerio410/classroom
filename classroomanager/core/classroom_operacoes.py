import simplejson
from googleapiclient import errors
from httplib2 import Http
from .classroom_utils import CourseState
# https://developers.google.com/resources/api-libraries/documentation/classroom/v1/python/latest/classroom_v1.courses.html
# https://developers.google.com/classroom/guides/batch


def criar_disciplina(service, nome, curso,
                     turma, ano_periodo,
                     dept, campus, professor='me', status='ACTIVE',
                     descricao='IFPI - Atividades Remotas'):
    course = {
        'name': nome,
        'section': f'{curso} - {turma} - {ano_periodo}/{dept}/{campus} ',
        'descriptionHeading': '',
        'description': descricao,
        'room': f'{dept} @ {campus}',
        'ownerId': professor,
        'courseState': status}

    course = service.courses().create(body=course).execute()
    return course


def obter_disciplina(service, course_id):
    try:
        course = service.courses().get(id=course_id).execute()
        return course
    except errors.HttpError as e:
        error = simplejson.loads(e.content).get('error')
        if(error.get('code') == 404):
            raise Exception(f'Course with ID "{course_id}" not found.')
        else:
            raise Exception(f'Erro no classroom')


def obter_disciplinas(service, professor='me'):
    courses = []
    page_token = None

    while True:
        try:
            response = service.courses().list(pageToken=page_token,
                                              pageSize=500,
                                              courseStates=[
                                                  CourseState.ACTIVE.value,
                                                  CourseState.PROVISIONED.value],
                                              # teacherId=professor
                                              ).execute()
        except errors.HttpError as e:
            error = simplejson.loads(e.content).get('error')
            if(error.get('code') == 404):
                raise Exception(f'Course with ID "{course_id}" not found.')
            else:
                raise Exception(f'Erro no classroom')
        except Exception as e:
            print('Exception', e)

        courses.extend(response.get('courses', []))
        page_token = response.get('nextPageToken', None)
        if not page_token:
            break

    return courses


def criar_disciplina_com_objeto(service, course):
    course = service.courses().create(body=course).execute()
    return course


def criar_disciplinas_lote_one_by_one(service, disciplinas, course_state,
                                      disciplinas_criadas,
                                      disciplinas_nao_criadas):

    for d in disciplinas:
        campus, dept, curso, nome, turma, ano_periodo, professor = d
        course = {
            'name': nome,
            'section': f'{curso} - {turma} - {ano_periodo}/{dept}/{campus} ',
            'descriptionHeading': '',
            'description': """ IFPI - Atividades Remotas """,
            'room': f'{dept}#{campus}#ifpi#remote#20201',
            # 'ownerId': 'me',
            # 'ownerId': 'emailinexistente.ok@ifpi.edu.br',
            'ownerId': professor,
            'courseState': course_state.value
        }

        try:
            c = criar_disciplina_com_objeto(service, course)
            disciplinas_criadas.append(c)
        except errors.HttpError as e:
            error = simplejson.loads(e.content).get('error')
            course['error'] = f"Erro ao criar: {error['code']} - {error['message']}"
            disciplinas_nao_criadas.append(course)
        except Exception as e:
            course['error'] = e
            disciplinas_nao_criadas.append(course)


def criar_disciplinas_lote(service, disciplinas):
    # Está dando erro ao processo 3 ou 4 requests do lote.
    disciplinas_criadas = []

    def callback(request_id, response, exception):

        if exception is not None:
            print(
                f'Error adding course "{request_id}" to\
                the course course: {exception}')
            error = simplejson.loads(exception.content).get('error')
            print('Error --> ', error)
        else:
            ''' Response dict
            {
                "id":"82332516514",
                "name":"REDAÇÃO",
                "section":"11IMEC - 303 - 2020/DCHL/CATCE ",
                "description":" IFPI - Atividades Remotas ",
                "room":"DCHL#CATCE#ifpi-remote-20201",
                "ownerId":"106866812652931243930",
                "creationTime":"2020-05-05T12:39:42.959Z",
                "updateTime":"2020-05-05T12:39:41.766Z",
                "enrollmentCode":"j3qlr5p",
                "courseState":"ACTIVE",
                "alternateLink":"https://classroom.google.com/c/ODIzMzI1MTY1MTRa",
                "teacherGroupEmail":"REDA_O_11IMEC_303_2020_DCHL_CATCE_teachers_facb32d2@ifpi.edu.br",
                "courseGroupEmail":"REDA_O_11IMEC_303_2020_DCHL_CATCE_1fa95268@ifpi.edu.br",
                "teacherFolder":{
                    "id":"0B-1bsqJzHRrSfmNSTGh3MjZ6alQ0RDdGNzIzWlZtU3FqZkp1cHRCemJLVjd2bDNMOGJxVzQ"
                },
                "guardiansEnabled":False
                }
            '''
            print(f'Course "{request_id}" criado')
            disciplinas_criadas.append(response)

    batch = service.new_batch_http_request(callback=callback)

    for d in disciplinas:
        campus, dept, curso, nome, turma, ano_periodo, professor = d
        course = {
            'name': nome,
            'section': f'{curso} - {turma} - {ano_periodo}/{dept}/{campus} ',
            'descriptionHeading': '',
            'description': """ IFPI - Atividades Remotas """,
            'room': f'{dept}#{campus}#ifpi-remote-20201',
            'ownerId': 'me',
            # 'ownerId': professor,
            'courseState': 'ACTIVE'
        }

        request = service.courses().create(body=course)
        request_id = f'{nome} - {curso} - {turma} - {ano_periodo}/{dept}/{campus} '
        batch.add(request, request_id=request_id)

    http = Http()
    batch.execute(http=http)
    return disciplinas_criadas


def arquivar_disciplina(service, disciplina_id):
    course_id = disciplina_id
    course = {
        'courseState': 'ARCHIVED',
    }
    try:
        course = service.courses().patch(id=course_id, updateMask='courseState',
                                         body=course).execute()
        return True
    except Exception as e:
        return False


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

'''
Disciplinas 0 {
   "id":"96337156580",
   "name":"Téc. Info. Adm.",
   "descriptionHeading":"Téc. Info. Adm.",
   "room":"3o Adm 2020",
   "ownerId":"110865431028909299594",
   "creationTime":"2020-05-05T12:20:06.988Z",
   "updateTime":"2020-05-05T12:20:05.952Z",
   "enrollmentCode":"24ondx7",
   "courseState":"ACTIVE",
   "alternateLink":"https://classroom.google.com/c/OTYzMzcxNTY1ODBa",
   "teacherGroupEmail":"T_c_Info_Adm_professores_71c955c1@ifpi.edu.br",
   "courseGroupEmail":"T_c_Info_Adm_9b29fb84@ifpi.edu.br",
   "teacherFolder":{
      "id":"0BzFHc4gP6QXifnJoUjVxV0JESXFpOEY3VkpKWDJsWDhuUFl2am9wMmNtX2UzaGw2V0JUX28"
   },
   "guardiansEnabled":False,
   "calendarId":"ifpi.edu.br_classroom77614723@group.calendar.google.com"
}
'''
