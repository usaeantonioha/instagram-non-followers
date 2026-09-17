"""
Instagram Non-Followers Scraper
Módulo principal con todas las medidas de seguridad implementadas.
"""

import time
import random
import json
import logging
import hashlib
from typing import List, Dict, Optional
from dataclasses import dataclass, field
import requests
from requests.exceptions import RequestException

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class ScraperConfig:
    """Configuración de seguridad para el scraper"""
    min_delay: float = 2.0
    max_delay: float = 5.0
    long_pause_min: int = 180
    long_pause_max: int = 300
    actions_before_pause: int = 15
    max_actions_per_hour: int = 100
    max_daily_actions: int = 500
    user_agents: List[str] = field(default_factory=lambda: [
        "Instagram 275.0.0.27.98 Android (26/8.0.0; 480dpi; 1080x1920; Xiaomi; Mi 6; sagit; qcom; en_US; 458229237)",
        "Instagram 275.0.0.27.98 Android (28/9.0; 420dpi; 1080x2029; samsung; SM-G960F; starlte; samsungexynos9810; en_US; 458229238)",
        "Instagram 275.0.0.27.98 Android (29/10.0; 440dpi; 1080x2138; google; Pixel 4; flame; flame; en_US; 458229239)",
        "Instagram 275.0.0.27.98 Android (30/11.0; 420dpi; 1080x2220; samsung; SM-G991B; o1s; exynos2100; en_US; 458229240)",
        "Instagram 275.0.0.27.98 Android (31/12.0; 480dpi; 1080x2400; oneplus; IN2023; OnePlus8T; qcom; en_US; 458229241)"
    ])


