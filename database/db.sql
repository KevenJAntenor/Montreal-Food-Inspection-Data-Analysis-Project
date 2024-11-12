CREATE TABLE Author (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username VARCHAR(50) UNIQUE NOT NULL,
  passwd VARCHAR(128) NOT NULL,
  nom VARCHAR(50),
  prenom VARCHAR(50),
  email VARCHAR(100),
  photo_profil VARCHAR(100)
);
CREATE TABLE Admin_user (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username VARCHAR(50) UNIQUE NOT NULL,
  passwd VARCHAR(128) NOT NULL,
  nom VARCHAR(50),
  prenom VARCHAR(50),
  email VARCHAR(100),
  active BOOLEAN DEFAULT 1
);
CREATE TABLE Article (
  id INTEGER PRIMARY KEY,
  titre VARCHAR(100),
  identifiant VARCHAR(50),
  auteur_id INTEGER,
  date_publication TEXT,
  paragraphe VARCHAR(500),
  FOREIGN KEY (auteur_id) REFERENCES author(id)
);
create table sessions (
  id integer primary key,
  id_session varchar(100),
  utilisateur varchar(50)
);