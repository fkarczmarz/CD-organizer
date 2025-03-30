from flask import Flask, render_template, request, redirect, jsonify
from app.database import init_db, SessionLocal
from app.models.album import Album

app = Flask(__name__)
init_db()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/add_album', methods=['GET', 'POST'])
def add_album_view():
    if request.method == 'POST':
        session = SessionLocal()
        try:
            # Pobieramy dane z formularza
            new_album = Album(
                title=request.form['title'],
                artist=request.form['artist'],
                year=request.form['year']
            )
            session.add(new_album)
            session.commit()
            return redirect('/albums')  # Przekierowanie na stronę z listą płyt
        except Exception as e:
            session.rollback()
            return f"Error: {str(e)}"
        finally:
            session.close()
    return render_template('add_album.html')

@app.route('/edit_album/<int:album_id>', methods=['GET', 'POST'])
def edit_album_view(album_id):
    session = SessionLocal()
    album = session.query(Album).filter(Album.id == album_id).first()
    if request.method == 'POST':
        try:
            album.title = request.form['title']
            album.artist = request.form['artist']
            album.year = request.form['year']
            session.commit()
            return redirect('/albums')
        except Exception as e:
            session.rollback()
            return f"Error: {str(e)}"
        finally:
            session.close()
    return render_template('edit_album.html', album=album)

@app.route('/delete_album/<int:album_id>', methods=['POST'])
def delete_album(album_id):
    session = SessionLocal()
    try:
        album = session.query(Album).filter(Album.id == album_id).first()
        session.delete(album)
        session.commit()
        return redirect('/albums')
    except Exception as e:
        session.rollback()
        return f"Error: {str(e)}"
    finally:
        session.close()

@app.route('/albums')
def albums_view():
    session = SessionLocal()
    try:
        # Pobieramy wszystkie płyty z bazy danych
        albums = session.query(Album).all()
        return render_template('albums.html', albums=albums)
    except Exception as e:
        return f"Error: {str(e)}"
    finally:
        session.close()

if __name__ == '__main__':
    app.run(debug=True)
