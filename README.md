# CampusEats Backend

Backend API production-ready pour l'app mobile CampusEats (Django + DRF + PostgreSQL + Redis + MinIO).

## Démarrage rapide

1. Copier le fichier d'environnement:
   - `cp .env.example .env`
2. Lancer la stack:
   - `docker compose up --build`
3. L'API est disponible sur:
   - `http://localhost:8000`

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
