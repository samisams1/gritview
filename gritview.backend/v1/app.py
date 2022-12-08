import datetime
import json
from django.http import JsonResponse, HttpResponse
from rest_framework.decorators import api_view
from v1.authentication import handle_user_registration, handle_user_login, handle_user_logout
from v1.review import create_review, update_review, read_review, read_all_reviews, delete_review
from v1.views import get_professor_course, get_professor, get_course, get_all_subjects_search, \
    get_all_professors_search, verfiy_user_auth, get_recent_reviews, track_selection, get_trending_searches, \
    get_unapproved_reviews, approve_reviews

ADMIN_TOKEN = ">>B6GmjA$%4]^^%z9Lx%X4f3?b<<"

# example request: http://127.0.0.1:5000/course?course=CMSC202
# example request: http://127.0.0.1:5000/professor?professor=Jeremy Dixon&course=CMSC202&semester=Spring 2019
@api_view(["GET"])
def professor(request):
    professor_name = request.GET.get('professor', None)
    professor_id = request.GET.get('profId', None)
    course_name = request.GET.get('course', None)
    topic = request.GET.get('topic', None)
    semester = request.GET.get('semester', None)
    section = request.GET.get('section', None)
    all = request.GET.get('all', None)

    if course_name == 'null': course_name = None
    if semester == 'null': semester = None
    if section == 'null': section = None
    if topic == 'null': topic = None
    if professor_id == 'null': professor_id = None

    if all != None:
        response = get_all_professors_search()
        return JsonResponse(response)
    if professor_name == None:
        msg = {"message": "Invalid request: specify all required parameters."}
        return JsonResponse(msg)
    elif course_name != None:
        response = get_professor_course(professor_name, professor_id, course_name, topic, semester, section)
        return JsonResponse(response)
    else:
        response = get_professor(professor_name, professor_id)
        return JsonResponse(response)


# example request: http://127.0.0.1:5000/course?course=CMSC202
@api_view(["GET"])
def course(request):
    course_name = request.GET.get('course', None)
    semester = request.GET.get('semester', None)
    topic = request.GET.get('topic', None)
    all = request.GET.get('all', None)
    if semester == 'null': semester = None
    if topic == 'null': topic = None

    if all:
        response = get_all_subjects_search()
        return JsonResponse(response)
    if course_name == None:
        msg = {"message": "Invalid request: specify all required parameters."}
        return JsonResponse(msg)
    response = get_course(course_name, topic, semester)
    return JsonResponse(response)


@api_view(["POST"])
def login(request):
    body_data = json.loads(request.body.decode('utf-8'))
    username = body_data.get('username', None)
    password = body_data.get('password', None)

    if not username or not password:
        msg = {"message": "Invalid request: specify all required parameters."}
        return JsonResponse(msg)

    response = handle_user_login(username.lower(), password.encode("utf-8"))
    return JsonResponse(response)


@api_view(["POST"])
def signup(request):
    body_data = json.loads(request.body.decode('utf-8'))
    username = body_data.get('username', None)
    password = body_data.get('password', None)
    email = body_data.get('email', None)
    if email == 'null': email = None

    if not username or not password:
        msg = {"message": "Invalid request: specify all required parameters."}
        return JsonResponse(msg)

    response = handle_user_registration(username.lower(), password.encode("utf-8"), email)
    return JsonResponse(response)


@api_view(["POST"])
def logout(request):
    body_data = json.loads(request.body.decode('utf-8'))
    username = body_data.get('username', None)
    token = body_data.get('token', None)

    if not username or not token:
        msg = {"message": "Invalid request: specify all required parameters."}
        return JsonResponse(msg)

    response = handle_user_logout(username.lower(), token)
    return JsonResponse(response)


# @api_view(['GET', 'POST', 'PATCH', 'DELETE'])
@api_view(['GET', 'POST'])
def review(request):
    CREATE = "POST"
    READ = "GET"
    UPDATE = "PATCH"
    DELETE = "DELETE"

    recent_reviews = request.GET.get('recent', None)
    if recent_reviews is not None:
        response = get_recent_reviews()
        return JsonResponse(response)

    body_data = json.loads(request.body)
    instructor_id = body_data.get('instructor_id', None)
    subject_id = body_data.get('subject_id', None)
    faculty_id = body_data.get('faculty_id', None)

    if request.method == READ:
        # response = read_review(instructor_id, subject_id)
        response = read_all_reviews()
        print(response)
        return JsonResponse(response)

    # verify Token with user
    token = body_data.get('token', None)
    username = body_data.get('username', None)
    if token is None or username is None:
        msg = {'message': 'Authentication Failed'}
        return JsonResponse(msg)
    if not verfiy_user_auth(username, token):
        msg = {'message': 'Authentication Failed'}
        return JsonResponse(msg)

    user_id = body_data.get('user_id', None)
    review_id = body_data.get('review_id', None)

    if request.method == CREATE or request.method == UPDATE:
        body = body_data.get('body', None)
        rating = body_data.get('rating', None)
        grade = body_data.get('grade', None)
        timestamp = datetime.datetime.utcnow()
        if request.method == CREATE:
            response = create_review(body, rating, grade, instructor_id, faculty_id, subject_id, user_id, timestamp)
            return JsonResponse(response)
        if request.method == UPDATE:
            return None  # not available for v1
            response = update_review(body, rating, grade, review_id, user_id, timestamp)
            return JsonResponse(response)
    elif request.method == DELETE:
        return None # not available for v1
        response = delete_review(review_id, user_id)
        return JsonResponse(response)
    else:
        msg = {"message": "Invalid method"}
        return JsonResponse(msg)


@api_view(["GET", "POST"])
def review_approval(request):
    if request.GET.get('token', None) != ADMIN_TOKEN:
        msg = {"message": "Auth Failed"}
        return JsonResponse(msg)
    if request.method == "GET":
        response = get_unapproved_reviews()
        return JsonResponse(response)
    elif request.method == "POST":
        body = json.loads(request.body)
        review_ids = body['review_ids']
        value = body['value']
        response = approve_reviews(review_ids, value)
        return JsonResponse(response)


@api_view(["GET"])
def trending(request):
    response = get_trending_searches()
    return JsonResponse(response)


@api_view(["POST"])
def track(request):
    body_data = json.loads(request.body)
    instructor_id = body_data.get('instructor_id', None)
    subject_id = body_data.get('subject_id', None)
    if instructor_id is None and subject_id is None:
        msg = {"message": "Invalid track state request"}
        return JsonResponse(msg)
    timestamp = datetime.datetime.utcnow()
    response = track_selection(instructor_id, subject_id, timestamp)
    return JsonResponse(response)

@api_view(["GET"])
def landing():
    return JsonResponse({'Welcome to Gritview.io': '200'})
