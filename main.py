import json

from flask import Flask
from flask import render_template, request, url_for, flash, redirect
from formencode import variabledecode
from flask_table import Table, Col
# from flask_datepicker import datepicker
from werkzeug.exceptions import abort
import common
import time


app = Flask(__name__)
app.config['SECRET_KEY'] = 'my secret key'


@app.route('/', methods=('GET', 'POST'))
def index():
    if request.method == 'POST':
        # postvars = variabledecode.variable_decode(request.form, dict_char='_')
        if 'dt_start' in request.form:
            common.select_year, common.select_month, common.select_day = request.form['dt_start'].split('-')
            common.select_year = int(common.select_year)
            common.select_month = int(common.select_month)
            common.select_day = int(common.select_day)
            common.select_type = request.form['type_history']
        # return render_template("index.html")
        # return redirect(url_for('index'))
        pass
    if common.select_year is None:
        common.select_year = time.gmtime().tm_year
        common.select_month = time.gmtime().tm_mon
        common.select_day = time.gmtime().tm_mday
    if common.select_type == 'Год':
        result = common.load_month(common.select_month, common.select_year)
    else:
        result = common.load_year(common.select_year)
    if result is not None:
        st_date = str(common.select_year) + '-' + str(common.select_month).rjust(2, '0') + '-' + \
                  str(common.select_day).rjust(2, '0')
        datas = common.make_answer(result)
        return render_template("index.html", datas=datas, st_date=st_date, type_history=common.select_type)


@app.route('/create', methods=('GET', 'POST'))
def create():
    if request.method == 'POST':
        money = request.form['money']
        comment = request.form['comment']
        dt = request.form['dt']
        cat_id = request.form['cat_id']

        if not money:
            flash('Money is required!')
        else:
            # conn = get_db_connection()
            # conn.execute('INSERT INTO posts (title, content) VALUES (?, ?)',
            #              (title, content))
            # conn.commit()
            # conn.close()
            return redirect(url_for('index'))
    return render_template("create.html")


@app.route('/category')
def category():
    answer, result, status_result = common.send_rest('v1/objects/family/categor')
    if result:
        answer = json.loads(answer)
        categories = answer['values']
        return render_template("categories.html", title="Категории расходов", categories=categories)


common.make_start()
app.run(port=common.OWN_PORT, host=common.OWN_HOST, debug=True)
