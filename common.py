import datetime
import json
import requests
import time
import calendar
from requests.exceptions import HTTPError
from flask import session
import base64


SCHEMA_NAME = 'test'
INFO_CODE = 'nsi'
URL = None
USER_DB = None
PASSWORD_DB = None
OWN_HOST = '127.0.0.1'
OWN_PORT = 8000
kirill = 'Kirill!981'

rashod_id = None
categories = list()

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
    login(USER_DB, PASSWORD_DB)


def login(e_mail, password):
    result = False
    txt_z = {"login": e_mail, "password": password, "rememberMe": True}
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
                    session['token'] = js["accessToken"]
                if "expires" in js:
                    session['expires'] = time.mktime(time.strptime(js["expires"], '%Y-%m-%d %H:%M:%S'))
                if 'lang' in js:
                    session['app_lang'] = js['lang']
                if 'role' in js:
                    session['user_role'] = js['role']
            else:
                session['token'] = None
                session['expires'] = 0
                return txt, result
        except Exception as err:
            txt = f'Error occurred: : {err}'
    return txt, result


def send_rest(mes, directive="GET", params=None, lang='', token_user=None):
    js = {}
    if token_user is not None:
        js['token'] = token_user
    else:
        js['token'] = session['token']  # токен при login
    if lang == '':
        lang = session['app_lang']
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
    answer, result, status_result = send_rest('v1/objects/family/categor', token_user='', lang='en')
    if result:
        answer = json.loads(answer)
        categories = answer['values']


def clear_current():
    session['left'] = None
    session['right'] = None
    session['current_month'] = None
    session['current_year'] = None
    session['current_day'] = None


def get_current(request):
    if 'dt_start' in request.form:
        session['select_year'], session['select_month'], session['select_day'] = request.form['dt_start'].split('-')
        session['select_year'] = int(session['select_year'])
        session['select_month'] = int(session['select_month'])
        session['select_day'] = int(session['select_day'])
    if 'type_history' in request.form:
        session['select_type'] = request.form['type_history']
    if 'select_month' in request.form:
        session['select_month'] = request.form['select_month']
    if 'select_name_month' in request.form:
        session['select_name_month'] = request.form['select_name_month']
    if 'year' in request.form:
        session['year'] = int(request.form['year'])
    session['left'] = request.form.get('left')
    session['right'] = request.form.get('right')
    session['current_month'] = request.form.get('current_month')
    session['current_year'] = request.form.get('current_year')
    session['current_day'] = request.form.get('current_day')


def get_data():
    global months
    if 'select_year' not in session:
        session['select_year'] = time.gmtime().tm_year
        session['select_month'] = time.gmtime().tm_mon
        session['select_day'] = time.gmtime().tm_mday
    if session['select_type'] == 'Год':
        if session['left']:
            session['year'] = session['year'] - 1
        if session['right']:
            session['year'] = session['year'] + 1
        if session['current_year']:
            session['year'] = time.gmtime().tm_year
        return load_year(session['year'])
    elif session['select_type'] == 'Месяц':
        month = months.index(session['select_name_month']) + 1
        if session['left']:
            session['year'], month = calc_month(session['year'], month, -1)
        if session['right']:
            session['year'], month = calc_month(session['year'], month, 1)
        if session['current_month']:
            session['year'] = time.gmtime().tm_year
            month = time.gmtime().tm_mon
        session['select_name_month'] = months[month - 1]
        return load_month(month, session['year'])
    else:
        if session['left']:
            session['select_year'], session['select_month'], session['select_day'] = \
                calc_day(session['select_year'], session['select_month'], session['select_day'], -1)
        if session['right']:
            session['select_year'], session['select_month'], session['select_day'] = \
                calc_day(session['select_year'], session['select_month'], session['select_day'], 1)
        if session['current_day']:
            session['select_year'] = time.gmtime().tm_year
            session['select_month'] = time.gmtime().tm_mon
            session['select_day'] = time.gmtime().tm_mday
        return load_day(session['select_day'], session['select_month'], session['select_year'])


