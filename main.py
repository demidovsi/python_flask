import json
from flask import Flask
from flask import render_template, request, url_for, flash, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from config import Config
import calendar
import common
import time


app = Flask(__name__)
app.config['SECRET_KEY'] = 'my secret key'
# db = SQLAlchemy(app)
# migrate = Migrate(app, db)
# login = LoginManager(app)
# login.login_view = 'login'


@app.route('/', methods=('GET', 'POST'))
def index():
    common.clear_current()
    if request.method == 'POST':
        common.get_current(request)
        for key in request.form.keys():
            if 'delete' in key:
                st2, st2 = key.split('delete')
                print('Надо удалить расход с id= ' + st2)
        for key in request.form.keys():
            if 'correct' in key:
                st2, st2 = key.split('correct')
                return redirect(f"correct/{st2}")

    result = common.get_data()
    if result is not None:
        st_date = str(common.select_year) + '-' + str(common.select_month).rjust(2, '0') + '-' + \
                  str(common.select_day).rjust(2, '0')
        datas = common.make_answer(result)
        moneys = 0
        for data in datas:
            try:
                moneys = moneys + data['money']
            except Exception as err:
                print('error money', f"{err}", data)
        return render_template(
            "index.html", datas=datas, st_date=st_date, type_history=common.select_type, months=common.months,
            select_name_month=common.select_name_month, year=common.year, count_datas=len(datas),
            moneys=round(moneys, 2))


@app.route('/create/', methods=('GET', 'POST'))
def create():
    st_date = str(time.gmtime().tm_year) + '-' + str(time.gmtime().tm_mon).rjust(2, '0') + '-' + \
              str(time.gmtime().tm_mday).rjust(2, '0')
    if request.method == 'POST':
        money = request.form['money']
        comment = request.form['comment']
        dt = request.form['dt']
        year, month, day = dt.split('-')
        dt = str(year) + '-' + str(month) + '-' + str(day)
        cat_id = request.form['select_category']
        for cat in common.categories:
            if cat['sh_name'] == cat_id:
                cat_id = cat['id']
                break

        if not money or float(money) == 0:
            flash('Money is required!')
        elif type(cat_id) == str:
            flash('Тип расхода is required!')
        else:
            values = dict()
            values["id"] = 0
            values["cat_id"] = cat_id
            values["money"] = money
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
                    if common.page_for_return is not None:
                        st = common.page_for_return
                        common.page_for_return = None
                        return redirect(st)
                    return redirect(url_for('index'))
    return render_template(
        "create.html", st_date=st_date, categories=common.categories, title='Создание нового расхода',
        id=None, select_category=None, money=0)


@app.route('/correct/<int:obj_id>/', methods=('GET', 'POST'))
def correct(obj_id):
    if request.method == 'POST' and 'dt' in request.form and request.form['dt']:
        money = request.form['money']
        comment = request.form['comment']
        dt = request.form['dt']
        cat_id = request.form['select_category']
        for cat in common.categories:
            if cat['sh_name'] == cat_id:
                cat_id = cat['id']
                break

        if not money or float(money) == 0:
            flash('Money is required!')
        elif type(cat_id) == str:
            flash('Тип расхода is required!')
        else:
            values = dict()
            values['cat_id'] = cat_id
            values['money'] = money
            values['id'] = obj_id
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
                    if common.page_for_return is not None:
                        st = common.page_for_return
                        common.page_for_return = None
                        return redirect(st)
                    year, month, day = dt.split('-')
                    common.select_type = 'Сутки'
                    common.select_year = int(year)
                    common.select_month = int(month)
                    common.select_day = int(day)
                    return redirect(url_for('index'))
    else:
        answer, result, status_result = common.send_rest('v1/object/family/rashod/' + str(obj_id))
        if result:
            answer = json.loads(answer)[0]
            comment = common.translateFromBase(answer['comment'])
            select_category = answer['cat_id_reference']['sh_name']
            if 'money' in answer:
                money = round(answer['money'], 2)
            else:
                money = None
            dt, t = answer['dt'].split(' ')
            return render_template(
                "create.html", categories=common.categories, title='Коррекция расхода с ID= ' + str(obj_id), id=obj_id,
                comment=comment, select_category=select_category, money=money, st_date=dt)


@app.route('/category/')
def category():
    return render_template("categories.html", title="Категории расходов", categories=common.categories)


@app.route('/summary/', methods=('GET', 'POST'))
def summary():
    common.clear_current()
    if request.method == 'POST':
        common.get_current(request)
        for key in request.form.keys():
            if 'correct' in key:
                st2, st2 = key.split('correct')
                common.page_for_return = '/summary/'
                return redirect("/correct/" + st2 +"/")
        for key in request.form.keys():
            if 'category_name_' in key:
                st2, common.select_category_name = key.split('category_name_')
    count, mas_data, moneys, summa_money, mas_structure = common.prepare_summary()
    st_date = str(common.select_year) + '-' + str(common.select_month).rjust(2, '0') + '-' + \
              str(common.select_day).rjust(2, '0')
    index = list()
    for i in range(count):
        index.append(str(i+9))
    return render_template(
        "summary.html", st_date=st_date, type_history=common.select_type, months=common.months,
        select_name_month=common.select_name_month, year=common.year, datas=mas_data, count_day=count,
        index=index, moneys=moneys, summa_money="%.0f" % summa_money, mas_structure=mas_structure,
        category_name=common.select_category_name)


common.make_start()
common.define_rashod_id()
common.load_categories()

app.run(port=common.OWN_PORT, host=common.OWN_HOST, debug=True)
