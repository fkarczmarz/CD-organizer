from flask import Flask, render_template, request, session, redirect, jsonify
from flask_caching import Cache
from werkzeug.utils import secure_filename
from app.database import init_db, SessionLocal
from app.models.album import Album
import discogs_client
import os
import time
import json
from json.decoder import JSONDecodeError

# Konfiguracja aplikacji
app = Flask(__name__)
app.secret_key = 'tajny_klucz_123'
app.config['CACHE_TYPE'] = 'SimpleCache'
cache = Cache(app)

# Konfiguracja Discogs
DISCOGS_USER_TOKEN = 'yjoMpKkEyzIKnpcDbFbgHiYFFvYhtEHEYOzZjzrE'
discogs = discogs_client.Client('CDOrganizer/1.0', user_token=DISCOGS_USER_TOKEN)

# Inicjalizacja bazy danych
init_db()

# Helper do pobierania danych z cache
@cache.memoize(timeout=3600)
def get_release_details(release_id):
    try:
        release = discogs.release(release_id)
        return {
            'title': release.title,
            'artists': [{'name': a.name} for a in release.artists] if hasattr(release, 'artists') else [],
            'year': release.year if hasattr(release, 'year') else None,
            'images': release.images if hasattr(release, 'images') else [],
            'genres': release.genres if hasattr(release, 'genres') else [],
            'country': release.country if hasattr(release, 'country') else None,
            'formats': [{'name': f['name']} for f in release.formats] if hasattr(release, 'formats') else []
        }
    except Exception as e:
        app.logger.error(f"Błąd Discogs API: {str(e)}")
        return None

# Error handling
@app.errorhandler(Exception)
def handle_exception(e):
    error_type = type(e).__name__
    app.logger.error(f"{error_type}: {str(e)}")
    
    friendly_messages = {
        'JSONDecodeError': "Problem z połączeniem do Discogs. Album może być już dodany!",
        'AttributeError': "Brak wymaganych danych w odpowiedzi API",
        'Exception': "Wystąpił nieoczekiwany błąd. Spróbuj ponownie."
    }
    
    message = friendly_messages.get(error_type, friendly_messages['Exception'])
    return render_template('error.html', message=message), 500

# Routing
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/add_album', methods=['GET', 'POST'])
def add_album_view():
    if request.method == 'POST':
        db_session = SessionLocal()
        try:
            new_album = Album(
                title=request.form['title'],
                artist=request.form['artist'],
                year=request.form['year']
            )
            db_session.add(new_album)
            db_session.commit()
            return redirect('/albums')
        except Exception as e:
            db_session.rollback()
            return f"Error: {str(e)}"
        finally:
            db_session.close()
    return render_template('add_album.html')

@app.route('/edit_album/<int:album_id>', methods=['GET', 'POST'])
def edit_album_view(album_id):
    db_session = SessionLocal()
    try:
        album = db_session.query(Album).filter(Album.id == album_id).first()
        
        if request.method == 'POST':
            try:
                album.title = request.form['title']
                album.artist = request.form['artist']
                album.year = request.form['year']
                album.genre = request.form.get('genre', '')
                album.country = request.form.get('country', '')
                album.format = request.form.get('format', '')
                
                if 'cover_image' in request.files and request.files['cover_image'].filename:
                    file = request.files['cover_image']
                    filename = secure_filename(file.filename)
                    upload_folder = 'static/covers'
                    os.makedirs(upload_folder, exist_ok=True)
                    file_path = os.path.join(upload_folder, filename)
                    file.save(file_path)
                    album.cover_url = f'/{file_path}'
                
                db_session.commit()
                return redirect('/albums')
            except Exception as e:
                db_session.rollback()
                return f"Error: {str(e)}"
        
        return render_template('edit_album.html', album=album)
    finally:
        db_session.close()

@app.route('/delete_album/<int:album_id>', methods=['POST'])
def delete_album(album_id):
    db_session = SessionLocal()
    try:
        album = db_session.query(Album).filter(Album.id == album_id).first()
        db_session.delete(album)
        db_session.commit()
        return redirect('/albums')
    except Exception as e:
        db_session.rollback()
        return f"Error: {str(e)}"
    finally:
        db_session.close()

@app.route('/search_discogs', methods=['GET', 'POST'])
def search_discogs():
    db_session = SessionLocal()
    try:
        source = request.args.get('source', '')
        
        if request.method == 'GET' and source == 'home':
            return render_template('search_discogs.html')
        
        query = session.get('last_search_query', '') if request.method == 'GET' else request.form['query']
        
        if not query:
            return render_template('search_discogs.html')
        
        session['last_search_query'] = query
        results = discogs.search(query, type='release')
        
        albums = []
        for result in results.page(1):
            try:
                release_data = get_release_details(result.id)
                if not release_data:
                    continue
                
                existing_album = db_session.query(Album).filter(Album.discogs_id == result.id).first()
                
                albums.append({
                    'title': release_data.get('title', 'Unknown Title'),
                    'artist': ', '.join([a['name'] for a in release_data['artists']]) if release_data['artists'] else 'Unknown Artist',
                    'year': release_data.get('year', 'Unknown Year'),
                    'cover_url': release_data['images'][0]['uri'] if release_data.get('images') else None,
                    'genre': ', '.join(release_data['genres']) if release_data.get('genres') else 'Unknown Genre',
                    'country': release_data.get('country', 'Unknown Country'),
                    'format': ', '.join([f['name'] for f in release_data['formats']]) if release_data.get('formats') else 'Unknown Format',
                    'id': result.id,
                    'is_added': existing_album is not None
                })
                
                if len(albums) >= 5:  # Tymczasowe ograniczenie
                    break
                    
            except Exception as e:
                app.logger.warning(f"Błąd przetwarzania wyniku: {str(e)}")
                continue
        
        return render_template('search_results.html', albums=albums)
    except Exception as e:
        return f"Error: {str(e)}", 500
    finally:
        db_session.close()

@app.route('/add_album_from_discogs/<int:discogs_id>', methods=['GET'])
def add_album_from_discogs(discogs_id):
    db_session = SessionLocal()
    try:
        if db_session.query(Album).filter(Album.discogs_id == discogs_id).first():
            return jsonify({'status': 'info', 'message': 'Album już istnieje w kolekcji!'})
        
        release_data = get_release_details(discogs_id)
        if not release_data:
            return jsonify({'status': 'error', 'message': 'Nie udało się pobrać danych z Discogs'}), 500
        
        new_album = Album(
            title=release_data.get('title', 'Unknown Title'),
            artist=', '.join([a['name'] for a in release_data['artists']]) if release_data['artists'] else 'Unknown Artist',
            year=release_data.get('year'),
            discogs_id=discogs_id,
            cover_url=release_data['images'][0]['uri'] if release_data.get('images') else None,
            genre=', '.join(release_data['genres']) if release_data.get('genres') else '',
            country=release_data.get('country', ''),
            format=', '.join([f['name'] for f in release_data['formats']]) if release_data.get('formats') else ''
        )
        
        db_session.add(new_album)
        db_session.commit()
        return jsonify({'status': 'success', 'message': 'Album dodany pomyślnie!'})
    except Exception as e:
        db_session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        db_session.close()

@app.route('/albums')
def albums_view():
    db_session = SessionLocal()
    try:
        albums = db_session.query(Album).all()
        return render_template('albums.html', albums=albums)
    except Exception as e:
        return f"Error: {str(e)}"
    finally:
        db_session.close()

if __name__ == '__main__':
    app.run(debug=True)
