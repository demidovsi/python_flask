import json
from flask import Flask
from flask import render_template, request, url_for, flash, redirect
import common
import time


app = Flask(__name__)
app.config['SECRET_KEY'] = 'my secret key'
months = ['январь', 'февраль', 'март', 'апрель', 'май', 'июнь', 'июль', 'август', 'сентябрь', 'октябрь', 'ноябрь',
          'декабрь']


@app.route('/', methods=('GET', 'POST'))
def index():
    left = None
    right = None
    current_month = None
    current_year = None
    current_day = None
    if request.method == 'POST':
        if 'dt_start' in request.form:
            common.select_year, common.select_month, common.select_day = request.form['dt_start'].split('-')
            common.select_year = int(common.select_year)
            common.select_month = int(common.select_month)
            common.select_day = int(common.select_day)
        if 'type_history' in request.form:
            common.select_type = request.form['type_history']
        if 'select_month' in request.form:
            common.select_name_month = request.form['select_month']
        if 'select_name_month' in request.form:
            common.select_name_month = request.form['select_name_month']
        if 'year' in request.form:
            common.year = int(request.form['year'])
        left = request.form.get('left')
        right = request.form.get('right')
        current_month = request.form.get('current_month')
        current_year = request.form.get('current_year')
        current_day = request.form.get('current_day')
        for key in request.form.keys():
            if 'delete' in key:
                st2, st2 = key.split('delete')
                print('Надо удалить расход с id= ' + st2)
    if common.select_year is None:
        common.select_year = time.gmtime().tm_year
        common.select_month = time.gmtime().tm_mon
        common.select_day = time.gmtime().tm_mday

    if common.select_type == 'Год':
        if left:
            common.year = common.year - 1
        if right:
            common.year = common.year + 1
        if current_year:
            common.year = time.gmtime().tm_year
        result = common.load_year(common.year)
    elif common.select_type == 'Месяц':
        month = months.index(common.select_name_month) + 1
        if left:
            common.year, month = common.calc_month(common.year, month, -1)
        if right:
            common.year, month = common.calc_month(common.year, month, 1)
        if current_month:
            common.year = time.gmtime().tm_year
            month = time.gmtime().tm_mon
        common.select_name_month = months[month - 1]
        result = common.load_month(month, common.year)
    else:
        if left:
            common.select_year, common.select_month, common.select_day = \
                common.calc_day(common.select_year, common.select_month, common.select_day, -1)
        if right:
            common.select_year, common.select_month, common.select_day = \
                common.calc_day(common.select_year, common.select_month, common.select_day, 1)
        if current_day:
            common.select_year = time.gmtime().tm_year
            common.select_month = time.gmtime().tm_mon
            common.select_day = time.gmtime().tm_mday
        result = common.load_day(common.select_day, common.select_month, common.select_year)

    if result is not None:
        st_date = str(common.select_year) + '-' + str(common.select_month).rjust(2, '0') + '-' + \
                  str(common.select_day).rjust(2, '0')
        datas = common.make_answer(result)
        moneys = 0
        for data in datas:
            try:
                moneys = moneys + data['money']
            except:
                print('error money', data)
        return render_template(
            "index.html", datas=datas, st_date=st_date, type_history=common.select_type, months=months,
            select_name_month=common.select_name_month, year=common.year, count_datas=len(datas),
            moneys=round(moneys, 2))


@app.route('/create/', methods=('GET', 'POST'))
def create():
    st_date = str(time.gmtime().tm_year) + '-' + str(time.gmtime().tm_mon).rjust(2, '0') + '-' + \
              str(time.gmtime().tm_mday).rjust(2, '0')
    answer, result, status_result = common.send_rest('v1/objects/family/categor')
    if result:
        answer = json.loads(answer)
        categories = answer['values']

    if request.method == 'POST':
        money = request.form['money']
        comment = request.form['comment']
        dt = request.form['dt']
        year, month, day = dt.split('-')
        dt = str(year) + '-' + str(month) + '-' + str(day)
        cat_id = request.form['select_category']
        for category in categories:
            if category['sh_name'] == cat_id:
                cat_id = category['id']
                break

        if not money or float(money) == 0:
            flash('Money is required!')
        elif type(cat_id) == str:
            flash('Тип расхода is required!')
        else:
            values = {'id': 0, 'cat_id': cat_id, 'money': money}
            values['dt'] = "'" + dt + "'"
            values['comment'] = common.translateToBase(comment)
            params = dict()
            params["schema_name"] = common.SCHEMA_NAME
            params["object_code"] = 'rashod'
            params["values"] = values
            answer, result = common.login()
            if not result:
                flash(answer)
            else:
                answer, result, status_result = common.send_rest('v1/objects', 'PUT', params=params)
                if not result:
                    flash(answer)
                else:
                    return redirect(url_for('index'))
    return render_template("create.html", st_date=st_date, categories=categories, title='Создание нового расхода',
                           id=None, select_category=None, money=0)


@app.route('/correct/<int:id>/', methods=('GET', 'POST'))
def correct(id):
    categories = list()
    answer, result, status_result = common.send_rest('v1/objects/family/categor')
    if result:
        answer = json.loads(answer)
        categories = answer['values']
    if request.method == 'POST' and 'dt' in request.form and request.form['dt']:
        money = request.form['money']
        comment = request.form['comment']
        dt = request.form['dt']
        year, month, day = dt.split('-')
        dt = str(year) + '-' + str(month) + '-' + str(day)
        cat_id = request.form['select_category']
        for category in categories:
            if category['sh_name'] == cat_id:
                cat_id = category['id']
                break

        if not money or float(money) == 0:
            flash('Money is required!')
        elif type(cat_id) == str:
            flash('Тип расхода is required!')
        else:
            values = {'id': 0, 'cat_id': cat_id, 'money': money, 'id': id}
            values['dt'] = "'" + dt + "'"
            values['comment'] = common.translateToBase(comment)
            params = dict()
            params["schema_name"] = common.SCHEMA_NAME
            params["object_code"] = 'rashod'
            params["values"] = values
            answer, result = common.login()
            if not result:
                flash(answer)
            else:
                answer, result, status_result = common.send_rest('v1/objects', 'PUT', params=params)
                if not result:
                    flash(answer)
                else:
                    return redirect(url_for('index'))
    else:
        answer, result, status_result = common.send_rest('v1/object/family/rashod/' + str(id))
        if result:
            answer = json.loads(answer)[0]
            comment = answer['comment']
            select_category = answer['cat_id_reference']['sh_name']
            if 'money' in answer:
                money = answer['money']
            else:
                money = None
            dt, t = answer['dt'].split(' ')
            year, month, day = dt.split('-')
            dt = str(year) + '-' + str(month) + '-' + str(day)
    return render_template("create.html", categories=categories, title='Коррекция расхода с ID= ' + str(id), id=id,
                           comment=comment, select_category=select_category, money=money, st_date=dt)


@app.route('/category/')
def category():
    answer, result, status_result = common.send_rest('v1/objects/family/categor')
    if result:
        answer = json.loads(answer)
        categories = answer['values']
        return render_template("categories.html", title="Категории расходов", categories=categories)


common.make_start()
common.define_rashod_id()
app.run(port=common.OWN_PORT, host=common.OWN_HOST, debug=True)
