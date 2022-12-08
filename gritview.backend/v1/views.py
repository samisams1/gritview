from django.db import connection
from v1.utils import split_alphanumeric
from .models import dictfetchall, dictfetchone, _query_reviews, _query_professor, _query_course, _query_subject, \
    _query_grades, _query_evaluations, _query_professors_by_subject, _query_all_professors, _query_all_subjects, \
    _query_subject_topics, _query_semesters, _query_token,  _query_recent_reviews, _query_subjects_by_instructor

# Verifies user token - Authentication for user related tasks
def verfiy_user_auth(username, token):
    try:
        cursor = connection.cursor()
        token_resp = _query_token(cursor, username)
        if token_resp['token'] == token: return True
        return False

    except Exception as error:
        print(error)
        return {'message': 'Error querying results'}

    finally:
        if connection:
            cursor.close()


def get_recent_reviews():
    try:
        cursor = connection.cursor()
        recent_reviews_resp = _query_recent_reviews(cursor)
        if recent_reviews_resp is None:
            return None
        return {'reviews': recent_reviews_resp}

    except Exception as error:
        print(error)
        return {'message': 'Error querying results'}

    finally:
        cursor.close()


# returns all professors details that teach the course, and all of the grades and (subject & courses) available by semester/sections.
# PreConditions: req: course_name | optional: semester
# example request: http://127.0.0.1:5000/course?course=ENGL100
def get_course(course_name, topic=None, semester=None):
    try:
        cursor = connection.cursor()
        resp = {}

        # Parses course_name to (name, catalog_number)
        name_catalog_num = split_alphanumeric(course_name)
        if name_catalog_num is None:
            return None
        name, catalog_number = name_catalog_num

        # Queries Subject
        subject_resp = _query_subject(cursor, name, catalog_number, topic)
        if subject_resp is None:
            resp["subject"] = resp["reviews"] = resp["courses"] = resp["instructors"] = resp["grades"] = resp['topics'] \
                    = resp['semesters'] = []
            return resp
        resp['subject'] = subject_resp

        # Queries Topics
        topic_resp = _query_subject_topics(cursor, name, catalog_number)
        resp['topics'] = topic_resp

        # Queries reviews
        subject_id = subject_resp['id']
        review_resp = _query_reviews(cursor, None, subject_id)
        if review_resp is None:
            resp["reviews"] = resp["courses"] = resp["instructors"] = resp["grades"] = resp['semesters'] = []
        resp['reviews'] = review_resp

        # Queries semesters
        semester_resp = _query_semesters(cursor, subject_id, None)
        resp['semesters'] = semester_resp

        # Queries instructors
        instructors_resp = _query_professors_by_subject(cursor, subject_id, None)
        if instructors_resp == []:
            resp["courses"] = resp["instructors"] = resp["grades"] = resp['semesters'] = []
        # Queries review count for each instructor
        for instructor in instructors_resp:
            review_resp = _query_reviews(cursor, instructor["id"], None)
            if review_resp is None:
                instructor["review_count"] = 0
            else:
                instructor["review_count"] = len(review_resp)
        resp["instructors"] = instructors_resp

        # Queries grades
        grades = []
        enrollment = {}
        course_resp = _query_course(cursor, subject_id, None, None, semester)
        for course in course_resp:
            grade_id = course["grade_id"]
            semester = course["semester"]
            grade_resp = _query_grades(cursor, None, grade_id)
            if grade_resp is not None:
                # There is only grade per course_id
                grades.append([] if grade_resp == [] else grade_resp[0])
                total_enrolled = 0 if grade_resp == [] else grade_resp[0]['total_enrolled']
                if semester in enrollment:
                    enrollment[semester] += total_enrolled
                else:
                    enrollment[semester] = total_enrolled
        resp['enrollment'] = list(enrollment.items())[::-1]
        resp["grades"] = grades

        return resp

    except Exception as error:
        print(error)
        return {'message': 'Error querying results for %s' % (course_name)}

    finally:
        cursor.close()


