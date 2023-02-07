import json
from flask import Flask
from flask import render_template, request, url_for, flash, redirect, session
import common
import time
import datetime
import os


app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(20).hex()
app.config['CSRF_ENABLED'] = True
app.permanent = True
app.permanent_session_lifetime = datetime.timedelta(hours=1)


@app.route('/', methods=('GET', 'POST'))
def index():
    common.init_session()
    if session['rights'] is None:
        return redirect('/login/')
    common.clear_current()
    if request.method == 'POST':
        common.get_current(request)
        for key in request.form.keys():
            if 'delete' in key:
                st2, st2 = key.split('delete')
                common.define_rashod_id()
                return redirect('/delete/'+st2+'/')
                # print('Надо удалить расход с id= ' + st2)
        for key in request.form.keys():
            if 'correct' in key:
                st2, st2 = key.split('correct')
                if 'page_history' in request.form:
                    session['page_history'] = request.form['page_history']
                return redirect(f"correct/{st2}")

    result, error = common.get_data()
    if result is not None:
        st_date = str(session['select_year']) + '-' + str(session['select_month']).rjust(2, '0') + '-' + \
                  str(session['select_day']).rjust(2, '0')
        datas = common.make_answer(result)
        moneys = 0
        for data in datas:
            try:
                moneys = moneys + data['money']
            except Exception as err:
                print('error money', f"{err}", data)
        if 'page_history' in session:
            page_history = session['page_history']
        else:
            page_history = 0
        session['page_history'] = 0
        return render_template(
            "index.html", datas=datas, st_date=st_date, type_history=session['select_type'], months=common.months,
            select_name_month=session['select_name_month'], year=session['year'], count_datas=len(datas),
            moneys=round(moneys, 2), page_history=int(page_history))
    else:
        error = error + ' Пользователь = ' + session['user_name']
        return error


@app.route('/create/', methods=('GET', 'POST'))
def create():
    common.init_session()
    if session['rights'] is None:
        return redirect('/login/')
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
            params["object_code"] = common.object_code
            params["values"] = values
            answer, result, status_result = common.send_rest('v1/objects', 'PUT', params=params)
            if not result:
                flash(answer)
            else:
                if 'page_for_return' in session and session['page_for_return'] is not None:
                    st = session['page_for_return']
                    session['page_for_return'] = None
                    return redirect(st)
                return redirect(url_for('index'))
    return render_template(
        "create.html", st_date=st_date, categories=common.categories, title='Создание нового расхода',
        id=None, select_category=None, money=0)


@app.route('/correct/<int:obj_id>/', methods=('GET', 'POST'))
def correct(obj_id):
    common.init_session()
    if session['rights'] is None:
        return redirect('/login/')
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
            params["object_code"] = common.object_code
            params["values"] = values
            answer, result, status_result = common.send_rest('v1/objects', 'PUT', params=params)
            if not result:
                flash(answer)
            else:
                if 'page_for_return' in session and session['page_for_return'] is not None:
                    st = session['page_for_return']
                    session['page_for_return'] = None
                    return redirect(st)
                # year, month, day = dt.split('-')
                # session['select_type'] = 'Сутки'
                # session['select_year'] = int(year)
                # session['select_month'] = int(month)
                # session['select_day'] = int(day)
                return redirect(url_for('index'))
    else:
        answer, result, status_result = common.send_rest('v1/object/family/' + common.object_code + '/' + str(obj_id))
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
    common.init_session()
    if session['rights'] is None:
        return redirect('/login/')
    return render_template("categories.html", title="Категории расходов", categories=common.categories)


