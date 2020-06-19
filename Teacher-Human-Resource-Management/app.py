from flask import Flask, render_template, request, session, logging, url_for, redirect, flash
from datetime import timedelta
from flask_mysqldb import MySQL
import yaml
import os

app = Flask(__name__)
app.send_file_max_age_default = timedelta(seconds=1)

# Configure db
db = yaml.safe_load(open('db.yaml'))
app.config['MYSQL_HOST'] = db['mysql_host']
app.config['MYSQL_USER'] = db['mysql_user']
app.config['MYSQL_PASSWORD'] = db['mysql_password']
app.config['MYSQL_DB'] = db['mysql_db']
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SECRET_KEY'] = os.urandom(24)

mysql = MySQL(app)

teacher_id = ''
teacher_name = ''
teacher_title = ''
teacher_tel = ''
teacher_address = ''
teacher_email = ''
teacher_college_id = ''
dept_id_list = []


@app.route('/')
def home():
    return render_template("home.html")


@app.route("/register", methods=['GET', 'POST'])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirm = request.form.get("confirm")

        if password == confirm:
            cur = mysql.connection.cursor()
            cur.execute("INSERT INTO sysuser(username, password) VALUES(%s, %s)", (username, password))
            mysql.connection.commit()
            cur.close()
            flash("you are registered successfully", 'success')
            return redirect(url_for('login'))
        else:
            flash("password does not match", "danger")
            return render_template("register.html")

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        cur = mysql.connection.cursor()
        sql_select_username_query = "SELECT username FROM sysuser WHERE username = %s"
        sql_select_password_query = "SELECT password FROM sysuser WHERE username = %s"
        cur.execute(sql_select_username_query, (username,))
        usernamedata = cur.fetchone()
        cur.execute(sql_select_password_query, (username,))
        passwordata = cur.fetchone()
        mysql.connection.commit()
        cur.close()
        if usernamedata is None:
            flash("No username", "danger")
            return render_template("login.html")
        else:
            for pass_data in passwordata:
                if str(pass_data) == str(password) and username != "admin":
                    session["log"] = True
                    session["all"] = True
                    session["search"] = True
                    flash("You successfully logged in as a normal user", "success")
                    return redirect(url_for('teacher'))
                elif str(pass_data) == str(password) and username == "admin":
                    session["log"] = True
                    session["admin"] = True
                    session["all"] = True
                    session["search"] = True
                    flash("You successfully logged in as an administrator", "success")
                    return redirect(url_for('teacher'))
                else:
                    flash("incorrect password", "danger")
                    return render_template("login.html")

    return render_template("login.html")


# teacher
@app.route("/teacher")
def teacher():
    cur = mysql.connection.cursor()
    sql_select_teacher_query = "SELECT * FROM teacher"
    cur.execute(sql_select_teacher_query)
    teahcerlist = cur.fetchall()
    sql_show_field_teacher_query = "SHOW FIELDS FROM teacher"
    cur.execute(sql_show_field_teacher_query)
    labels = cur.fetchall()
    labels = [l[0] for l in labels]
    cur.close()
    session['all'] = True

    return render_template("teacher.html", labels=labels, teahcerlist=teahcerlist)


# add step one
@app.route("/add_teacher_step_one", methods=['POST'])
def add():
    if request.method == 'POST':
        global teacher_id
        global teacher_name
        global teacher_title
        global teacher_tel
        global teacher_address
        global teacher_email
        global teacher_college_id

        global dept_id_list

        teacher_id = request.form['teacher_id']
        teacher_name = request.form['teacher_name']
        teacher_title = request.form['teacher_title']
        teacher_tel = request.form['teacher_tel']
        teacher_address = request.form['teacher_address']
        teacher_email = request.form['teacher_email']

        teacher_college_id = request.form['college']

        # print(teacher_college_id)

        cur = mysql.connection.cursor()
        sql_select_teacher_query = "SELECT * FROM teacher"
        cur.execute(sql_select_teacher_query)
        teahcerlist = cur.fetchall()
        sql_show_field_teacher_query = "SHOW FIELDS FROM teacher"
        cur.execute(sql_show_field_teacher_query)
        labels = cur.fetchall()
        labels = [l[0] for l in labels]
        cur.close()

        # 到数据库department表中找，完成二级互联的功能
        cur = mysql.connection.cursor()
        cur.execute("SELECT dept_id FROM department WHERE father_id = %s", (teacher_college_id,))
        dept_id = cur.fetchall()
        cur.execute("SELECT dept_name FROM department WHERE father_id = %s", (teacher_college_id,))
        dept_name = cur.fetchall()
        mysql.connection.commit()
        cur.close()
        dept_id_list = [int(i[0]) for i in dept_id]
        dept_name_list = [j[0] for j in dept_name]
        dept_dic = dict(zip(dept_id_list, dept_name_list))
        print(dept_dic)
        flash("Complete Add step one", "success")
        return render_template("success_add.html", labels=labels, teahcerlist=teahcerlist, dept_dic=dept_dic)


