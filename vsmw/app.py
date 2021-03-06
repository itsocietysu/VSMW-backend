import concurrent.futures as ftr
import json
import logging
import os
import re
from collections import OrderedDict
import time

import falcon
from falcon_multipart.middleware import MultipartMiddleware

from sqlalchemy import func
from vsmw import utils
from vsmw.db import DBConnection
from vsmw.serve_swagger import SpecServer
from vsmw.utils import obj_to_json, getIntPathParam, guess_response_type, date_time_string, admin_access_type_required,\
fulfill_images, getPathParam

from vsmw.Entities.EntityBase import EntityBase
from vsmw.Entities.EntitySession import EntitySession
from vsmw.Entities.EntityUser import EntityUser
from vsmw.Entities.EntityVote import EntityVote
from vsmw.Entities.EntityCurrentSession import EntityCurrentSession

from vsmw.auth import auth

from beaker.cache import CacheManager
from beaker.util import parse_cache_config_options

cache_opts = {
    'cache.type': 'memory',
    'cache.lock_dir': './lock'
}

cache = CacheManager(**parse_cache_config_options(cache_opts))

def httpDefault(**request_handler_args):
    req = request_handler_args['req']
    resp = request_handler_args['resp']

    path = req.path
    src_path = path
    path = path.replace(baseURL, '.')

    if os.path.isdir(path):
        for index in "index.html", "index.htm", "test-search.html":
            index = os.path.join(path + '/', index)
            if os.path.exists(index):
                path = index
                break
        else:
            return None

    if path.endswith('swagger.json'):
        path = path.replace('swagger.json', 'swagger_temp.json')

    ctype = guess_response_type(path)

    try:
        with open(path, 'rb') as f:
            resp.status = falcon.HTTP_200

            fs = os.fstat(f.fileno())
            length = fs[6]

            buffer = f.read()
            if path.endswith('index.html'):
                str = buffer.decode()
                str = str.replace('127.0.0.1:4201', server_host)
                buffer = str.encode()
                length = len(buffer)

    except IOError:
        resp.status = falcon.HTTP_404
        return

    resp.set_header("Content-type", ctype)
    resp.set_header("Content-Length", length)
    resp.set_header("Last-Modified", date_time_string(fs.st_mtime))
    resp.set_header("Access-Control-Allow-Origin", "*")
    resp.set_header("Path", path)
    resp.body = buffer


def getVersion(**request_handler_args):
    resp = request_handler_args['resp']
    resp.status = falcon.HTTP_200
    with open("VERSION") as f:
        resp.body = obj_to_json({"version": f.read()[0:-1]})


@cache.cache('get_session_cached_stats', expire=1)
def get_cached_stats(id, type):
    return EntityVote.stats(id, type)


def get_stats_by_id(**request_handler_args):
    resp = request_handler_args['resp']

    id = getIntPathParam('id', **request_handler_args)
    entity = get_session_objects(id)
    obj_dict = []

    if len(entity):
        stats = get_cached_stats(id, entity[0]["type"])

        obj_dict = entity[0]
        obj_dict.update({'stats': stats})
        obj_dict = [obj_dict]

    resp.body = obj_to_json(obj_dict)
    resp.status = falcon.HTTP_200

@admin_access_type_required
def all_session(**request_handler_args):
    resp = request_handler_args['resp']

    resp.body = obj_to_json([o.to_dict() for o in fulfill_images(base_name, EntitySession.get().all())])
    resp.status = falcon.HTTP_200


@cache.cache('get_current_session_group', expire=3600)
def get_current_session_id():
    return [_.curr_id for _ in EntityCurrentSession.get().all()]


@cache.cache('get_current_session_group_object', expire=3600)
def get_current_session_object():
    res = []
    for _ in EntityCurrentSession.get().all():
        res.extend(get_session_objects(_.curr_id))

    return res


def current_session(**request_handler_args):
    resp = request_handler_args['resp']

    resp.body = obj_to_json(get_current_session_id())
    resp.status = falcon.HTTP_200


def current_session_object(**request_handler_args):
    resp = request_handler_args['resp']

    resp.body = obj_to_json(get_current_session_object())
    resp.status = falcon.HTTP_200


@admin_access_type_required
def set_session(**request_handler_args):
    resp = request_handler_args['resp']
    try:
        value = getIntPathParam('id', **request_handler_args)
        EntityCurrentSession.update_from_params({'curr_id': value})
        cache.invalidate(get_current_session_id, 'get_current_session_group')
        cache.invalidate(get_current_session_object, 'get_current_session_group_object')
        resp.body = obj_to_json(get_current_session_id())
        resp.status = falcon.HTTP_200
        return None
    except Exception as e:
        resp.body = obj_to_json({'message': str(e)})
        resp.status = falcon.HTTP_400
        return None