# returns professor details, reviews, and all of the (subjects & courses) available by sections.
# PreConditions: req: professor_name | optional: none
# example request: http://127.0.0.1:5000/professor?professor=Shane Moritz
def get_professor(instructor_name, instructor_id):
    try:
        cursor = connection.cursor()
        resp = {}

        # Queries instructor
        instructor_resp = _query_professor(cursor, instructor_name, instructor_id)
        if instructor_resp is None:
            resp["reviews"] = resp["instructor"] = resp["grades"] = resp["subjects"] = resp["evaluations"] = resp[
                'semesters'] = []
            return resp

        # Queries reviews
        instructor_id = instructor_resp["id"]
        review_resp = _query_reviews(cursor, instructor_id, None)
        if review_resp is None:
            resp["reviews"] = resp["instructor"] = resp["grades"] = resp["subjects"] = resp["evaluations"] = resp[
                'semesters'] = []

        # Queries subjects
        subjects = _query_subjects_by_instructor(cursor, instructor_id)
        instructor_resp['subjects'] = subjects
        instructor_resp['semesters'] = []

        resp["instructor"] = instructor_resp
        resp['reviews'] = review_resp
        resp['enrollment'] = []

        # Queries grades
        grade_resp = _query_grades(cursor, instructor_id, None)
        if grade_resp == None: resp['grades'] = []
        else: resp['grades'] = grade_resp

        # Queries evaluations
        resp['evaluations'] = _query_evaluations(cursor, instructor_id, None)

        return resp


    except Exception as error:
        print(error)
        return {'message': 'Error querying results for %s' % (instructor_name)}

    finally:
        cursor.close()


# returns professor details, reviews, evaluations, and all of the grades and (subject & courses) available by sections.
# PreConditions: req: professor_name, course_name | optional: semester, section
# example request: http://127.0.0.1:5000/professor?professor=Shane Moritz&course=ENGL100
def get_professor_course(instructor_name, instructor_id, course_name, topic=None, semester=None, section=None):
    try:
        cursor = connection.cursor()
        resp = {}

        # Queries instructor details
        instructor_resp = _query_professor(cursor, instructor_name, instructor_id)
        if instructor_resp is None:
            resp["instructor"] = resp["subjects"] = resp["reviews"] = resp["grades"] = resp["subjects"] = resp["evaluations"] = resp[
                'semesters'] = []
            return resp

        # Queries subjects
        instructor_id = instructor_resp["id"]
        subjects = _query_subjects_by_instructor(cursor, instructor_id)
        instructor_resp['subjects'] = subjects
        instructor_resp['semesters'] = []

        # Parses course_name to name and catalog_number
        # ENGL100 -> ('ENGL', '100')
        name_catalog_num = split_alphanumeric(course_name)
        if name_catalog_num is None:
            resp["subject"] = resp["courses"] = resp["grades"] = resp["evaluations"] = resp['semesters'] = []
            return resp
        name, catalog_number = name_catalog_num

        # Queries Subject
        subject_resp = _query_subject(cursor, name, catalog_number, topic)
        if subject_resp == None:
            resp["subject"] = resp["courses"] = resp["grades"] = resp["evaluations"] = resp['semesters'] = []
            return resp
        resp['subject'] = subject_resp

        # Queries reviews
        subject_id = subject_resp['id']
        review_resp = _query_reviews(cursor, instructor_id, None)
        if review_resp is None:
            resp["reviews"] = resp["subject"] = resp["courses"] = resp["grades"] = resp["evaluations"] = resp[
                'semesters'] = []
        resp['reviews'] = review_resp

        # Queries semesters
        semester_resp = _query_semesters(cursor, subject_id, instructor_id)
        instructor_resp['semesters'] = semester_resp
        resp["instructor"] = instructor_resp
        resp['semesters'] = semester_resp

        # Queries Topics
        topic_resp = _query_subject_topics(cursor, name, catalog_number)
        resp['topics'] = topic_resp

        # Queries instructors (For Other instructors Teaching Section)
        instructors_resp = _query_professors_by_subject(cursor, subject_id, None)
        if instructors_resp is None:
            resp["instructor"] = resp["grades"] = []
            return resp
        # Queries review count for each instructor
        for instructor in instructors_resp:
            review_resp = _query_reviews(cursor, instructor["id"], None)
            if review_resp is None:
                instructor["review_count"] = 0
            else:
                instructor["review_count"] = len(review_resp)
        resp["instructors"] = instructors_resp

        # Queries grades and evaluations
        grades = []
        evaluations = []
        enrollment = {}
        course_resp = _query_course(cursor, subject_id, instructor_id, section, semester)
        for course in course_resp:
            grade_id = course["grade_id"]
            semester = course["semester"]
            grade_resp = _query_grades(cursor, None, grade_id)
            evaluation_resp = _query_evaluations(cursor, None, course['evaluation_id'])[0]
            evaluations.append(evaluation_resp)

            if grade_resp is not None:
                # There is only grade per course_id
                grades.append([] if grade_resp == [] else grade_resp[0])
                total_enrolled = (0 if grade_resp == [] else grade_resp[0]['total_enrolled'])
                if semester in enrollment:
                    enrollment[semester] += total_enrolled
                else:
                    enrollment[semester] = total_enrolled
        resp['enrollment'] = list(enrollment.items())[::-1]
        resp["grades"] = grades
        resp["evaluations"] = evaluations

        return resp

    except Exception as error:
        print(error)
        return {'message': 'Error querying results for %s and %s' % (instructor_name, course_name)}

    finally:
        cursor.close()


