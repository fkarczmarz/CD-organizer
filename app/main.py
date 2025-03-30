from flask import Flask, request, jsonify
from app.database import init_db, SessionLocal  # <-- Zmiana z `app.database` na `.database`
from app.models.album import Album

app = Flask(__name__)
init_db()


@app.route('/')
def home():
    return "Welcome to the CD Organizer!"

# Dodawanie nowej płyty CD
@app.route('/add', methods=['POST'])
def add_album():
    session = SessionLocal()  # Otwieramy sesję bazy danych
    data = request.json  # Pobieramy dane z żądania POST
    try:
        # Tworzymy nowy obiekt Album
        new_album = Album(
            title=data['title'],
            artist=data['artist'],
            year=data['year']
        )
        session.add(new_album)  # Dodajemy album do sesji
        session.commit()  # Zapisujemy zmiany w bazie danych
        return jsonify({"message": "Album added successfully!"}), 201
    except Exception as e:
        session.rollback()  # Cofamy zmiany w razie błędu
        return jsonify({"error": str(e)}), 400
    finally:
        session.close()  # Zamykamy sesję


# Wyświetlanie wszystkich płyt CD
@app.route('/albums', methods=['GET'])
def get_albums():
    session = SessionLocal()  # Otwieramy sesję bazy danych
    try:
        # Pobieramy wszystkie rekordy z tabeli albums
        albums = session.query(Album).all()
        # Tworzymy listę albumów w formacie JSON
        result = [
            {"id": album.id, "title": album.title, "artist": album.artist, "year": album.year}
            for album in albums
        ]
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    finally:
        session.close()  # Zamykamy sesję

if __name__ == '__main__':
    app.run(debug=True)
