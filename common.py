import datetime
import json
import requests
import time
from requests.exceptions import HTTPError


SCHEMA_NAME = 'test'
INFO_CODE = 'nsi'
URL = None
USER_DB = None
PASSWORD_DB = None
OWN_HOST = '127.0.0.1'
OWN_PORT = 8000
app_lang = 'ru'
token = ''
expires = None
user_role = None
rashod_id = None
categories = list()

select_year = None
select_month = None
select_day = None
select_type = 'Сутки'
select_name_month = 'январь'
left = None
right = None
current_month = None
current_year = None
current_day = None
year = 2023
months = ['январь', 'февраль', 'март', 'апрель', 'май', 'июнь', 'июль', 'август', 'сентябрь', 'октябрь', 'ноябрь',
          'декабрь']


def make_start():
    global URL, USER_DB, PASSWORD_DB, SCHEMA_NAME, INFO_CODE, OWN_HOST, OWN_PORT
    f = open('config.json', 'r', encoding='utf-8')
    with f:
        data = f.read()
        data = json.loads(data)
        if 'url' in data:
            URL = data['url']
        if 'user_name' in data:
            USER_DB = data['user_name']
        if 'password' in data:
            PASSWORD_DB = data['password']
        if 'schema_name' in data:
            SCHEMA_NAME = data['schema_name']
        if 'info_code' in data:
            INFO_CODE = data['info_code']
        if 'OwnHost' in data and OWN_HOST is None:
            OWN_HOST = data['OwnHost']
        if 'OwnPort' in data and OWN_PORT is None:
            OWN_PORT = data['OwnPort']


def login():
    global token, expires, app_lang, user_role
    txt = ''
    result = False
    txt_z = {"login": USER_DB, "password": PASSWORD_DB, "rememberMe": True}
    try:
        headers = {"Accept": "application/json"}
        response = requests.request(
            'POST', URL + 'v1/login', headers=headers,
            json={"params": txt_z}
            )
    except HTTPError as err:
        txt = f'HTTP error occurred: {err}'
    except Exception as err:
        txt = f'Other error occurred: : {err}'
    else:
        try:
            txt = response.text
            result = response.ok
            if result:
                js = json.loads(txt)
                if "accessToken" in js:
                    token = js["accessToken"]
                if "expires" in js:
                    expires = time.mktime(time.strptime(js["expires"], '%Y-%m-%d %H:%M:%S'))
                if 'lang' in js:
                    app_lang = js['lang']
                if 'role' in js:
                    user_role = js['role']
            else:
                return txt, result
        except Exception as err:
            txt = f'Error occurred: : {err}'
    return txt, result


def send_rest(mes, directive="GET", params=None, lang='', token_user=None):
    js = {}
    if token_user is not None:
        js['token'] = token_user
    else:
        js['token'] = token  # токен при login
    if lang == '':
        lang = app_lang
    if directive == 'GET' and 'lang=' not in mes:
        if '?' in mes:
            mes = mes + '&lang=' + lang
        else:
            mes = mes + '?lang=' + lang
    else:
        js['lang'] = lang   # код языка пользователя
    if params:
        if type(params) is not str:
            params = json.dumps(params, ensure_ascii=False)
        js['params'] = params  # дополнительно заданные параметры
    try:
        headers = {"Accept": "application/json"}
        response = requests.request(directive, URL + mes.replace(' ', '+'), headers=headers, json=js)
    except HTTPError as err:
        txt = f'HTTP error occurred: {err}'
        return txt, False, None
    except Exception as err:
        txt = f'Other error occurred: {err}'
        return txt, False, None
    else:
        return response.text, response.ok, '<' + str(response.status_code) + '> - ' + response.reason


def define_rashod_id():
    global rashod_id
    data, result, status_result = send_rest("v1/MDM/objects?usl=app_code='" + SCHEMA_NAME + "' and code='rashod'")
    if result:
        data = json.loads(data)
        try:
            rashod_id = data[0]["id"]
        except Exception:
            pass


def make_answer(result):
    datas = list()
    cat = list()
    for data in result:
        if not data['8']:
            cat.append({"id": data["0"], "name": data["1"]})
    for data in result:
        if data['8']:
            st = ''
            for ct in cat:
                if ct['id'] == data['0']:
                    st = ct['name']
                    break
            if data['2']:
                st_money = round(data['2'], 2)
            else:
                st_money = ''
            dat = {"dt": data['1'], "money": st_money, "comment": translateFromBase(data['3']), "category": st,
                   "id": data["8"]}
            datas.append(dat)
    return datas