# Fetches 2 Top Professors
# Fetches 2 top Subjects & Professor@Subjects
# Fetches 2 top Professor@Subjects
def get_trending_searches():
    try:
        trending = []
        cursor = connection.cursor()
        def get_professor_details(instructor_id):
            resp = {}
            query_professor_name = "SELECT first_name, last_name FROM \"Instructor\" WHERE id=%s" % (instructor_id)
            cursor.execute(query_professor_name)
            professor_name_resp = dictfetchone(cursor)
            resp['instructor_name'] = professor_name_resp['first_name'] + " " + professor_name_resp['last_name']
            review_resp = _query_reviews(cursor, instructor_id, None)
            if review_resp is None: resp["review_count"] = 0
            else: resp["review_count"] = len(review_resp)
            return resp

        def get_subject_details(subject_id):
            resp = {}
            query_subject_name = "SELECT name, catalog_number, catalog_topic, credits FROM \"Subject\" WHERE id=%s" % (trend['subject_id'])
            cursor.execute(query_subject_name)
            subject = dictfetchone(cursor)
            if subject['catalog_topic'] is not None:
                resp['subject_name'] = subject['name'] + subject['catalog_number'] + ' - ' + subject['catalog_topic']
            else: resp['subject_name'] = subject['name'] + subject['catalog_number']
            resp['credits'] = subject['credits']
            return resp

        trend_professor_subject = """SELECT instructor_id, subject_id, count(*) as num FROM \"Analytics\"
        WHERE instructor_id IS NOT NULL AND subject_id IS NOT NULL
        AND date_created >= NOW() - '2 day'::INTERVAL
        GROUP BY instructor_id, subject_id
        ORDER BY num desc
        LIMIT 2;
        """
        cursor.execute(trend_professor_subject)
        resp = dictfetchall(cursor)
        for trend in resp:
            professor_details = get_professor_details(trend['instructor_id'])
            subject_details = get_subject_details(trend['subject_id'])
            trend['instructor_name'] = professor_details['instructor_name']
            trend['review_count'] = professor_details['review_count']
            trend['subject_name'] = subject_details['subject_name']
            trend['credits'] = subject_details['credits']
        trending += resp

        trend_professor = """
        SELECT instructor_id, count(*) as num FROM \"Analytics\"
        WHERE instructor_id IS NOT NULL AND subject_id IS NULL
        AND date_created >= NOW() - '2 day'::INTERVAL
        GROUP BY instructor_id
        ORDER BY num desc
        LIMIT 2;
        """
        cursor.execute(trend_professor)
        resp = dictfetchall(cursor)
        for trend in resp:
            professor_details = get_professor_details(trend['instructor_id'])
            trend['instructor_name'] = professor_details['instructor_name']
            trend['review_count'] = professor_details['review_count']
        trending += resp

        trend_subject = """
        SELECT subject_id, count(*) as num FROM \"Analytics\" 
        WHERE subject_id IS NOT NULL AND instructor_id IS NULL
        AND date_created >= NOW() - '2 day'::INTERVAL
        GROUP BY subject_id
        ORDER BY num desc
        LIMIT 2;
        """
        cursor.execute(trend_subject)
        resp = dictfetchall(cursor)
        for trend in resp:
            subject_details = get_subject_details(trend['subject_id'])
            trend['subject_name'] = subject_details['subject_name']
            trend['credits'] = subject_details['credits']
        trending += resp

        return {'trending': sorted(trending, key = lambda i: i['num'], reverse=True)}

    except Exception as error:
        print(error)
        return {'message': 'Error posting state'}

    finally:
        cursor.close()


