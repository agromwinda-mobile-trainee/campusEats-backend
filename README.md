# CampusEats Backend

Backend API production-ready pour l'app mobile CampusEats (Django + DRF + PostgreSQL + Redis + MinIO).

## Documentation API

- Documentation complète: `docs/API_DOCUMENTATION.md`
- Base URL VPS actuelle: `http://74.208.50.178`
- Prompt React Native (TikTok-style): `docs/PROMPT_REACT_NATIVE_TIKTOK_APP.md`

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

### HTTPS sans nom de domaine (auto-signé)

Let’s Encrypt ne fournit généralement pas de certificat pour une IP. Pour chiffrer quand même:

1. Génère un certificat auto-signé sur le VPS:
   - `mkdir -p nginx/certs`
   - `openssl req -x509 -newkey rsa:2048 -nodes -days 365 -keyout nginx/certs/privkey.pem -out nginx/certs/fullchain.pem -subj "/CN=IP_DU_VPS"`
2. Décommente le bloc `listen 443 ssl` dans `nginx/conf.d/app.conf`
3. Relance:
   - `docker compose -f docker-compose.vps.yml up -d --build`

## Endpoints principaux

- `POST /api/auth/register`
- `POST /api/auth/login`
- `GET /api/videos/`
- `POST /api/videos/`
- `GET /api/videos/{id}/`
- `POST /api/videos/{id}/like/`
- `POST /api/videos/{id}/comment/`
- `GET /api/reviews/`
- `POST /api/reviews/`

## Filtres utiles

- Feed trending:
  - `GET /api/videos/?feed=trending`
- Feed nearby:
  - `GET /api/videos/nearby/?lat=48.85&lng=2.35&radius_km=3`
# campusEats-backend
