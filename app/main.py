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
    session = SessionLocal()
    data = request.json
    new_album = Album(
        title=data['title'],
        artist=data['artist'],
        year=data['year']
    )
    session.add(new_album)
    session.commit()
    session.close()
    return jsonify({"message": "Album added successfully!"}), 201

# Wyświetlanie wszystkich płyt CD
@app.route('/albums', methods=['GET'])
def get_albums():
    session = SessionLocal()
    albums = session.query(Album).all()
    session.close()
    return jsonify([{"id": album.id, "title": album.title, "artist": album.artist, "year": album.year} for album in albums])

if __name__ == '__main__':
    app.run(debug=True)
