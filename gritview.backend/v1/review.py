from django.db import connection
from v1.models import _query_reviews, dictfetchall, _filter_reviews

# Test Value
# http://127.0.0.1:5000/createpost?title=This is the title &body=postman test&rating=5&instructor_id=1111&course_id=1111&user_id=2
def create_review(body, rating, grade, instructor_id, faculty_id, subject_id, user_id, timestamp):
    try:
        if not user_id or not instructor_id or not subject_id:
            return {'message': 'Specify all required parameters.'}

        if not body or not rating:
            return {'message': 'Specify all required parameters.'}

        cursor = connection.cursor()
        add_review = "INSERT INTO \"Review\" (body, rating, grade, subject_id, user_id, instructor_id, faculty_id, date_created, last_updated) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s);"
        cursor.execute(add_review,
                       (body, rating, grade, subject_id, user_id, instructor_id, faculty_id, timestamp, timestamp))
        connection.commit()

        print('instructor_id', instructor_id, faculty_id)

        # TODO: sends an email notification to gritview.io@gmail.com so review can be reviewd and approved.
        return {'message': 'Successfully posted'}

    except Exception as error:
        print(error)
        return {'message': 'Something went wrong'}

    finally:
        cursor.close()


def update_review(body, rating, grade, review_id, user_id, timestamp):
    try:
        cursor = connection.cursor()

        if not body or not rating or not review_id or not user_id:
            return {'message': 'Specify all required parameters.'}

        update_review = "UPDATE \"Review\" SET body=%s, rating=%s, grade=%s, last_updated=%s WHERE id=%s AND user_id=%s;"
        cursor.execute(update_review, (body, rating, grade, timestamp, review_id, user_id))
        connection.commit()
        return {"message": "Successfully Updated"}

    except Exception as error:
        print(error)
        return {"message": "Invalid request"}

    finally:
        cursor.close()


def delete_review(review_id, user_id):
    try:
        cursor = connection.cursor()

        if not review_id or not user_id:
            return {'message': 'Specify all required parameters.'}

        delete_review = "DELETE FROM \"Review\" WHERE id=%s and user_id=%s;"
        cursor.execute(delete_review, (review_id, user_id))
        connection.commit()
        return {'message': 'Successfully Deleted'}

    except Exception as error:
        print(error)
        return {'message': 'Something went wrong'}

    finally:
        cursor.close()


def read_all_reviews():
    try:
        cursor = connection.cursor()
        review_query = "SELECT * FROM \"Review\" ORDER BY last_updated asc"
        cursor.execute(review_query)
        review_resp = dictfetchall(cursor)

        return {'reviews': _filter_reviews(cursor, review_resp)}

    except Exception as error:
        print(error)
        return {'message': 'Something went wrong, please try again'}

    finally:
        cursor.close()


def read_review(instructor_id, subject_id):
    try:
        cursor = connection.cursor()
        review_resp = _query_reviews(cursor, instructor_id, subject_id)

        if review_resp is None:
            return {'message': 'Something went wrong, please try again'}

        return {'reviews': review_resp}

    except Exception as error:
        print(error)
        return {'message': 'Something went wrong, please try again'}

    finally:
        cursor.close()
