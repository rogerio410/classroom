import datetime


class Course(object):

    def __init__(self, id, name,
                 enrollmentCode, section,
                 room, description,
                 descriptionHeading, ownerId, courseState,
                 creationTime, updateTime, alternateLink):
        self.id = id
        self.name = name
        self.enrollmentCode = enrollmentCode
        self.section = section
        self.room = room
        self.description = description
        self.descriptionHeading = descriptionHeading
        self.ownerId = ownerId
        self.courseState = courseState
        self.creationTime = creationTime
        try:
            self.updateTime = datetime.datetime.strptime(
                updateTime, '%Y-%m-%dT%H:%M:%S.%fz')
        except:
            self.updateTime = datetime.datetime.strptime(
                updateTime, '%Y-%m-%dT%H:%M:%SZ')

        self.alternateLink = alternateLink

    @staticmethod
    def from_dict(course_dict):
        c = Course(course_dict['id'],
                   course_dict['name'],
                   course_dict.get('enrollmentCode') or '',
                   course_dict.get('section') or '',
                   course_dict.get('room') or '',
                   course_dict.get('description') or '',
                   course_dict.get('descriptionHeading') or '',
                   course_dict.get('ownerId') or '',
                   course_dict.get('courseState') or '',
                   course_dict.get('creationTime') or '',
                   course_dict.get('updateTime') or '',
                   course_dict.get('alternateLink') or '',
                   )
        return c

    def to_dict(self):
        return self.__dict__