def track_selection(instructor_id, subject_id, timestamp):
    try:
        cursor = connection.cursor()
        track_statement = "INSERT INTO \"Analytics\" (instructor_id, subject_id, date_created) VALUES(%s,%s,%s);"
        cursor.execute(track_statement, (instructor_id, subject_id, timestamp))
        connection.commit()
        return {'message': 'success'}

    except Exception as error:
        print(error)
        return {'message': 'Error posting state'}

    finally:
        cursor.close()


# Fetches 10 unapproved reviews
def get_unapproved_reviews():
    try:
        cursor = connection.cursor()
        unapproved_reviews = "SELECT id, body, rating, grade, date_created, user_id, approved  FROM \"Review\" WHERE approved=0 LIMIT 10;"
        cursor.execute(unapproved_reviews)
        return {'reviews': dictfetchall(cursor)}

    except Exception as error:
        print(error)
        return {'message': 'Error retrieving reviews'}

    finally:
        cursor.close()


# approves reviews based on list of reviews ids recieved from request
# if value is 1 approved, if -1 disapproved
def approve_reviews(reviews_ids, value):
    try:
        cursor = connection.cursor()
        update_review = "UPDATE \"Review\" SET approved=%s WHERE id=%s;"
        for reviewId in reviews_ids:
            cursor.execute(update_review, (value, reviewId))
            connection.commit()
        return {"message": "Successfully approved reviews"}

    except Exception as error:
        print(error)
        return {'message': 'Error approving reviews'}

    finally:
        cursor.close()

def get_all_professors_search():
    try:
        cursor = connection.cursor()
        resp = {}

        professors_resp = _query_all_professors(cursor)
        if professors_resp is None:
            return {"message": "No results"}

        for professor in professors_resp:
            full_name = professor['first_name'] + ' ' + professor['last_name']
            professor['full_name'] = full_name
        resp["professors"] = professors_resp
        return resp

    except Exception as error:
        print(error)
        return {'message': 'Error querying results'}

    finally:
        cursor.close()


def get_all_subjects_search():
    try:
        cursor = connection.cursor()
        resp = {}

        subjects_resp = _query_all_subjects(cursor)
        if subjects_resp is None:
            return {"message": "No results"}

        subjects = []
        for subject in subjects_resp:
            res = {}
            if subject['catalog_topic'] != None:
                res['topic'] = subject['catalog_topic']
            course_name = subject['name'] + subject['catalog_number']
            res['name'] = course_name
            subjects.append(res)
        resp["subjects"] = subjects
        return resp

    except Exception as error:
        print(error)
        return {'message': 'Error querying results'}

    finally:
        cursor.close()
