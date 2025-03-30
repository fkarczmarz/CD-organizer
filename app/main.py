from flask import Flask, render_template, request, session, redirect, jsonify
from app.database import init_db, SessionLocal
from app.models.album import Album
import discogs_client
import time

# Wstaw swój User Token tutaj
DISCOGS_USER_TOKEN = 'yjoMpKkEyzIKnpcDbFbgHiYFFvYhtEHEYOzZjzrE'

# Konfiguracja klienta Discogs
discogs = discogs_client.Client('CDOrganizer/1.0', user_token=DISCOGS_USER_TOKEN)

app = Flask(__name__)
app.secret_key = 'tajny_klucz_123'
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

@app.route('/search_discogs', methods=['GET', 'POST'])
def search_discogs():
    db_session = SessionLocal()
    try:
        # Obsługa powrotu z zachowaniem wyników
        if request.method == 'GET':
            if 'last_search' in session and not request.args.get('refresh'):
                return render_template('search_results.html', 
                                    albums=session['last_search'],
                                    query=session.get('last_query', ''))
            if 'last_query' in session:
                return render_template('search_discogs.html', 
                                     default_query=session['last_query'])
            return render_template('search_discogs.html')

        # Obsługa nowego wyszukiwania
        query = request.form['query']
        session['last_query'] = query
        
        # Zabezpieczenie przed szybkimi zapytaniami
        time.sleep(1.5)
        
        try:
            results = discogs.search(query, type='release')
        except Exception as e:
            return render_template('error.html', 
                                 message=f"Discogs API error: {str(e)}")

        albums = []
        for result in results.page(1):
            try:
                # Obsługa błędnych danych z API
                artist_names = [artist.name for artist in result.artists]
                year = result.year if hasattr(result, 'year') else 'Unknown'
                discogs_id = result.id
            except AttributeError:
                continue

            existing_album = db_session.query(Album).filter(
                Album.discogs_id == discogs_id
            ).first()
            
            albums.append({
                'title': result.title,
                'artist': ', '.join(artist_names),
                'year': year,
                'id': discogs_id,
                'is_added': existing_album is not None
            })

        # Zapisz wyniki w sesji
        session['last_search'] = albums
        return render_template('search_results.html', 
                             albums=albums,
                             query=query)

    except Exception as e:
        return render_template('error.html', 
                             message=f"Unexpected error: {str(e)}")
    finally:
        db_session.close()



@app.route('/add_album_from_discogs/<int:discogs_id>', methods=['GET'])
def add_album_from_discogs(discogs_id):
    time.sleep(1.5)  # Dodaj opóźnienie między żądaniami
    db_session = SessionLocal()
    try:
        release = discogs.release(discogs_id)
        new_album = Album(
            title=release.title,
            artist=', '.join([artist.name for artist in release.artists]),
            year=release.year if hasattr(release, 'year') else None,
            discogs_id=release.id
        )
        db_session.add(new_album)
        db_session.commit()
        return redirect('/search_discogs')  # Wracamy do wyników wyszukiwania
    except Exception as e:
        db_session.rollback()
        return f"Error: {str(e)}"
    finally:
        db_session.close()


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
