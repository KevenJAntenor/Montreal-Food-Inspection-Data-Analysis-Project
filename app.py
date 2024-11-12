import uuid
from datetime import date, datetime
from functools import wraps

from flask import (
    Flask,
    abort,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from database.database import Database

app = Flask(__name__)


# cle secrete pour les messages flash
app.config["SECRET_KEY"] = "secretKey"

table_created = False


def intialize_database_data():
    db = Database()
    db.create_tables()
    db.insert_random_data()
    table_created = db.table_created
    db.disconnect()


def get_db():
    if not table_created:
        intialize_database_data()
    return Database()


@app.route("/")
def home_page():
    db = get_db()
    conn = db.get_connection()
    conn.commit()
    cursor = conn.cursor()
    articles = cursor.execute("SELECT * FROM Article").fetchall()
    empty = "Aucun article n'a encore été publié !"
    if not articles:
        cursor.close()
        conn.close()
        flash(empty, "info")
        return render_template("home.html", empty=empty)
    else:
        date_today = date.today()
        articles = cursor.execute(
            "SELECT * FROM Article WHERE date_publication <= ? ORDER BY date_publication DESC LIMIT 5",
            (date_today,),
        ).fetchall()

        cursor.close()
        conn.close()

        return render_template("home.html", articles=articles)


@app.route("/searching_result_page", methods=["POST"])
def searching_result_page():
    if request.method == "POST":
        content = request.form.get("search_field")
        if content:
            db = get_db()
            conn = db.get_connection()
            cursor = conn.cursor()
            found_articles = cursor.execute(
                "SELECT * FROM Article WHERE titre LIKE ? OR paragraphe LIKE ?",
                (f"%{content}%", f"%{content}%"),
            ).fetchall()
            cursor.close()
            conn.close()
            if found_articles:
                return render_template("home.html", found_articles=found_articles)
            else:
                flash(f'Aucun article trouvé pour "{content}" !')
                return redirect("/")
    else:
        abort(404)


@app.route("/article/<string:identifiant>", methods=["GET", "POST"])
def details_article(identifiant):
    db = get_db()
    conn = db.get_connection()
    cursor = conn.cursor()
    article = cursor.execute(
        "SELECT * FROM Article WHERE identifiant = ?", (identifiant,)
    ).fetchone()

    if article:
        auteur = cursor.execute(
            "SELECT * FROM author WHERE id = ?",
            (article[3],),
        ).fetchone()
        print(auteur)
        if request.method == "GET":
            cursor.close()
            conn.close()
            return render_template(
                "details_article.html", article=article, auteur=auteur
            )
    cursor.close()
    conn.close()
    # If article is not found, return a 404 error
    abort(404)


@app.errorhandler(404)
def retourner404(err):
    return render_template("erreur.html", err="404"), 404


@app.errorhandler(400)
def retourner400(err):
    return render_template("erreur.html", err="400"), 400


@app.errorhandler(405)
def retourner500(err):
    return render_template("erreur.html", err="405"), 405


@app.route("/admin", methods=["GET", "POST"])
def login_admin_user():
    if request.method == "GET":
        return render_template("login.html"), 200
    else:
        error_message = "Username et/ou Password"
        username = request.form["username"]
        password = request.form["password"]

        db = get_db()
        conn = db.get_connection()
        cursor = conn.cursor()
        user = cursor.execute(
            "SELECT passwd FROM Admin_user WHERE username = ?", (username,)
        ).fetchone()

        error_message = error_message + " incorrect !"
        if user is None:
            cursor.close()
            conn.close()
            flash(error_message)
            return render_template("login.html"), 404

        if password == user[0]:
            # Access granted
            id_session = uuid.uuid4().hex
            cursor.execute(
                "INSERT INTO sessions (id_session, utilisateur) VALUES (?, ?)",
                (id_session, username),
            )
            conn.commit()
            cursor.close()
            conn.close()
            session["admin"] = id_session
            return redirect("/liste-articles")

        else:
            cursor.close()
            conn.close()
            flash(error_message)
            return render_template("login.html", error_message=error_message), 404


@app.route("/logout")
def admin_logout():
    session.pop("admin", None)
    return redirect(url_for("login_admin_user"))


def authenticated_only(route_function):
    @wraps(route_function)
    def wrapper(*args, **kwargs):
        if is_authenticated(session):
            return route_function(*args, **kwargs)
        else:
            flash("Connectez-vous !", "info")
            return redirect("/admin")

    # wrapper.__name__ = functools.__name__
    return wrapper


def is_authenticated(session):
    admin_session = session.get("admin")
    if admin_session:
        return True
    return False


@app.route("/liste-articles")
@authenticated_only
def page_accueil_admin():
    db = get_db()
    conn = db.get_connection()
    conn.commit()
    cursor = conn.cursor()
    articles = cursor.execute("SELECT * FROM Article").fetchall()
    empty = "Aucun article n'a encore été publié !"
    if not articles:
        cursor.close()
        conn.close()
        flash(empty, "info")
        return render_template("liste_articles.html")
    cursor.close()
    conn.close()
    return render_template("liste_articles.html", articles=articles)


@app.route("/admin-nouveau", methods=["GET", "POST"])
@authenticated_only
def admin_nouvel_article():
    if request.method == "GET":
        return render_template("creer_nouvel_article.html"), 200
    else:
        titre = request.form["titre"]
        identifiant = request.form["identifiant"]
        auteur = request.form["auteur"]
        date_publication = request.form["date_publication"]
        paragraphe = request.form["paragraphe"]

        if (
            not titre
            or not identifiant
            or not auteur
            or not date_publication
            or not paragraphe
        ):
            flash("Tous les champs sont obligatoires !")
            return render_template("creer_nouvel_article.html")

        try:
            datetime.strptime(date_publication, "%Y-%m-%d")
        except ValueError:
            flash("Format de date incorrecte ! Respectez ce format  : YYYY-MM-JJ.")
            return render_template("creer_nouvel_article.html")

        db = get_db()
        conn = db.get_connection()
        cursor = conn.cursor()

        existing_author = cursor.execute(
            "SELECT * FROM Author WHERE nom = ?", (auteur,)
        ).fetchone()

        if not existing_author:
            cursor.execute(
                "INSERT INTO Author (nom, username, passwd) VALUES (?, ?, ?)",
                (auteur, auteur, auteur),
            )
            author_id = cursor.lastrowid
        else:
            author_id = existing_author[0]

        cursor.execute(
            "INSERT INTO Article (titre, identifiant, auteur_id, date_publication, paragraphe) VALUES (?, ?, ?, ?, ?)",
            (titre, identifiant, author_id, date_publication, paragraphe),
        )
        conn.commit()
        cursor.close()
        conn.close()
        flash("Article ajouté avec succès !")
        return redirect("/liste-articles")


@app.route("/utilisateurs", methods=["GET", "POST", "PATCH"])
@authenticated_only
def gerer_utilisateurs():
    db = get_db()
    conn = db.get_connection()
    conn.commit()
    cursor = conn.cursor()
    admin_users = cursor.execute("SELECT * FROM Admin_user").fetchall()

    if admin_users:
        if request.method == "GET":
            cursor.close()
            conn.close()
            return (
                render_template("gerer_utilisateurs.html", admin_users=admin_users),
                200,
            )
    else:
        cursor.close()
        conn.close()
        abort(404)


@app.route("/ajouter_utilisateur", methods=["POST"])
@authenticated_only
def ajouter_utilisateur():
    if request.method == "POST":
        username = request.form["username"]
        passwd = request.form["password"]
        nom = request.form["nom"]
        prenom = request.form["prenom"]
        email = request.form["email"]

        db = get_db()
        db.insert_admin_user(
            username=username,
            passwd=passwd,
            nom=nom,
            prenom=prenom,
            email=email,
        )
        db.connection.commit()

        flash("Utilisateur ajouté avec succès !")
        return redirect(url_for("gerer_utilisateurs"))


@app.route("/modifier_utilisateur/<int:user_id>", methods=["POST"])
@authenticated_only
def modifier_utilisateur(user_id):
    if request.method == "POST":
        username = request.form["username"]
        passwd = request.form["password"]
        nom = request.form["nom"]
        prenom = request.form["prenom"]
        email = request.form["email"]

        db = get_db()
        db.update_admin_user(user_id, username, passwd, nom, prenom, email)
        db.connection.commit()
        flash("Utilisateur mis à jour avec succès !")
        return redirect(url_for("gerer_utilisateurs"))


@app.route("/desactiver_utilisateur/<int:user_id>", methods=["POST"])
@authenticated_only
def desactiver_utilisateur(user_id):
    if request.method == "POST":
        db = get_db()
        db.desactiver_admin_user(user_id)
        db.connection.commit()
        if user_id:
            flash("Utilisateur activé avec succès !")
        else:
            flash("Utilisateur désactivé avec succès !")
        return redirect(url_for("gerer_utilisateurs"))


@app.route("/modifier_article/<string:identifiant>", methods=["POST"])
@authenticated_only
def modifier_article(identifiant):
    db = get_db()
    conn = db.get_connection()
    conn.commit()
    cursor = conn.cursor()
    article = cursor.execute(
        "SELECT * FROM Article WHERE identifiant = ?", (identifiant,)
    ).fetchone()

    if article:
        if request.method == "POST":
            titre = request.form["title"]
            paragraphe = request.form["content"]

            cursor.execute(
                """UPDATE Article SET titre = ?, paragraphe = ? WHERE identifiant = ?""",
                (titre, paragraphe, identifiant),
            )
            conn.commit()
            cursor.close()
            conn.close()
            flash("L'article a bien été mis à jour !")
            return redirect(url_for("page_accueil_admin"))
    else:
        cursor.close()
        conn.close()
        abort(404)


def example_route():
    db = Database()
    db.create_tables()
    db.insert_author("username", "passwd", "nom", "prenom", "email", "photo_profil")
    return "Example route"


if __name__ == "__main__":
    app.run(debug=True)
