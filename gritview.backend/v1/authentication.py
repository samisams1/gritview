import datetime
import bcrypt
import jwt
from django.db import connection
from .models import dictfetchone

def encode_auth_token(username):
    """
    Generates the Auth Token
    :return: string
    """
    try:
        SECRET_KEY = 'a52489d4f4924dfdbc9dea7824f012e4'
        payload = {
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=0, seconds=60),
            'iat': datetime.datetime.utcnow(),
            'sub': username
        }
        return jwt.encode(
            payload,
            SECRET_KEY,
            algorithm='HS256'
        )
    except Exception as e:
        print(e)
        return None


# resource: https://pythonise.com/categories/python/python-password-hashing-bcrypt
# Registers a user in the database if requirements are met
# Test: http://127.0.0.1:5000/signup?username=user105&password=password2
def handle_user_registration(username, password, email):
    hashed_password = bcrypt.hashpw(password, bcrypt.gensalt(rounds=12)).decode('utf-8')
    try:
        cursor = connection.cursor()
        user_resp = "SELECT * FROM \"User\" WHERE username='%s'" % (username)
        cursor.execute(user_resp)
        user_resp = cursor.fetchone()

        email_resp = None
        if email is not None:
            email_query = "SELECT * FROM \"User\" WHERE email='%s'" % (email)
            cursor.execute(email_query)
            email_resp = cursor.fetchone()

        if user_resp is not None or email_resp is not None:
            return {
                'message': 'The username or email is already in use. Please try again with a different username or email.'}

        timestamp = datetime.datetime.utcnow()
        token = encode_auth_token(username).decode('UTF-8')
        add_user = "INSERT INTO \"User\" (username, email, password, token, date_created) VALUES(%s, %s, %s, %s, %s) RETURNING id;"
        cursor.execute(add_user, (username, email, hashed_password, token, timestamp))
        user_id_res = dictfetchone(cursor)
        connection.commit()
        return {'token': token, "user_id": user_id_res['id']}

    except Exception as error:
        print(error)
        return {'message': 'Error creating a user. Please try again!'}

    finally:
        cursor.close()


# Authenticates a user
# test : http://127.0.0.1:5000/signup?username=user103&password=password&email=email_3
def handle_user_login(username, password):
    try:
        cursor = connection.cursor()
        user_password_query = "SELECT * FROM \"User\" WHERE username='%s'" % (username)
        cursor.execute(user_password_query)
        user_resp = dictfetchone(cursor)

        if (user_resp is None):
            return {'message': 'User account does not exist'}

        hashed_password = user_resp['password'].encode("utf-8")

        if bcrypt.checkpw(password, hashed_password):
            token = encode_auth_token(username).decode('UTF-8')
            set_token = "Update \"User\" SET token='%s' WHERE username='%s'" % (token, username)
            cursor.execute(set_token)
            connection.commit()
            return {'token': token, "user_id": user_resp['id']}
        else:
            return {'message': 'Please Check your password and username again!!'}

    except Exception as error:
        print(error)
        return {'message': 'Error authenticating the user. Please try again!'}

    finally:
        cursor.close()


# Logs out a user
# test : http://127.0.0.1:5000/logout?username=<user>&token=<token>
def handle_user_logout(username, token):
    try:
        cursor = connection.cursor()
        user_password_query = "SELECT * FROM \"User\" WHERE username='%s'" % (username)
        cursor.execute(user_password_query)
        user_resp = dictfetchone(cursor)

        if user_resp is None:
            return None

        if token == user_resp['token']:
            remove_token = "Update \"User\" SET token=NULL WHERE username='%s'" % (username)
            cursor.execute(remove_token)
            connection.commit()
            return {'status': 'true'}

    except Exception as error:
        print(error)
        return None

    finally:
        cursor.close()