@admin_access_type_required
def create_session(**request_handler_args):
    req = request_handler_args['req']
    resp = request_handler_args['resp']

    try:
        params = {}
        for _ in req.params.keys():
            if _ == 'image':
                params[_] = req.get_param(_).file.read()
            else:
                params[_] = req.get_param(_)

        id = EntitySession.add_from_params(params)

        if id:
            resp.body = obj_to_json([o.to_dict() for o in fulfill_images(base_name, EntitySession.get().filter_by(vid=id).all())])
            resp.status = falcon.HTTP_200
            return
    except ValueError:
        resp.status = falcon.HTTP_405
        return

    resp.status = falcon.HTTP_501


@admin_access_type_required
def update_session(**request_handler_args):
    req = request_handler_args['req']
    resp = request_handler_args['resp']

    try:
        params = {}
        for _ in req.params.keys():
            if _ == 'image':
                params[_] = req.get_param(_).file.read()
            else:
                params[_] = req.get_param(_)

        id = EntitySession.update_from_params(params)

        if id:
            cache.invalidate(get_session_objects, 'get_session_func', id)
            cache.invalidate(get_current_session_object, 'get_current_session_group_object')
            resp.body = obj_to_json(get_session_objects(id))

            resp.status = falcon.HTTP_200
            return
    except ValueError:
        resp.status = falcon.HTTP_405
        return

    resp.status = falcon.HTTP_501


@admin_access_type_required
def delete_session(**request_handler_args):
    resp = request_handler_args['resp']

    id = getIntPathParam("id", **request_handler_args)

    if id is not None:
        try:
            EntitySession.delete(id)
        except FileNotFoundError:
            resp.status = falcon.HTTP_404
            return

        object = EntitySession.get().filter_by(vid=id).all()
        if not len(object):
            resp.status = falcon.HTTP_200
            cache.invalidate(get_session_objects, 'get_session_func', id)
            return

    resp.status = falcon.HTTP_400


@admin_access_type_required
def reset_session(**request_handler_args):
    resp = request_handler_args['resp']

    id = getIntPathParam("id", **request_handler_args)

    if id is not None:
        try:
            with DBConnection() as db_session:
                fp = db_session.db.query(EntityVote).filter_by(session=id).all()
                db_session.db.query(EntityVote).filter_by(session=id).delete()
                db_session.db.commit()

            resp.status = falcon.HTTP_200
            cache.invalidate(get_session_objects, 'get_session_func', id)
            for _ in fp:
                cache.invalidate(get_vote_objects, 'get_vote_func', id, _.user)
            return

        except FileNotFoundError:
            resp.status = falcon.HTTP_404
            return

    resp.status = falcon.HTTP_400


@cache.cache('get_session_func', expire=3600)
def get_session_objects(id):
    return [o.to_dict() for o in fulfill_images(base_name, EntitySession.get().filter_by(vid=id).all())]


def get_session(**request_handler_args):
    resp = request_handler_args['resp']

    id = getIntPathParam("id", **request_handler_args)
    if id:
        resp.body = obj_to_json(get_session_objects(id))
        resp.status = falcon.HTTP_200
        return

    resp.status = falcon.HTTP_400

def create_fingerprint(**request_handler_args):
    resp = request_handler_args['resp']

    try:
        fingerprint = getIntPathParam("fingerprint", **request_handler_args)
        id = EntityUser(fingerprint).add()

        if id:
            resp.body = obj_to_json([o.to_dict() for o in EntityUser.get().filter_by(vid=id).all()])
            resp.status = falcon.HTTP_200
            return
    except ValueError:
        resp.status = falcon.HTTP_405
        return

    resp.status = falcon.HTTP_501


@cache.cache('get_vote_func', expire=3600)
def get_vote_objects(session, fingerprint):
    return [o.to_dict() for o in EntityVote.get().filter_by(session=session, user=str(fingerprint)).all()]


def get_vote(**request_handler_args):
    resp = request_handler_args['resp']

    session     = getIntPathParam("session", **request_handler_args)
    fingerprint = getPathParam("fingerprint", **request_handler_args)
    if id:
        resp.body = obj_to_json(get_vote_objects(session, fingerprint))
        resp.status = falcon.HTTP_200
        return

    resp.status = falcon.HTTP_400