def prepare_summary():
    mas_structure = list()
    count = 0
    summa_money = 0
    moneys = []
    mas_data = list()
    result = get_data()
    if result is not None:
        if session['select_category_name'] != '':
            guid = None
            for data in result:
                if data['6'] == 1 and data['1'] == session['select_category_name']:
                    guid = data['4']
                    break
            if guid is not None:
                for data in result:
                    if data['6'] == 2 and data['5'] == guid:
                        data['2'] = "%.2f" % data['2']
                        mas_structure.append(data)

        for data in result:
            if data['6'] == 1:
                if data['2'] is not None:
                    data['2'] = round(data['2'], 2)
                mas_data.append(data)
        count = 0
        if session['select_type'] != 'Сутки':
            if session['select_type'] == 'Месяц':
                count = calendar.monthrange(session['year'], months.index(session['select_name_month']) + 1)[1]
            else:
                count = 12
            # подготовим массив колонок для суммирования
            for data in mas_data:
                for i in range(count):
                    data[str(i + 9)] = 0
            # расчет (суммирование) по колонкам выходной таблицы
            for data in result:
                if data['6'] == 1:
                    continue
                for i in range(len(mas_data)):
                    if data['0'] != mas_data[i]['0']:  # не совпадают категории расходов
                        continue
                    for j in range(count):  # цикл по количеству дней или месяцев
                        ind = str(9 + j)
                        try:
                            if data[ind] is not None:
                                mas_data[i][ind] = round(mas_data[i][ind] + data[ind], 2)
                        except Exception as err:
                            print(ind, count, session['select_name_month'], f"{err}")
            # заменим float на str
            for data in mas_data:
                for i in range(count):
                    ind = str(i + 9)
                    if data[ind] == 0:
                        data[ind] = ""
                    else:
                        data[ind] = str(round(data[ind], 2))
        # строка footer
        moneys = [0] * count
        for data in mas_data:
            for i in range(count):

                value = data[str(i + 9)]
                if value is not None and value != '':
                    moneys[i] = moneys[i] + float(value)
        for i in range(count):
            if moneys[i] == 0:
                moneys[i] = ''
            else:
                moneys[i] = "%.0f" % moneys[i]
        for data in mas_data:
            if data['2'] is not None and data['2'] != '':
                summa_money += data['2']
    return count, mas_data, moneys, summa_money, mas_structure


def init_session():
    if 'select_type' not in session:
        session['select_type'] = 'Месяц'
    if 'select_name_month' not in session:
        session['select_name_month'] = 'январь'
    if 'year' not in session:
        session['year'] = time.gmtime().tm_year
    if 'select_category_name' not in session:
        session['select_category_name'] = ''
    if 'current_year' not in session:
        session['current_year']= None
    if 'current_month' not in session:
        session['current_month']= None
    if 'current_day' not in session:
        session['current_day']= None
    if 'current_day' not in session:
        session['current_day'] = None
    if 'current_day' not in session:
        session['current_day'] = None
    if 'select_month' not in session:
        session['select_month'] = time.gmtime().tm_mon
    if 'select_day' not in session:
        session['select_day'] = time.gmtime().tm_mday
    if 'token' not in session:
        session['token'] = ''
    if 'app_lang' not in session:
        session['app_lang'] = 'ru'
    if 'user_role' not in session:
        session['user_role'] = ''
    if 'expires' not in session:
        session['expires'] = 0
    if 'login' not in session:
        session['login'] = None


def decode(key, enc):
    dec = []
    enc = base64.urlsafe_b64decode(enc).decode()
    for i in range(len(enc)):
        key_c = key[i % len(key)]
        dec_c = chr((256 + ord(enc[i]) - ord(key_c)) % 256)
        dec.append(dec_c)
    return "".join(dec)


def is_directive_correct(directive):
    return directive in session['login']