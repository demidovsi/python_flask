import json
import requests
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

select_year = None
select_month = None
select_day = None
select_type = 'Месяц'


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
    # if not token and (dir != 'GET'):
    #     return 'Не получен токен для работы', False, None
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
            dat = {"dt": data['1'], "money": st_money, "comment": data['3'], "category": st, "id": data["8"]}
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


def load_year(year):
    dt_beg = str(year-1) + '-1-1'
    dt_end = str(year) + '-1-1'
    params = "'" + dt_beg + "','" + dt_end + "'"
    txt = 'v1/function/' + SCHEMA_NAME + '/p_history_rashod_year?text=' + params
    data, result, status_result = send_rest(txt)
    if result:
        return json.loads(data)
