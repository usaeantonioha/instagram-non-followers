"""
Instagram Non-Followers Finder - Aplicación Web
Servidor Flask con API REST
"""

from flask import Flask, render_template, request, jsonify, session
from instagram_scraper import InstagramScraper, ScraperConfig
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'change-this-to-a-random-secret-key')

# Almacenamiento temporal de resultados (en producción usar Redis/DB)
results_cache = {}


@app.route('/')
def index():
    """Página principal"""
    return render_template('index.html')


@app.route('/api/analyze', methods=['POST'])
def analyze():
    """Endpoint para analizar no seguidores"""
    try:
        data = request.json
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return jsonify({
                'success': False,
                'message': 'Usuario y contraseña son requeridos'
            }), 400

        # Configuración segura
        config = ScraperConfig(
            min_delay=2.5,
            max_delay=5.5,
            long_pause_min=200,
            long_pause_max=320,
            actions_before_pause=12,
            max_actions_per_hour=80,
            max_daily_actions=400
        )

        scraper = InstagramScraper(username, password, config)

        # Login
        if not scraper.login():
            scraper.close()
            return jsonify({
                'success': False,
                'message': 'Error al iniciar sesión. Verifica tus credenciales.'
            }), 401

        # Obtener datos
        followers = scraper.get_followers()
        following = scraper.get_following()

        # Encontrar no seguidores
        non_followers = scraper.find_non_followers(followers, following)

        # Guardar en caché
        session_id = username
        results_cache[session_id] = {
            'followers': followers,
            'following': following,
            'non_followers': non_followers
        }

        scraper.close()

        return jsonify({
            'success': True,
            'data': {
                'followers_count': len(followers),
                'following_count': len(following),
                'non_followers_count': len(non_followers),
                'non_followers': non_followers[:50]  # Limitar a 50 para la UI
            }
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500


@app.route('/api/results')
def get_results():
    """Obtener resultados cacheados"""
    username = request.args.get('username')
    if username in results_cache:
        data = results_cache[username]
        return jsonify({
            'success': True,
            'data': data
        })
    return jsonify({
        'success': False,
        'message': 'No hay resultados disponibles'
    }), 404


@app.route('/api/export', methods=['POST'])
def export_results():
    """Exportar resultados a JSON"""
    try:
        data = request.json
        username = data.get('username')

        if username in results_cache:
            results = results_cache[username]
            return jsonify({
                'success': True,
                'data': results['non_followers']
            })

        return jsonify({
            'success': False,
            'message': 'No hay resultados para exportar'
        }), 404

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)