class InstagramScraper:
    """Scraper de Instagram con medidas de seguridad avanzadas"""

    def __init__(self, username: str, password: str, config: Optional[ScraperConfig] = None):
        self.username = username
        self.password = password
        self.config = config or ScraperConfig()
        self.session = requests.Session()
        self.session_id = None
        self.csrf_token = None
        self.actions_count = 0
        self.hourly_actions = 0
        self.daily_actions = 0
        self.last_action_time = None
        self.last_hour_reset = time.time()
        self.last_day_reset = time.time()
        self._setup_headers()

    def _setup_headers(self):
        """Configura headers para simular un dispositivo real"""
        user_agent = random.choice(self.config.user_agents)
        self.session.headers.update({
            'User-Agent': user_agent,
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'X-IG-App-ID': '936619743392459',
            'X-IG-Device-ID': self._generate_device_id(),
            'X-IG-Android-ID': self._generate_android_id(),
        })

    def _generate_device_id(self) -> str:
        """Genera un ID de dispositivo aleatorio"""
        return f"android-{random.randint(10000000000000, 99999999999999)}"

    def _generate_android_id(self) -> str:
        """Genera un Android ID aleatorio"""
        random_str = ''.join(random.choices('0123456789abcdef', k=16))
        return hashlib.md5(random_str.encode()).hexdigest()[:16]

    def _human_delay(self, is_long_pause: bool = False):
        """Implementa delays aleatorios para simular comportamiento humano"""
        if is_long_pause:
            delay = random.uniform(self.config.long_pause_min, self.config.long_pause_max)
            logger.info(f"⏸️ Pausa larga de {delay:.1f} segundos (humanización)")
        else:
            delay = random.uniform(self.config.min_delay, self.config.max_delay)
            logger.debug(f"⏱️ Delay de {delay:.2f} segundos")
        time.sleep(delay)

    def _check_rate_limits(self):
        """Verifica que no se excedan los límites de tasa"""
        current_time = time.time()

        if current_time - self.last_hour_reset > 3600:
            self.hourly_actions = 0
            self.last_hour_reset = current_time

        if current_time - self.last_day_reset > 86400:
            self.daily_actions = 0
            self.last_day_reset = current_time

        if self.hourly_actions >= self.config.max_actions_per_hour:
            wait_time = 3600 - (current_time - self.last_hour_reset)
            logger.warning(f"⚠️ Límite horario alcanzado. Esperando {wait_time/60:.1f} minutos")
            time.sleep(wait_time)
            self.hourly_actions = 0

        if self.daily_actions >= self.config.max_daily_actions:
            wait_time = 86400 - (current_time - self.last_day_reset)
            logger.warning(f"⚠️ Límite diario alcanzado. Esperando {wait_time/3600:.1f} horas")
            time.sleep(wait_time)
            self.daily_actions = 0

    def _record_action(self):
        """Registra una acción realizada"""
        self.actions_count += 1
        self.hourly_actions += 1
        self.daily_actions += 1
        self.last_action_time = time.time()

        if self.actions_count % self.config.actions_before_pause == 0:
            self._human_delay(is_long_pause=True)

    def login(self) -> bool:
        """Inicia sesión en Instagram"""
        try:
            logger.info(f"🔐 Iniciando sesión como {self.username}...")

            response = self.session.get('https://www.instagram.com/')
            self._human_delay()

            self.csrf_token = self.session.cookies.get('csrftoken')
            if not self.csrf_token:
                logger.error("❌ No se pudo obtener CSRF token")
                return False

            login_url = 'https://www.instagram.com/accounts/login/ajax/'
            login_data = {
                'username': self.username,
                'enc_password': f'#PWD_INSTAGRAM_BROWSER:0:{int(time.time())}:{self.password}',
                'queryParams': '{}',
                'optIntoOneTap': 'false'
            }

            headers = {
                'X-CSRFToken': self.csrf_token,
                'X-Requested-With': 'XMLHttpRequest',
                'Referer': 'https://www.instagram.com/accounts/login/'
            }

            response = self.session.post(login_url, data=login_data, headers=headers)
            self._human_delay()

            result = response.json()

            if result.get('authenticated'):
                self.session_id = self.session.cookies.get('sessionid')
                logger.info("✅ Login exitoso")
                return True
            else:
                logger.error(f"❌ Login fallido: {result.get('message', 'Error desconocido')}")
                return False

        except Exception as e:
            logger.error(f"❌ Error durante login: {str(e)}")
            return False

    def get_followers(self, limit: Optional[int] = None) -> List[Dict]:
        """Obtiene la lista de seguidores"""
        try:
            logger.info("📥 Obteniendo lista de seguidores...")
            followers = []
            end_cursor = None
            has_next_page = True

            while has_next_page:
                self._check_rate_limits()

                user_id = self._get_user_id()
                if not user_id:
                    break

                url = 'https://www.instagram.com/graphql/query/'
                variables = {
                    'id': user_id,
                    'first': 50,
                    'after': end_cursor
                } if end_cursor else {
                    'id': user_id,
                    'first': 50
                }

                params = {
                    'query_hash': 'c76146de99bb02f6415203be841dd25a',
                    'variables': json.dumps(variables)
                }

                headers = {
                    'X-CSRFToken': self.csrf_token,
                    'X-Requested-With': 'XMLHttpRequest'
                }

                response = self.session.get(url, params=params, headers=headers)
                self._human_delay()
                self._record_action()

                data = response.json()

                if 'data' not in data:
                    logger.error(f"❌ Error en respuesta: {data}")
                    break

                edge_followed_by = data['data']['user']['edge_followed_by']
                edges = edge_followed_by['edges']

                for edge in edges:
                    followers.append({
                        'username': edge['node']['username'],
                        'id': edge['node']['id'],
                        'full_name': edge['node'].get('full_name', ''),
                        'profile_pic': edge['node'].get('profile_pic_url', '')
                    })

                    if limit and len(followers) >= limit:
                        return followers

                has_next_page = edge_followed_by['page_info']['has_next_page']
                end_cursor = edge_followed_by['page_info'].get('end_cursor')

                logger.info(f"📊 Obtenidos {len(followers)} seguidores hasta ahora...")

            logger.info(f"✅ Total seguidores obtenidos: {len(followers)}")
            return followers

        except Exception as e:
            logger.error(f"❌ Error obteniendo seguidores: {str(e)}")
            return []

    def get_following(self, limit: Optional[int] = None) -> List[Dict]:
        """Obtiene la lista de seguidos"""
        try:
            logger.info("📤 Obteniendo lista de seguidos...")
            following = []
            end_cursor = None
            has_next_page = True

            while has_next_page:
                self._check_rate_limits()

                user_id = self._get_user_id()
                if not user_id:
                    break

                url = 'https://www.instagram.com/graphql/query/'
                variables = {
                    'id': user_id,
                    'first': 50,
                    'after': end_cursor
                } if end_cursor else {
                    'id': user_id,
                    'first': 50
                }

                params = {
                    'query_hash': 'd04b0a864b4b54837c0d870b0e77e076',
                    'variables': json.dumps(variables)
                }

                headers = {
                    'X-CSRFToken': self.csrf_token,
                    'X-Requested-With': 'XMLHttpRequest'
                }

                response = self.session.get(url, params=params, headers=headers)
                self._human_delay()
                self._record_action()

                data = response.json()

                if 'data' not in data:
                    logger.error(f"❌ Error en respuesta: {data}")
                    break

                edge_follow = data['data']['user']['edge_follow']
                edges = edge_follow['edges']

                for edge in edges:
                    following.append({
                        'username': edge['node']['username'],
                        'id': edge['node']['id'],
                        'full_name': edge['node'].get('full_name', ''),
                        'profile_pic': edge['node'].get('profile_pic_url', '')
                    })

                    if limit and len(following) >= limit:
                        return following

                has_next_page = edge_follow['page_info']['has_next_page']
                end_cursor = edge_follow['page_info'].get('end_cursor')

                logger.info(f"📊 Obtenidos {len(following)} seguidos hasta ahora...")

            logger.info(f"✅ Total seguidos obtenidos: {len(following)}")
            return following

        except Exception as e:
            logger.error(f"❌ Error obteniendo seguidos: {str(e)}")
            return []

    def _get_user_id(self) -> str:
        """Obtiene el ID del usuario autenticado"""
        try:
            url = 'https://www.instagram.com/accounts/edit/?__a=1'
            headers = {
                'X-CSRFToken': self.csrf_token,
                'X-Requested-With': 'XMLHttpRequest'
            }

            response = self.session.get(url, headers=headers)
            self._human_delay()

            data = response.json()
            return str(data['id'])

        except Exception as e:
            logger.error(f"❌ Error obteniendo user ID: {str(e)}")
            return ""

    def find_non_followers(self, followers: List[Dict], following: List[Dict]) -> List[Dict]:
        """Encuentra usuarios que sigues pero no te siguen"""
        follower_usernames = {f['username'] for f in followers}
        non_followers = [
            user for user in following
            if user['username'] not in follower_usernames
        ]

        logger.info(f"🎯 Encontrados {len(non_followers)} no seguidores")
        return non_followers

    def close(self):
        """Cierra la sesión"""
        if self.session:
            self.session.close()
            logger.info(" Sesión cerrada")