@app.route('/summary/', methods=('GET', 'POST'))
def summary():
    common.init_session()
    if session['rights'] is None:
        return redirect('/login/')
    common.clear_current()
    if request.method == 'POST':
        common.get_current(request)
        for key in request.form.keys():
            if 'correct' in key:
                st2, st2 = key.split('correct')
                session['page_for_return'] = '/summary/'
                return redirect("/correct/" + st2 + "/")
        for key in request.form.keys():
            if 'category_name_' in key:
                st2, session['select_category_name'] = key.split('category_name_')
    count, mas_data, moneys, summa_money, mas_structure = common.prepare_summary()
    st_date = str(session['select_year']) + '-' + str(session['select_month']).rjust(2, '0') + '-' + \
        str(session['select_day']).rjust(2, '0')
    index_column = list()
    for i in range(count):
        index_column.append(str(i+9))
    if 'page_summary' in session:
        page_summary = session['page_summary']
    else:
        page_summary = 0
    session['page_summary'] = 0
    return render_template(
        "summary.html", st_date=st_date, type_history=session['select_type'], months=common.months,
        select_name_month=session['select_name_month'], year=session['year'], datas=mas_data, count_day=count,
        index=index_column, moneys=moneys, summa_money="%.0f" % summa_money, mas_structure=mas_structure,
        category_name=session['select_category_name'], page_summary=page_summary)


@app.route('/login/', methods=('GET', 'POST'))
def login():
    common.init_session()
    if request.method == 'POST':
        user_name = request.form.get('user_name')
        session['user_name'] = user_name
        password = request.form.get('password')
        txt, result = common.login(user_name, password)
        if not result:
            flash('Ошибка login = ' + txt)
            return render_template('login.html')
        token = common.decode(common.kirill, session['token'])
        token = json.loads(token)
        for key in token.keys():
            common.SCHEMA_NAME = key
            break
        session['rights'] = token[common.SCHEMA_NAME]

        if 'visible' not in session['rights']:
            flash(f'Для пользователя {user_name} нет доступа к базе данных')
            return render_template('login.html')
        return redirect('/')
    return render_template('login.html')


@app.route('/logout/', methods=('GET', 'POST'))
def logout():
    common.init_session()
    session['rights'] = None
    return redirect('/login/')


@app.route('/test/', methods=('GET', 'POST'))
def test():
    return render_template('test.html')
    # return redirect('/test/#openModal')


@app.route('/delete/<int:obj_id>/', methods=('GET', 'POST'))
def delete(obj_id):
    if request.method == 'POST':
        if 'page_for_return' in session and session['page_for_return'] is not None:
            st = session['page_for_return']
            session['page_for_return'] = None
            return redirect(st)
        return redirect(url_for('index'))

    return render_template("delete.html", obj_id=obj_id)


@app.route('/char/', methods=('GET', 'POST'))
def char():
    common.init_session()
    if session['rights'] is None:
        return redirect('/login/')
    common.clear_current()
    if request.method == 'POST':
        common.get_current(request)
        for key in request.form.keys():
            if 'correct' in key:
                st2, st2 = key.split('correct')
                session['page_for_return'] = '/summary/'
                return redirect("/correct/" + st2 + "/")
        for key in request.form.keys():
            if 'category_name_' in key:
                st2, session['select_category_name'] = key.split('category_name_')

    st_date = str(session['select_year']) + '-' + str(session['select_month']).rjust(2, '0') + '-' + \
        str(session['select_day']).rjust(2, '0')
    count, mas_data, moneys, summa_money, mas_structure = common.prepare_summary()

    x = list()
    y = list()
    for data in mas_data:
        if data['2'] is None:
            continue
        x.append(data['1'])
        y.append(float("%.2f" % (data['2'] / summa_money * 100)))
    return render_template(
        "char.html", st_date=st_date, type_history=session['select_type'], months=common.months,
        select_name_month=session['select_name_month'], year=session['year'], labels=x, values=y,
        legend='% Проценты к общей сумме расходов за период',
        summa_money=int(summa_money))


common.make_start()
common.load_categories()

app.run(port=common.OWN_PORT, host=common.OWN_HOST, debug=True)
