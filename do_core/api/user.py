import logging
import requests
import json
from flask import request, Response
from flask_restplus import Resource, fields
from do_core.api.api import api
from do_core.userAuthentication import UserAuthentication
from do_core.exception import wrongRequest, unauthorizedRequest, UserNotFound

login_user = api.namespace('login', description = 'Login Resource')
login_user_model = api.model('Login', {
    'username': fields.String(required = True, description = 'Username',  type = 'string'),
    'password': fields.String(required = True, description = 'Password',  type = 'string') })
@login_user.route('', methods=['POST'])
@api.doc(responses={404: 'User Not Found'})
class UserAuth(Resource):

    @login_user.expect(login_user_model)
    @login_user.response(200, 'Login Successfully.')
    @login_user.response(400, 'Bad Request.')
    @login_user.response(409, 'Validation Error.')
    @login_user.response(401, 'Unauthorized.')
    @login_user.response(500, 'Internal Error.')
    def post(self):
        """
        Given the credentials it returns the token associated to that user
        Perform the login
        """

        try:
            credentials = json.loads(request.data.decode())
            token = UserAuthentication().authenticateUserFromCredentials(credentials)
            resp_token = Response(response=token, status=200, mimetype="application/token")
            return resp_token

        except wrongRequest as err:
            logging.exception(err)
            return ("Bad Request", 400)
        except (unauthorizedRequest, UserNotFound) as err:
            if request.headers.get("X-Auth-User") is not None:
                logging.debug("Unauthorized access attempt from user " + request.headers.get("X-Auth-User"))
            logging.debug(err.message)
            return ("Unauthorized", 401)
        except requests.HTTPError as err:
            logging.exception(err)
            return (str(err), 500)
        except requests.ConnectionError as err:
            logging.exception(err)
            return (str(err), 500)
        except Exception as err:
            logging.exception(err)
            return ("Contact the admin " + str(err), 500)