from flask import Flask, render_template, redirect, url_for, flash, request, abort
from flask_bs4 import Bootstrap
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, EmailField, SubmitField, SelectField, FileField
from wtforms.validators import DataRequired, Length
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy
import os
from flask_wtf.file import FileAllowed
from werkzeug.utils import secure_filename
from datetime import datetime
import shutil

# ustawienia aplikacji
app = Flask(__name__)
bootstrap = Bootstrap(app)
app.config['SECRET_KEY'] = 'kjhg67YHJKL:&*()YUI&*()'
bcrypt = Bcrypt(app)
app.config['UPLOAD_PATH'] = 'uploads'
app.config['UPLOAD_EXTENSIONS'] = ['.jpg', '.jpeg', '.png', '.txt']
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 #16MB

# ustawienia bazy danych
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'data/users.sqlite')
db = SQLAlchemy(app)

current_parent = ""
current_path = ""
# definicja tabeli w bazie
class Users(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    firstName = db.Column(db.String(20))
    lastName = db.Column(db.String(30))
    userMail = db.Column(db.String(50), unique=True)
    userPass = db.Column(db.String(50))
    userRole = db.Column(db.String(20))

    def is_authenticated(self):
        return True

class Folders(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    folderName = db.Column(db.String(50))
    type = db.Column(db.String(20))
    icon = db.Column(db.String(20))
    time = db.Column(db.String(20))
    parent = db.Column(db.String(50))

class Files(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fileName = db.Column(db.String(50))
    type = db.Column(db.String(20))
    icon = db.Column(db.String(20))
    time = db.Column(db.String(20))
    size = db.Column(db.String(20))
    parent = db.Column(db.String(50))

# ustawienia Flask-Login
loginManager = LoginManager()
loginManager.init_app(app)
loginManager.login_view = 'login'
loginManager.login_message = 'Nie jesteś zalogowany'
loginManager.login_message_category = 'warning'

@loginManager.user_loader
def loadUser(id):
    return Users.query.filter_by(id=id).first()

# formularze
class Login(FlaskForm):
    """formularz logowania"""
    userMail = EmailField('Mail', validators=[DataRequired()], render_kw={"placeholder": "Mail"})
    userPass = PasswordField('Hasło', validators=[DataRequired()], render_kw={"placeholder": "Hasło"})
    submit = SubmitField('Zaloguj')

class Register(FlaskForm):
    """formularz rejestracji"""
    firstName = StringField('Imię', validators=[DataRequired()], render_kw={"placeholder": "Imię"})
    lastName = StringField('Nazwisko', validators=[DataRequired()], render_kw={"placeholder": "Nazwisko"})
    userMail = EmailField('Mail', validators=[DataRequired()], render_kw={"placeholder": "Mail"})
    userPass = PasswordField('Hasło', validators=[DataRequired()], render_kw={"placeholder": "Hasło"})
    submit = SubmitField('Rejestruj')

class Add(FlaskForm):
    """formularz dodawania użytkowników"""
    firstName = StringField('Imię', validators=[DataRequired()], render_kw={"placeholder": "Imię"})
    lastName = StringField('Nazwisko', validators=[DataRequired()], render_kw={"placeholder": "Nazwisko"})
    userMail = EmailField('Mail', validators=[DataRequired()], render_kw={"placeholder": "Mail"})
    userPass = PasswordField('Hasło', validators=[DataRequired()], render_kw={"placeholder": "Hasło"})
    userRole = SelectField('Uprawnienia', validators=[DataRequired()], choices=[('user', 'Użytkownik'), ('admin', 'Administrator')])
    submit = SubmitField('Dodaj')

class Edit(FlaskForm):
    """formularz edycji danych użytkownika"""
    firstName = StringField('Imię', validators=[DataRequired()], render_kw={"placeholder": "Imię"})
    lastName = StringField('Nazwisko', validators=[DataRequired()], render_kw={"placeholder": "Nazwisko"})
    userMail = EmailField('Mail', validators=[DataRequired()], render_kw={"placeholder": "Mail"})
    userRole = SelectField('Uprawnienia', validators=[DataRequired()], choices=[('user', 'Użytkownik'), ('admin', 'Administrator')])
    submit = SubmitField('Zapisz')

class EditFolder(FlaskForm):
    """formularz edycji danych użytkownika"""
    folderName = StringField('Nowa nazwa', validators=[DataRequired()], render_kw={"placeholder": "Folder"})
    submit = SubmitField('Zapisz')

class Password(FlaskForm):
    """formularz zmiany hasła przez zalogowanego użytkownika"""
    userMail = EmailField('Mail', validators=[DataRequired()], render_kw={"placeholder": "Mail"})
    userPass = PasswordField('Bieżące Hasło', validators=[DataRequired()], render_kw={"placeholder": "Bieżące hasło"})
    newUserPass = PasswordField('Nowe hasło', validators=[DataRequired()], render_kw={"placeholder": "Nowe hasło"})
    submit = SubmitField('Zapisz')

class ChangePass(FlaskForm):
    """formularz zmiany hasła uzytkownika z panelu admina"""
    userPass = PasswordField('Hasło', validators=[DataRequired()], render_kw={"placeholder": "Hasło"})
    submit = SubmitField('Zapisz')

class Search(FlaskForm):
    """formularz wyszukiwania plików i folderów"""
    searchkey = StringField('Szukaj', validators=[DataRequired()])
    submit = SubmitField('Szukaj')

class CreateFolders(FlaskForm):
    """formularz tworzenia folderów"""
    folderName = StringField('Nazwa folderu', validators=[DataRequired()], render_kw={'placeholder': 'Nazwa folderu'})
    submit = SubmitField('Utwórz')

class UploadFiles(FlaskForm):
    """formularz tworzenia folderów"""
    fileName = FileField('Nazwa pliku', validators=[FileAllowed(app.config['UPLOAD_EXTENSIONS'])], render_kw={'placeholder': '.jpg, .jpeg, .png, .txt'})
    submit = SubmitField('Prześlij')

class DeleteFolder(FlaskForm):
    """formularz usuwający folder"""
    deleteFolder = StringField('Usuń folderu', validators=[DataRequired()])
    submit = SubmitField('Usuń')

# główna aplkacja
@app.route('/')
def index():
    return render_template('index.html', title='Home', headline='Zarządzanie użytkownikami')

@app.route('/login', methods=['GET', 'POST'])
def login():
    user = Users.query.all()
    if not user:
        return redirect(url_for('register'))
    else:
        loginForm = Login()
        if loginForm.validate_on_submit():
            user = Users.query.filter_by(userMail=loginForm.userMail.data).first()
            if user:
                if bcrypt.check_password_hash(user.userPass, loginForm.userPass.data):
                    login_user(user)
                    return redirect(url_for('dashboard'))
    return render_template('login.html', title='Logowanie', headline='Logowanie', loginForm=loginForm)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    registerForm = Register()
    user = Users.query.all()
    if registerForm.validate_on_submit() and not user:
        try:
            hashPass = bcrypt.generate_password_hash(registerForm.userPass.data)
            newUser = Users(userMail=registerForm.userMail.data, userPass=hashPass, firstName=registerForm.firstName.data, lastName=registerForm.lastName.data, userRole='admin')
            db.session.add(newUser)
            db.session.commit()
            flash('Konto utworzone poprawnie', 'success')
            return redirect(url_for('login'))
        except Exception:
            flash('Taki adres mail już istnieje, wpisz inny', 'danger')
            # return redirect(url_for('register'))
    elif registerForm.validate_on_submit():
        try:
            hashPass = bcrypt.generate_password_hash(registerForm.userPass.data)
            newUser = Users(userMail=registerForm.userMail.data, userPass=hashPass, firstName=registerForm.firstName.data, lastName=registerForm.lastName.data, userRole='user')
            db.session.add(newUser)
            db.session.commit()
            flash('Konto utworzone poprawnie', 'success')
            return redirect(url_for('login'))
        except Exception:
            flash('Taki adres mail już istnieje, wpisz inny', 'danger')
            # return redirect(url_for('register'))
    return render_template('register.html', title='Rejestracja', headline='Rejestracja', registerForm=registerForm)

@app.route('/dashboard')
@login_required
def dashboard():
    addUser = Add()
    editUser = Edit()
    editUserPass = ChangePass()
    search = Search()
    createFolder = CreateFolders()
    uploadFile = UploadFiles()
    users = Users.query.all()
    deleteFolder = DeleteFolder()
    efitFolder = EditFolder()
    folders = Folders.query.filter_by(parent=current_parent)
    files = Files.query.filter_by(parent=current_parent)
    return render_template('dashboard.html', title='Dashboard', users=users, addUser=addUser, editUser=editUser,
                           editUserPass=editUserPass, search=search, createFolder=createFolder, uploadFile=uploadFile,
                           folders=folders, files=files, renameFolder=efitFolder, deleteFolder=deleteFolder, current_parent=current_parent)

@app.route('/add-user', methods=['GET', 'POST'])
@login_required
def addUser():
    addUser = Add()
    if addUser.validate_on_submit():
        try:
            hashPass = bcrypt.generate_password_hash(addUser.userPass.data)
            newUser = Users(userMail=addUser.userMail.data, userPass=hashPass, firstName=addUser.firstName.data, lastName=addUser.lastName.data, userRole=addUser.userRole.data)
            db.session.add(newUser)
            db.session.commit()
            flash('Konto utworzone poprawnie', 'success')
            return redirect(url_for('dashboard'))
        except Exception:
            flash('Taki adres mail już istnieje, wpisz inny', 'danger')
            return redirect(url_for('dashboard'))

@app.route('/edit-user<int:id>', methods=['POST', 'GET'])
@login_required
def editUser(id):
    editUser = Edit()
    user = Users.query.get_or_404(id)
    if editUser.validate_on_submit():
        user.firstName = editUser.firstName.data
        user.lastName = editUser.lastName.data
        user.userMail = editUser.userMail.data
        user.userRole = editUser.userRole.data
        db.session.commit()
        flash('Dane zapisane poprawnie', 'success')
        return redirect(url_for('dashboard'))

@app.route('/delete-user', methods=['GET', 'POST'])
@login_required
def deleteUser():
    if request.method == 'GET':
        id = request.args.get('id')
        user = Users.query.filter_by(id=id).one()
        db.session.delete(user)
        db.session.commit()
        flash('Użytkownik usunięty poprawnie', 'success')
        return redirect(url_for('dashboard'))


@app.route('/enter-folder<string:name>', methods=['POST', 'GET'])
@login_required
def enterFolder(name):
    global current_parent, current_path
    current_parent = name
    current_path += name
    current_path += "/"
    return redirect(url_for('dashboard'))

@app.route('/leave-folder<string:parent>', methods=['POST', 'GET'])
@login_required
def leaveFolder(parent):
    global current_parent, current_path
    current_parent = ""
    lengthof = len(current_path.split('/'))-2
    counter = 0
    new_path = ""
    if lengthof > 0:
        for i in current_path.split('/'):
            counter = counter + 1
            new_path += i
            new_path += "/"
            if counter == lengthof:
                current_path = new_path
                current_parent = i
                break
    else:
        current_path = ""
        current_parent = ""
    return redirect(url_for('dashboard'))

@app.route('/edit-user-pass<int:id>', methods=['GET', 'POST'])
@login_required
def editUserPass(id):
    editUserPass = ChangePass()
    user = Users.query.get_or_404(id)
    if editUserPass.validate_on_submit():
        user.userPass = bcrypt.generate_password_hash(editUserPass.userPass.data)
        db.session.commit()
        flash('Hasło zmienione poprawnie', 'success')
        return redirect(url_for('dashboard'))

@app.route('/change-pass', methods=['GET', 'POST'])
@login_required
def changePass():
    changePassForm = Password()
    if changePassForm.validate_on_submit():
        user = Users.query.filter_by(userMail=changePassForm.userMail.data).first()
        if user:
            if bcrypt.check_password_hash(user.userPass, changePassForm.userPass.data):
                user.userPass = bcrypt.generate_password_hash(changePassForm.newUserPass.data)
                db.session.commit()
                flash('Hasło zostało zmienione', 'success')
                return redirect(url_for('dashboard'))
    return render_template('change-pass.html', title='Zmiana hasła', changePassForm=changePassForm)

@app.route('/create-folder', methods=['GET', 'POST'])
@login_required
def createFolder():
    folderName = request.form['folderName']
    if folderName != '':
        os.mkdir(os.path.join(app.config['UPLOAD_PATH'],current_path, folderName))
        time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        newFolder = Folders(folderName=folderName, type='folder', time=time, icon='bi bi-folder',parent=current_parent)
        db.session.add(newFolder)
        db.session.commit()
        flash('Folder utworzony poprawnie', 'success')
        return redirect(url_for('dashboard'))

@app.route('/rename-folder<int:id>', methods=['GET', 'POST'])
@login_required
def renameFolder(id):
    folder = Folders.query.get_or_404(id)

    folderr = Folders.query.filter_by(id=id).first()
    newName = request.form['folderName']
    oldname = folderr.folderName
    oldpath = os.path.join(app.config['UPLOAD_PATH'],current_path, oldname)
    newpath = os.path.join(app.config['UPLOAD_PATH'],current_path, newName)
    os.rename(oldpath, newpath)
    folderr.folderName = newName
    folders = Folders.query.filter_by(parent=oldname)
    for f in folders:
        f.parent = newName
    files = Files.query.filter_by(parent=oldname)
    for fi in files:
        fi.parent = newName
    db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/delete-folder<int:id>', methods=['GET', 'POST'])
@login_required
def deleteFolder(id):
    deleteFolder = Folders.query.get_or_404(id)
    shutil.rmtree(os.path.join(app.config['UPLOAD_PATH'], current_path, deleteFolder.folderName))
    # os.rmdir(os.path.join(app.config['UPLOAD_PATH'], deleteFolder.folderName))
    db.session.delete(deleteFolder)
    db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/upload-file', methods=['GET', 'POST'])
@login_required
def uploadFile():
    uploadedFile = request.files['fileName']
    fileName = secure_filename(uploadedFile.filename)
    if fileName != '':
        fileExtension = os.path.splitext(fileName)[1]
        if fileExtension not in app.config['UPLOAD_EXTENSIONS']:
            abort(400)
        type = ''
        icon = ''
        if fileExtension == '.png':
            type = 'png'
            icon = 'bi bi-filetype-png'
        elif fileExtension == '.jpg':
            type = 'jpg'
            icon = 'bi bi-filetype-jpg'
        elif fileExtension == '.jpeg':
            type = 'jpeg'
            icon = 'bi bi-filetype-jpg'
        elif fileExtension == '.txt':
            type = 'txt'
            icon = 'bi bi-filetype-txt'
        uploadedFile.save(os.path.join(app.config['UPLOAD_PATH'],current_path, fileName))
        size = round(os.stat(os.path.join(app.config['UPLOAD_PATH'],current_path, fileName)).st_size / (1024 * 1024), 2)
        time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        newFile = Files(fileName=fileName, type=type, icon=icon, size=size, time=time,parent=current_parent)
        db.session.add(newFile)
        db.session.commit()
        flash('Plik przesłany poprawnie', 'success')
        return redirect(url_for('dashboard'))



if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
