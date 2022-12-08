from datetime import datetime
from dateutil import relativedelta as rdelta

# "Return all rows from a cursor as a dict"
def dictfetchall(cursor):
    columns = [col[0] for col in cursor.description]
    return [
        dict(zip(columns, row))
        for row in cursor.fetchall()
    ]

# "Return one row from a cursor as a dict"
def dictfetchone(cursor):
    columns = [col[0] for col in cursor.description]
    return [
        dict(zip(columns, row))
        for row in cursor.fetchall()
    ][0]

# Queries user token
def _query_token(cursor, username):
    try:
        token_query = "SELECT token FROM \"User\" WHERE username='%s'" % (username)
        cursor.execute(token_query)
        return dictfetchone(cursor)

    except Exception as error:
        print(error)
        return None


# formats response for reviews and removes un-necessary data
def _filter_reviews(cursor, review_resp):
    reviews = []
    for _review in review_resp:
        # fetches Professor
        review = {'id': _review['id'], 'body': _review['body'], 'rating': _review['rating'],
                  'grade': _review['grade']}

        professor_resp = _query_professors_by_id(cursor, _review['instructor_id'])
        instructor_name = professor_resp['first_name'] + " " + professor_resp['last_name']
        review['instructor_name'] = instructor_name

        # fetches subject
        subject_resp = _query_subject_by_id(cursor, _review['subject_id'])
        subject_name = subject_resp['name'] + subject_resp['catalog_number']
        review['subject_name'] = subject_name

        # Posted ? sec/min/hour ago filtering
        diff = rdelta.relativedelta(datetime.utcnow(), _review['last_updated'])

        if diff.years != 0:
            label = 'years'
            if diff.years == 1: label = 'year'
            review['posted'] = "Posted %s %s ago" % (diff.years, label)
        elif diff.months != 0:
            label = 'months'
            if diff.months == 1: label = 'month'
            review['posted'] = "Posted %s %s ago" % (diff.months, label)
        elif diff.days != 0:
            label = 'days'
            if diff.days == 1: label = 'day'
            review['posted'] = "Posted %s %s ago" % (diff.days, label)
        elif diff.hours != 0:
            label = 'hours'
            if diff.hours == 1: label = 'hour'
            review['posted'] = "Posted %s %s ago" % (diff.hours, label)
        elif diff.minutes != 0:
            label = 'minutes'
            if diff.minutes == 1: label = 'minute'
            review['posted'] = "Posted %s %s ago" % (diff.minutes, label)
        else:
            review['posted'] = "Posted %s seconds ago" % diff.seconds
        reviews.append(review)

    return reviews


def _query_recent_reviews(cursor):
    try:
        review_query = "SELECT * FROM \"Review\" WHERE approved=1 ORDER BY last_updated desc LIMIT 4"
        cursor.execute(review_query)
        return _filter_reviews(cursor, dictfetchall(cursor))

    except Exception as error:
        print(error)
        return None


# Queries all reviews of a professor given a instructor_id
def _query_reviews(cursor, instructor_id, subject_id):
    try:
        if instructor_id and subject_id:
            review_query = "SELECT * FROM \"Review\" WHERE approved=1 AND instructor_id=%s AND subject_id=%s ORDER BY last_updated desc" % (
            str(instructor_id), str(subject_id))
        elif instructor_id:
            review_query = "SELECT * FROM \"Review\" WHERE approved=1 AND instructor_id=%s ORDER BY last_updated desc" % (
                str(instructor_id))
        elif subject_id:
            review_query = "SELECT * FROM \"Review\" WHERE approved=1 AND subject_id=%s ORDER BY last_updated desc" % (
                str(subject_id))
        else:
            return None

        cursor.execute(review_query)
        review_resp = dictfetchall(cursor)
        return _filter_reviews(cursor, review_resp)

    except Exception as error:
        print(error)
        return None


# Queries a professor given the professor_name
def _query_professor(cursor, professor_name, instructor_id):
    # Bug fix: escape apostrophe (Kathy O'Dell -> Kathy O''Dell)
    professor_name = professor_name.replace("'", "''")
    try:
        professor_name_parsed = tuple(professor_name.split())
        
        if len(professor_name_parsed) == 3:
            first_name, last_name, suffix = professor_name_parsed
            last_name = last_name + " " + suffix
            
        elif len(professor_name_parsed) == 2:
            first_name, last_name = professor_name_parsed
        else:
            return None
        
        # bug fix: get instructor by id to prevent duplicate name issues
        if instructor_id:
            professor_query = "SELECT id, faculty_id, first_name, last_name FROM \"Instructor\" WHERE first_name='%s' AND last_name='%s' AND id='%d'" % (
                first_name, last_name, int(instructor_id))
        else:
            professor_query = "SELECT id, faculty_id, first_name, last_name FROM \"Instructor\" WHERE first_name='%s' AND last_name='%s'" % (
                first_name, last_name)

        cursor.execute(professor_query)
        return dictfetchone(cursor)

    except Exception as error:
        print(error)
        return None


