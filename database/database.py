import datetime
import sqlite3


class Database:
    table_created = False

    def __init__(self):
        self.connection = None

    def get_connection(self):
        if self.connection is None:
            self.connection = sqlite3.connect("database/article.db")
        return self.connection

    def disconnect(self):
        if self.connection is not None:
            self.connection.close()

    def create_tables(self):
        if not self.table_created:
            try:
                with self.get_connection() as conn:
                    cursor = conn.cursor()
                    sql_script_path = "database/db.sql"
                    with open(sql_script_path, "r") as file:
                        sql_script = file.read()
                        sql_commands = sql_script.split(";")
                        for command in sql_commands:
                            if command.strip() and not self.table_created:
                                try:
                                    cursor.execute(command)
                                except sqlite3.OperationalError as e:
                                    print(f"Ignoring table creation error: {e}")
                                    self.table_created = True
                        print("Tables created successfully.")
                        self.table_created = True
            except Exception as e:
                print(f"An error occurred while creating tables: {e}")
                return False

    def execute_sql_script(self, file_path):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            with open(file_path, "r") as script_file:
                script = script_file.read()
                cursor.executescript(script)
            conn.commit()
            print("SQL script executed successfully.")
        except Exception as e:
            print("Error executing SQL script:", e)

    def insert_admin_user(self, username, passwd, nom, prenom, email):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO Admin_user (username, passwd, nom, prenom, email) VALUES (?, ?, ?, ?, ?)",
                (username, passwd, nom, prenom, email),
            )
            conn.commit()
            print("Utilisateur inséré avec succès.")
        except sqlite3.IntegrityError:
            print(
                "L'utilisateur avec le nom d'utilisateur {} existe déjà.".format(
                    username
                )
            )

    def insert_author(self, username, passwd, nom, prenom, email, photo_profil):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO Author (username, passwd, nom, prenom, email, photo_profil) VALUES (?, ?, ?, ?, ?, ?)",
                (username, passwd, nom, prenom, email, photo_profil),
            )
            conn.commit()
            print("Auteur inséré avec succès.")
        except sqlite3.IntegrityError:
            print("L'auteur avec le nom d'utilisateur {} existe déjà.".format(username))

    def insert_article(
        self, titre, identifiant, auteur_username, date_publication, paragraphe
    ):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT id FROM Author WHERE username = ?", (auteur_username,)
            )
            auteur_id = cursor.fetchone()[0]

            cursor.execute(
                "INSERT INTO Article (titre, identifiant, auteur_id, date_publication, paragraphe) VALUES (?, ?, ?, ?, ?)",
                (titre, identifiant, auteur_id, date_publication, paragraphe),
            )
            conn.commit()
            print("Article inséré avec succès.")
        except sqlite3.IntegrityError:
            print("L'article avec l'identifiant {} existe déjà.".format(identifiant))

    def insert_random_data(self):
        try:
            # if not self.table_created:
            self.create_tables()
            self.insert_admin_user(
                "prof",
                "secret1234",
                "Jacques",
                "Berger",
                "jb@example.com",
            )
            for i in range(1, 7):
                self.insert_author(
                    f"auteur{i}",
                    "secret1234",
                    f"Nom de l'auteur {i}",
                    f"Prénom de l'auteur {i}",
                    f"email_auteur{i}@example.com",
                    f"profiles_photos/images.jpeg",
                )

                date_publication = f"2024-02-2{i}"
                self.insert_article(
                    f"Titre de l'article {i}",
                    f"identifiant{i}",
                    f"auteur{i}",
                    date_publication,
                    f"Contenu de l'article {i}...",
                )

                self.insert_admin_user(
                    f"utilisateur{i}",
                    "secret1234",
                    f"Nom de l'utilisateur {i}",
                    f"Prénom de l'utilisateur {i}",
                    f"email_utilisateur{i}@example.com",
                )
        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            self.disconnect()

    def desactiver_admin_user(self, user_id):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                if user_id:
                    cursor.execute(
                        "UPDATE Admin_user SET active = 1 WHERE id = ?", (user_id,)
                    )
                else:
                    cursor.execute(
                        "UPDATE Admin_user SET active = 0 WHERE id = ?", (user_id,)
                    )
                conn.commit()
                return True
        except Exception as e:
            print(f"An error occurred while disabling user: {e}")
            return False

    def update_admin_user(self, user_id, username, password, nom, prenom, email):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE Admin_user SET username = ?, passwd = ?, nom = ?, prenom = ?, email = ? WHERE id = ?",
                    (username, password, nom, prenom, email, user_id),
                )
                conn.commit()
                return True
        except Exception as e:
            print(f"An error occurred while updating user: {e}")
            return False


# if __name__ == "__main__":
#     try:
#         db = Database()
#         if not db.table_created:
#             db.create_tables()
#         for i in range(1, 7):
#             db.insert_author(
#                 f"auteur{i}",
#                 "secret1234",
#                 f"Nom de l'auteur {i}",
#                 f"Prénom de l'auteur {i}",
#                 f"email_auteur{i}@example.com",
#                 f"photo_auteur{i}.jpg",
#             )

#             date_publication = f"2024-02-2{i}"
#             db.insert_article(
#                 f"Titre de l'article {i}",
#                 f"identifiant{i}",
#                 f"auteur{i}",
#                 date_publication,
#                 f"Contenu de l'article {i}...",
#             )

#             db.insert_admin_user(
#                 f"utilisateur{i}",
#                 "secret1234",
#                 f"Nom de l'utilisateur {i}",
#                 f"Prénom de l'utilisateur {i}",
#                 f"email_utilisateur{i}@example.com",
#             )
#     except Exception as e:
#         print(f"An error occurred: {e}")
#     finally:
#         db.disconnect()