def load_month(month, year):
    dt_beg = str(year) + '-' + str(month) + '-1'
    if month == 12:
        month = 1
        year += 1
    else:
        month += 1
    dt_end = str(year) + '-' + str(month) + '-1'
    params = "'" + dt_beg + "','" + dt_end + "'"
    txt = 'v1/function/' + SCHEMA_NAME + '/p_history_rashod_month?text=' + params
    data, result, status_result = send_rest(txt)
    if result:
        return json.loads(data)


def load_day(day, month, year):
    dt = datetime.date(year, month, day) + datetime.timedelta(days=1)
    dt_beg = str(year) + '-' + str(month) + '-' + str(day)
    dt_end = str(dt.year) + '-' + str(dt.month) + '-' + str(dt.day)
    params = "'" + dt_beg + "','" + dt_end + "'"
    txt = 'v1/function/' + SCHEMA_NAME + '/p_history_rashod?text=' + params
    data, result, status_result = send_rest(txt)
    if result:
        return json.loads(data)


def load_year(year):
    dt_beg = str(year) + '-1-1'
    dt_end = str(year + 1) + '-1-1'
    params = "'" + dt_beg + "','" + dt_end + "'"
    txt = 'v1/function/' + SCHEMA_NAME + '/p_history_rashod_year?text=' + params
    data, result, status_result = send_rest(txt)
    if result:
        return json.loads(data)


def calc_month(year, month, delta):
    month += delta
    if month < 1:
        month += 12
        year -= 1
    if month > 12:
        month -= 12
        year += 1
    return year, month


def calc_day(year, month, day, delta):
    dt = datetime.date(year, month, day) + datetime.timedelta(days=delta)
    return dt.year, dt.month, dt.day


def translateFromBase(st):
    st = st.replace('~LF~', '\n').replace('~A~', '(').replace('~B~', ')').replace('~a1~', '@')
    st = st.replace('~a2~', ',').replace('~a3~', '=').replace('~a4~', '"').replace('~a5~', "'")
    st = st.replace('~a6~', ':').replace('~b1~', '/')
    return st


def translateToBase(st):
    st = st.replace('\n', '~LF~').replace('(', '~A~').replace(')', '~B~').replace('@', '~a1~')
    st = st.replace(',', '~a2~').replace('=', '~a3~').replace('"', '~a4~').replace("'", '~a5~')
    st = st.replace(':', '~a6~').replace('/', '~b1~')
    return st


def load_categories():
    global categories
    answer, result, status_result = send_rest('v1/objects/family/categor')
    if result:
        answer = json.loads(answer)
        categories = answer['values']


def clear_current():
    global left, right, current_month, current_year, current_day
    left = None
    right = None
    current_month = None
    current_year = None
    current_day = None


def get_current(request):
    global select_type, select_year, select_month, select_day, select_name_month, year, left, right, current_month, \
        current_year, current_day
    if 'dt_start' in request.form:
        select_year, select_month, select_day = request.form['dt_start'].split('-')
        select_year = int(select_year)
        select_month = int(select_month)
        select_day = int(select_day)
    if 'type_history' in request.form:
        select_type = request.form['type_history']
    if 'select_month' in request.form:
        select_name_month = request.form['select_month']
    if 'select_name_month' in request.form:
        select_name_month = request.form['select_name_month']
    if 'year' in request.form:
        year = int(request.form['year'])
    left = request.form.get('left')
    right = request.form.get('right')
    current_month = request.form.get('current_month')
    current_year = request.form.get('current_year')
    current_day = request.form.get('current_day')


def get_data():
    global select_year, year, select_name_month, select_month, select_day, months
    if select_year is None:
        select_year = time.gmtime().tm_year
        select_month = time.gmtime().tm_mon
        select_day = time.gmtime().tm_mday

    if select_type == 'Год':
        if left:
            year = year - 1
        if right:
            year = year + 1
        if current_year:
            year = time.gmtime().tm_year
        return load_year(year)
    elif select_type == 'Месяц':
        month = months.index(select_name_month) + 1
        if left:
            year, month = calc_month(year, month, -1)
        if right:
            year, month = calc_month(year, month, 1)
        if current_month:
            year = time.gmtime().tm_year
            month = time.gmtime().tm_mon
        select_name_month = months[month - 1]
        return load_month(month, year)
    else:
        if left:
            select_year, select_month, select_day = \
                calc_day(select_year, select_month, select_day, -1)
        if right:
            select_year, select_month, select_day = \
                calc_day(select_year, select_month, select_day, 1)
        if current_day:
            select_year = time.gmtime().tm_year
            select_month = time.gmtime().tm_mon
            select_day = time.gmtime().tm_mday
        return load_day(select_day, select_month, select_year)