# Queries a professor by id
def _query_professors_by_id(cursor, instructor_id):
    try:
        professor_query = "SELECT id, first_name, last_name FROM \"Instructor\" WHERE id=%s" % (instructor_id)
        cursor.execute(professor_query)
        return dictfetchone(cursor)

    except Exception as error:
        return None


# Queries a professor given the professor_name
def _query_professors_by_subject(cursor, subject_id, semester):
    try:
        if semester:
            professor_query = "SELECT DISTINCT instructor_id FROM \"Course\" WHERE subject_id=%s AND semester='%s'" % (
                str(subject_id), semester)
        else:
            professor_query = "SELECT DISTINCT instructor_id FROM \"Course\" WHERE subject_id=%s" % (subject_id)

        cursor.execute(professor_query)
        professors = dictfetchall(cursor)
        professors_list = []
        for professor in professors:
            instructor_id = professor['instructor_id']
            professor_query = "SELECT id, first_name, last_name FROM \"Instructor\" WHERE id=%s" % (str(instructor_id))
            cursor.execute(professor_query)
            professor_res = dictfetchone(cursor)
            professors_list.append(professor_res)
        return professors_list

    except Exception as error:
        print(error)
        return None


# Queries courses
def _query_course(cursor, subject_id, instructor_id, section, semester):
    try:
        # Queries by instructor_id
        if subject_id is None and instructor_id:
            if semester and section:
                course_query = "SELECT * FROM \"Course\" WHERE instructor_id=%s AND section='%s' AND semester='%s' " % (
                    str(instructor_id), section, semester)
            elif semester:
                course_query = "SELECT * FROM \"Course\" WHERE instructor_id=%s AND semester='%s'" % (
                    str(instructor_id), semester)
            elif section:
                course_query = "SELECT * FROM \"Course\" WHERE instructor_id=%s AND section='%s'" % (
                    str(instructor_id), section)
            else:
                course_query = "SELECT * FROM \"Course\" WHERE instructor_id=%s" % (str(instructor_id))

        # Queries by subject_id and/or semester only
        elif instructor_id is None:
            if semester is None:
                course_query = "SELECT * FROM \"Course\" WHERE subject_id=%s" % (str(subject_id))
            else:
                course_query = "SELECT * FROM \"Course\" WHERE subject_id=%s AND semester='%s'" % (
                    str(subject_id), semester)

        # Queries by instructor_id, subject_id, section and semester
        else:
            if section is not None and semester is not None:
                course_query = "SELECT * FROM \"Course\" WHERE subject_id='%s' AND section='%s' AND semester='%s' AND instructor_id=%s" % (
                    subject_id, str(section), semester, str(instructor_id))
            elif section is not None:
                course_query = "SELECT * FROM \"Course\" WHERE subject_id='%s' AND section='%s' AND instructor_id=%s" % (
                    subject_id, str(section), str(instructor_id))
            elif semester is not None:
                course_query = "SELECT * FROM \"Course\" WHERE subject_id='%s' AND semester='%s' AND instructor_id=%s" % (
                    subject_id, semester, str(instructor_id))
            else:
                course_query = "SELECT * FROM \"Course\" WHERE subject_id='%s' AND instructor_id=%s" % (
                    subject_id, str(instructor_id))

        cursor.execute(course_query)
        return dictfetchall(cursor)

    except Exception as error:
        print(error)
        return None


# queries
def _query_semesters(cursor, subject_id, instructor_id):
    try:
        if instructor_id and subject_id:
            course_query = "SELECT DISTINCT semester, term FROM \"Course\" WHERE subject_id='%s' AND instructor_id='%s' ORDER BY term desc" % (
                subject_id, instructor_id)
        elif instructor_id:
            course_query = "SELECT DISTINCT semester, term FROM \"Course\" WHERE instructor_id='%s' ORDER BY term desc" % (instructor_id)
        elif subject_id:
            course_query = "SELECT DISTINCT semester, term FROM \"Course\" WHERE subject_id='%s' ORDER BY term desc" % (subject_id)
        else:
            return None

        cursor.execute(course_query)
        resp = dictfetchall(cursor)
        semesters = []
        for semester in resp:
            semesters.append(semester['semester'])
        return semesters


    except Exception as error:
        print(error)
        return None


# Queries subjects by instructor_id
def _query_subjects_by_instructor(cursor, instructor_id):
    try:
        course_query = "SELECT DISTINCT subject_id FROM \"Course\" WHERE instructor_id=%s" % (str(instructor_id))
        cursor.execute(course_query)
        course_query = dictfetchall(cursor)
        return [_query_subject_by_id(cursor, course_res['subject_id']) for course_res in course_query]

    except Exception as error:
        print(error)
        return None

# Queries subject by subject_id
def _query_subject_by_id(cursor, subject_id):
    try:
        subject_query = "SELECT id, name, catalog_number, catalog_topic, description, credits, academic_org_short_desc, descriptive_name FROM \"Subject\" WHERE id=%s" % (str(subject_id))
        cursor.execute(subject_query)
        return dictfetchone(cursor)

    except Exception as error:
        print(error)
        return None


