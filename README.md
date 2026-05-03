# CampusEats Backend

Backend API production-ready pour l'app mobile CampusEats (Django + DRF + PostgreSQL + Redis + MinIO).

## Documentation API

- Documentation complète: `docs/API_DOCUMENTATION.md`
- Base URL VPS actuelle: `http://74.208.50.178`
- Prompt React Native (TikTok-style): `docs/PROMPT_REACT_NATIVE_TIKTOK_APP.md`
- Prompt intégration routes social / favoris / recherche / notifications : `docs/PROMPT_INTEGRER_ROUTES_SOCIAL.md`

## Démarrage rapide

1. Copier le fichier d'environnement:
   - `cp .env.example .env`
2. Lancer la stack:
   - `docker compose up --build`
3. L'API est disponible sur:
   - `http://localhost:8000`

## Déploiement VPS (avec Nginx reverse-proxy)

1. Sur le VPS, prépare `.env` (au minimum):
   - `DEBUG=False`
   - `SECRET_KEY=...`
   - `ALLOWED_HOSTS=IP_DU_VPS`
   - `CSRF_TRUSTED_ORIGINS=http://IP_DU_VPS`
   - `MEDIA_PUBLIC_DOMAIN=IP_DU_VPS/media`
   - `MEDIA_PUBLIC_PROTOCOL=http:`
2. Lancer:
   - `docker compose -f docker-compose.vps.yml up -d --build`
3. L'API est disponible sur:
   - `http://IP_DU_VPS` (Nginx → Django)
   - Les fichiers vidéo sont servis via `http://IP_DU_VPS/media/...` (Nginx → MinIO)

### Mettre à jour le VPS après un `git pull`

Le conteneur `web` exécute `migrate` et `collectstatic` au démarrage (`scripts/start.sh`). Après avoir récupéré le code :

1. **SSH** sur le VPS, puis aller dans le répertoire du dépôt (celui où se trouvent `docker-compose.vps.yml` et `.env`).
2. **Sauvegardes (recommandé avant migration)** : sauvegarde PostgreSQL si la base contient des données importantes (ex. `docker compose -f docker-compose.vps.yml exec db pg_dump -U campuseats campuseats > backup.sql`).
3. **Mettre à jour le code** : `git pull` (branche concernée).
4. **Reconstruire et redémarrer** la stack pour prendre en compte dépendances, migrations et code :
   - `docker compose -f docker-compose.vps.yml up -d --build`
5. **Vérifier** : logs du service web sans erreur au démarrage :
   - `docker compose -f docker-compose.vps.yml logs -f web`  
   Vous devez voir les lignes « Appliquer migrations Django… » puis Gunicorn.
6. En cas de **nouvelles variables** dans `.env.example`, fusionner manuellement dans le `.env` du VPS avant le redémarrage.

### HTTPS sans nom de domaine (auto-signé)

Let’s Encrypt ne fournit généralement pas de certificat pour une IP. Pour chiffrer quand même:

1. Génère un certificat auto-signé sur le VPS:
   - `mkdir -p nginx/certs`
   - `openssl req -x509 -newkey rsa:2048 -nodes -days 365 -keyout nginx/certs/privkey.pem -out nginx/certs/fullchain.pem -subj "/CN=IP_DU_VPS"`
2. Décommente le bloc `listen 443 ssl` dans `nginx/conf.d/app.conf`
3. Relance:
   - `docker compose -f docker-compose.vps.yml up -d --build`

## Endpoints principaux

Voir la liste complète dans `docs/API_DOCUMENTATION.md`. Exemples :

- Auth : `POST /api/auth/register`, `POST /api/auth/login`, `POST /api/auth/token/refresh`
- Vidéos : `GET /api/videos`, `POST /api/videos`, `GET /api/videos/{id}`, `GET /api/videos/nearby`, `POST /api/videos/{id}/like`, `GET /api/videos/{id}/comments`, `POST /api/videos/{id}/comment`, `POST|DELETE /api/videos/{id}/bookmark`
- Utilisateurs : `GET|PATCH /api/users/me`, `POST /api/users/me/avatar`, `GET /api/users/{id}`, `GET /api/users/{id}/videos`, `GET .../followers|following`, `POST|DELETE /api/users/{id}/follow`, …
- Autres : `GET /api/search`, `GET|POST /api/sounds`, `GET /api/bookmarks`, `GET /api/notifications`, reviews sous `/api/reviews`

## Filtres utiles (feed vidéo)

- Chronologique : `GET /api/videos`
- Tendance : `GET /api/videos?feed=trending`
- Pour toi : `GET /api/videos?feed=for_you`
- Abonnements (JWT) : `GET /api/videos?feed=following`
- Proximité : `GET /api/videos/nearby?lat=48.85&lng=2.35&radius_km=3`