def create_vote(**request_handler_args):
    req = request_handler_args['req']
    resp = request_handler_args['resp']

    params = json.loads(req.stream.read().decode('utf-8'))

    curr_sess = 0
    if 'fingerprint' in params and 'value' in params and 'session' in params:
        try:
            curr_sessions = get_current_session_id()
            curr_sess = curr_sessions[0] if len(curr_sessions) else -1
            if curr_sess != params['session']:
                raise Exception('Only current session allowed')

            id = EntityVote(curr_sess, params['fingerprint'], params['value']).add()

            if id:
                cache.invalidate(get_vote_objects, 'get_vote_func', curr_sess, params['fingerprint'])
        except:
            resp.body = obj_to_json([])
            resp.status = falcon.HTTP_404

        resp.body = obj_to_json(get_vote_objects(curr_sess, params['fingerprint']))
        resp.status = falcon.HTTP_200
        return


def parse_plan(**request_handler_args):
    resp = request_handler_args['resp']

    id = getIntPathParam("id", **request_handler_args)
    if id:
        obj = OrderedDict([('vid', str(id)), ('image', base_name + '/images/parsed_plan' + str(id) + '.png')])
        resp.body = obj_to_json(obj)
        resp.status = falcon.HTTP_200
        time.sleep(4)
        return

    resp.status = falcon.HTTP_400


# End of game feature set functions
# ---------------------------------

operation_handlers = {
    # Session
    'get_stats_by_id':          [get_stats_by_id],
    'all_session':              [all_session],
    'create_session':           [create_session],
    'update_session':           [update_session],
    'delete_session':           [delete_session],
    'reset_session':            [reset_session],
    'get_session':              [get_session],
    'set_session':              [set_session],
    'current_session':          [current_session],
    'current_session_object':   [current_session_object],
    'parse_plan':               [parse_plan],

    # User
    'create_fingerprint': [create_fingerprint],

    # Vote
    'get_vote':           [get_vote],
    'create_vote':        [create_vote],
    # Default
    'getVersion':           [getVersion],
    'httpDefault':          [httpDefault]
}

class CORS(object):
    def process_response(self, req, resp, resource, params):
        origin = req.get_header('Origin')
        if origin:
            resp.set_header('Access-Control-Allow-Origin', origin)
            resp.set_header('Access-Control-Max-Age', '100')
            resp.set_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS, PUT, DELETE')
            resp.set_header('Access-Control-Allow-Credentials', 'true')

            acrh = req.get_header('Access-Control-Request-Headers')
            if acrh:
                resp.set_header('Access-Control-Allow-Headers', acrh)


class Auth(object):
    def process_request(self, req, resp):
        req.context['access_type'] = ''

        if re.match('(/each/version|'
                     '/each/settings/urls|'
                     '/each/images|'
                     '/each/ui|'
                     '/each/swagger\.json|'
                     '/each/swagger-temp\.json|'
                     '/each/swagger-ui).*', req.relative_uri):
            return

        if req.method == 'OPTIONS':
            return # pre-flight requests don't require authentication

        ################################################### WARNING!

        token = None
        try:
            if req.auth:
                token = req.auth.split(" ")[1].strip()
            else:
                token = req.params.get('access_token')
        except:
            return

        error = 'Authorization required.'
        if token:
            error, acc_type, user_email, user_id, user_name = auth.Validate(
                cfg['oidc']['each_oauth2']['check_token_url'],
                token
            )

            if not error:
                req.context['user_email'] = user_email
                req.context['user_id'] = user_id
                req.context['user_name'] = user_name
                req.context['access_type'] = acc_type

                return # passed access token is valid

        return


logging.getLogger().setLevel(logging.DEBUG)
args = utils.RegisterLaunchArguments()

cfgPath = args.cfgpath
profile = args.profile

# configure
with open(cfgPath) as f:
    cfg = utils.GetAuthProfile(json.load(f), profile, args)
    DBConnection.configure(**cfg['each_db'])
    if 'oidc' in cfg:
        cfg_oidc = cfg['oidc']

# wsgi_app = api = falcon.API(middleware=[CORS(), Auth(), MultipartMiddleware()])
wsgi_app = api = falcon.API(middleware=[CORS(), MultipartMiddleware()])

server = SpecServer(operation_handlers=operation_handlers)

if 'server_host' in cfg:
    with open('swagger.json') as f:
        swagger_json = json.loads(f.read(), object_pairs_hook=OrderedDict)

    server_host = cfg['server_host']
    base_name = server_host
    swagger_json['host'] = server_host

    baseURL = '/each'
    if 'basePath' in swagger_json:
        baseURL = swagger_json['basePath']

    EntityBase.host = server_host + baseURL
    json_string = json.dumps(swagger_json)

    with open('swagger_temp.json', 'wt') as f:
        f.write(json_string)

with open('swagger_temp.json') as f:
    server.load_spec_swagger(f.read())

#   os.remove('swagger_temp.json')

api.add_sink(server, r'/')