# Queries subject by name and catalog_number
def _query_subject(cursor, name, catalog_number, topic):
    # Bug fix: escape apostrophe
    if topic:
        topic = topic.replace("'", "''")
    try:
        if topic:
            subject_query = "SELECT id, name, catalog_number, catalog_topic, description, credits, academic_org_short_desc, descriptive_name FROM \"Subject\" WHERE name='%s' AND catalog_number='%s' AND catalog_topic='%s'" % (
                name, str(catalog_number), topic)
        else:
            subject_query = "SELECT id, name, catalog_number, catalog_topic, description, credits, academic_org_short_desc, descriptive_name FROM \"Subject\" WHERE name='%s' AND catalog_number='%s'" % (
                name, str(catalog_number))
        cursor.execute(subject_query)
        return dictfetchone(cursor)

    except Exception as error:
        print(error)
        return None


def _query_subject_topics(cursor, name, catalog_number):
    try:
        subject_query = "SELECT catalog_topic FROM \"Subject\" WHERE name='%s' AND catalog_number='%s'" % (name, str(catalog_number))
        cursor.execute(subject_query)
        topic_resp = dictfetchall(cursor)

        topics = []
        for topic in topic_resp:
            topic_name = topic['catalog_topic']
            if topic_name != None:
                topics.append(topic_name)
        return topics

    except Exception as error:
        print(error)
        return None


# Queries grades
def _query_grades(cursor, instructor_id, grade_id):
    try:
        if instructor_id:
            grade_query = "SELECT * FROM \"Grade\" WHERE instructor_id=%s" % (str(instructor_id))
        elif grade_id:
            grade_query = "SELECT * FROM \"Grade\" WHERE id=%s" % (str(grade_id))
        else:
            return None

        cursor.execute(grade_query)
        resp = dictfetchall(cursor)
        # filters null grades
        grades = []
        for grade in resp:
            if grade['A'] != None:
                grades.append(grade)
        return grades

    except Exception as error:
        print(error)
        return None


def _query_subject_evaluations_avg(cursor, subject):
    try:
        if subject:
            subject_id_query = "SELECT id FROM \"Subject\" WHERE name=%s" % (subject)
        else:
            return None

        cursor.execute(subject_id_query)
        resp = dictfetchall(cursor)
        # filters null grades
        subject_evaluation_avg = []
        for subject_id in resp:
            evaluation_id_query = "SELECT evaluation_id FROM \"Course\" WHERE subject_id=%s" % (subject_id)
            cursor.execute(evaluation_id_query)
            evaluation_ids = dictfetchall(cursor)
            for evaluation_id in evaluation_ids:
                eval_resp = _query_evaluations(cursor, evaluation_id)
                subject_evaluation_avg.append(eval_resp)

    except Exception as error:
        print(error)
        return None




# Queries evaluations by instructor_id or instructor_id and course_id
def _query_evaluations(cursor, instructor_id, evaluation_id):
    try:
        if instructor_id:
            evaluation_query = "SELECT * FROM \"Evaluation\" WHERE instructor_id=%s" % (str(instructor_id))
        elif evaluation_id:
            evaluation_query = "SELECT * FROM \"Evaluation\" WHERE id=%s" % (str(evaluation_id))
        else:
            return None

        cursor.execute(evaluation_query)
        evaluation_resp = dictfetchall(cursor)

        for index, evaluation in enumerate(evaluation_resp):
            for column in evaluation:
                if column[0] == 'Q':
                    evaluation_resp[index][column] = _query_evaluation_score(cursor, evaluation[column])
        return evaluation_resp


    except Exception as error:
        print(error)
        return None


# Queries evaluation score
def _query_evaluation_score(cursor, evaluation_score_id):
    try:
        if evaluation_score_id:
            evaluation_score_query = "SELECT * FROM \"EvaluationScore\" WHERE id=%s" % (str(evaluation_score_id))
        else:
            return None

        cursor.execute(evaluation_score_query)
        return dictfetchone(cursor)

    except Exception as error:
        print(error)
        return None


def _query_professor_subjects_and_courses(cursor, instructor_id, section=None, semester=None):
    resp = {}
    # Queries courses
    course_resp = _query_course(cursor, None, instructor_id, section, semester)
    if course_resp is None:
        resp["courses"] = resp['subjects'] = []
        return resp
    resp['courses'] = course_resp

    # Queries all unique subjects from various courses
    subjects = []
    subject_ids = set([course['subject_id'] for course in course_resp])
    for subject_id in subject_ids:
        subjects.append(_query_subject_by_id(cursor, subject_id))
    resp['subjects'] = subjects
    return resp


def _query_all_professors(cursor):
    try:
        instructors_query = "SELECT id, first_name, last_name FROM \"Instructor\""
        cursor.execute(instructors_query)
        return dictfetchall(cursor)

    except Exception as error:
        print(error)
        return None

def _query_all_subjects(cursor):
    try:
        subjects_query = "SELECT id, name, catalog_number, catalog_topic FROM \"Subject\""
        cursor.execute(subjects_query)
        return dictfetchall(cursor)

    except Exception as error:
        print(error)
        return None