# add step two
@app.route("/add_teacher_step_two", methods=['POST'])
def add_two():
    if request.method == 'POST':
        teacher_dept_id = request.form['teacher_dept_id']
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO teacher(teacher_id, teacher_name, teacher_dept_id, teacher_title, teacher_tel, teacher_address, teacher_email) VALUES(%s, %s, %s, %s, %s, %s, %s)", (teacher_id, teacher_name, teacher_dept_id, teacher_title, teacher_tel, teacher_address, teacher_email))
        mysql.connection.commit()
        cur.close()

        cur = mysql.connection.cursor()
        sql_select_teacher_query = "SELECT * FROM teacher"
        cur.execute(sql_select_teacher_query)
        teahcerlist = cur.fetchall()
        sql_show_field_teacher_query = "SHOW FIELDS FROM teacher"
        cur.execute(sql_show_field_teacher_query)
        labels = cur.fetchall()
        labels = [l[0] for l in labels]
        cur.close()
        flash("New Teacher Information added Successfully", "success")
        return render_template("teacher.html", labels=labels, teahcerlist=teahcerlist)


# fuzzy search
@app.route("/search", methods=['POST'])
def search():
    if request.method == 'POST':
        searched_name = request.form['searched_name']
        sql_search_like = "SELECT * FROM teacher WHERE teacher_name LIKE '%%%%%s%%%%'" % searched_name
        cur = mysql.connection.cursor()
        result = cur.execute(sql_search_like)
        if result > 0:
            session['search'] = True
            session['all'] = False
            search_result = cur.fetchall()
            sql_show_field_teacher_query = "SHOW FIELDS FROM teacher"
            cur.execute(sql_show_field_teacher_query)
            labels = cur.fetchall()
            labels = [l[0] for l in labels]
            cur.close()
            return render_template("teacher.html", labels=labels, search_result=search_result)
        else:
            flash("No results found", "danger")
            search_result = None
            return render_template("teacher.html", search_result=search_result)


# logout
@app.route("/logout")
def logout():
    session.clear()
    flash("Your are now logged out", "success")
    return redirect(url_for('login'))


# edit teacher
@app.route("/edit/<teacher_id>")
def get_teacher(teacher_id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM teacher WHERE teacher_id = %s", (teacher_id,))
    data = cur.fetchall()
    cur.close()
    return render_template('edit.html', information=data[0])


# change password
@app.route("/change_password", methods=["GET", "POST"])
def change_password():
    if request.method == 'POST':
        new_password = request.form['new_password']
        cur = mysql.connection.cursor()
        cur.execute("UPDATE sysuser SET password = %s WHERE id = 1", (new_password,))
        mysql.connection.commit()
        cur.close()
        flash("Your password was changed successfully", "success")
    return render_template('change_password.html')


@app.route('/update/<teacher_id>', methods=['POST'])
def update_teacher(teacher_id):
    if request.method == 'POST':
        teacher_name = request.form['teacher_name']
        teacher_dept_id = request.form['teacher_dept_id']
        teacher_title = request.form['teacher_title']
        teacher_tel = request.form['teacher_tel']
        teacher_address = request.form['teacher_address']
        teacher_email = request.form['teacher_email']
        cur = mysql.connection.cursor()
        cur.execute("""
        UPDATE teacher
        SET teacher_name = %s,
            teacher_dept_id = %s,
            teacher_title = %s,
            teacher_tel = %s,
            teacher_address = %s,
            teacher_email = %s
        WHERE teacher_id = %s
        """, (teacher_name, teacher_dept_id, teacher_title, teacher_tel, teacher_address, teacher_email, teacher_id))
        mysql.connection.commit()
        flash('Teacher Information Updated Successfully', 'success')
        return redirect(url_for('teacher'))


# delete teacher
@app.route("/delete/<string:teacher_id>")
def delete_teacher(teacher_id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM teacher WHERE teacher_id = {0}".format(teacher_id))
    mysql.connection.commit()
    cur.close()
    flash('Teacher Removed Successfully', 'success')
    return redirect(url_for("teacher"))


if __name__ == '__main__':
    app.run(debug=True)
