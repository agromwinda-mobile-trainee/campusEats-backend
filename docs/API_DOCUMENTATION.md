# CampusEats API Documentation

Documentation officielle de l'API backend CampusEats.

- **Base URL (VPS):** `http://74.208.50.178`
- **Version API:** `v1` (routes actuelles sous `/api`)
- **Format:** JSON (sauf uploads fichiers en `multipart/form-data`)
- **Auth:** JWT Bearer

---

## 1) Authentification

L'API utilise JWT.  
Après login, ajoutez le token d'accès dans l'en-tête:

`Authorization: Bearer <access_token>`

### 1.1 Register

- **Endpoint:** `POST /api/auth/register`
- **Auth requise:** Non
- **Content-Type:** `application/json`

#### Request body

```json
{
  "username": "alice",
  "email": "alice@example.com",
  "password": "StrongPass123",
  "bio": "food lover",
  "latitude": 48.8566,
  "longitude": 2.3522
}
```

#### Success response (201)

```json
{
  "id": 1,
  "username": "alice",
  "email": "alice@example.com",
  "avatar": null,
  "bio": "food lover",
  "latitude": "48.856600",
  "longitude": "2.352200"
}
```

### 1.2 Login

- **Endpoint:** `POST /api/auth/login`
- **Auth requise:** Non
- **Content-Type:** `application/json`

#### Request body

```json
{
  "username": "alice",
  "password": "StrongPass123"
}
```

#### Success response (200)

```json
{
  "refresh": "<jwt_refresh>",
  "access": "<jwt_access>"
}
```

---

## 2) Videos

### 2.1 Lister le feed

- **Endpoint:** `GET /api/videos`
- **Auth requise:** Non
- **Pagination:** Cursor pagination (infinite scroll)

#### Query params

- `feed=trending` (optionnel): feed “tendance”

#### Success response (200)

```json
{
  "next": "http://74.208.50.178/api/videos?cursor=cD0yMDI2LTA0...",
  "previous": null,
  "results": [
    {
      "id": 10,
      "user": 1,
      "username": "alice",
      "video_url": "http://74.208.50.178/media/videos/clip.mp4",
      "caption": "Best noodles near campus",
      "latitude": "48.856600",
      "longitude": "2.352200",
      "created_at": "2026-04-29T08:30:00Z",
      "views_count": 12,
      "likes_count": 4,
      "comments_count": 2
    }
  ]
}
```

### 2.2 Créer une vidéo

- **Endpoint:** `POST /api/videos`
- **Auth requise:** Oui (JWT)
- **Content-Type:** `multipart/form-data`

#### Form fields

- `video_url` (fichier, obligatoire)
- `caption` (string, optionnel)
- `latitude` (decimal, optionnel)
- `longitude` (decimal, optionnel)

#### Success response (201)

```json
{
  "id": 11,
  "video_url": "http://74.208.50.178/media/videos/new.mp4",
  "caption": "Campus burger test",
  "latitude": "48.856600",
  "longitude": "2.352200"
}
```

### 2.3 Détail d'une vidéo

- **Endpoint:** `GET /api/videos/{id}`
- **Auth requise:** Non
- **Effet métier:** incrémente `views_count`

### 2.4 Vidéos à proximité

- **Endpoint:** `GET /api/videos/nearby`
- **Auth requise:** Non

#### Query params requis

- `lat` (decimal)
- `lng` (decimal)

#### Query params optionnels

- `radius_km` (decimal, défaut `3`)

#### Exemple

`GET /api/videos/nearby?lat=48.8566&lng=2.3522&radius_km=5`

---

## 3) Interactions

### 3.1 Like / Unlike (toggle)

- **Endpoint:** `POST /api/videos/{id}/like`
- **Auth requise:** Oui (JWT)
- **Comportement:** 
  - crée le like si absent
  - supprime le like si déjà présent

#### Success responses

- **201** `{ "liked": true }`
- **200** `{ "liked": false }`

### 3.2 Commenter une vidéo

- **Endpoint:** `POST /api/videos/{id}/comment`
- **Auth requise:** Oui (JWT)
- **Content-Type:** `application/json`

#### Request body

```json
{
  "text": "Excellent spot!"
}
```

#### Success response (201)

```json
{
  "id": 8,
  "video": 11,
  "username": "alice",
  "text": "Excellent spot!",
  "created_at": "2026-04-29T08:40:00Z"
}
```

---

## 4) Reviews

### 4.1 Lister les reviews

- **Endpoint:** `GET /api/reviews`
- **Auth requise:** Non
- **Pagination:** activée

### 4.2 Créer une review

- **Endpoint:** `POST /api/reviews`
- **Auth requise:** Oui (JWT)
- **Content-Type:** `multipart/form-data`

#### Form fields

- `place_name` (string, obligatoire)
- `rating` (int, obligatoire, 1 à 5)
- `comment` (string, optionnel)
- `media` (fichier image/vidéo, optionnel)
- `latitude` (decimal, optionnel)
- `longitude` (decimal, optionnel)

#### Success response (201)

```json
{
  "id": 3,
  "user": 1,
  "username": "alice",
  "place_name": "Cafeteria Centrale",
  "rating": 5,
  "comment": "Great quality and fast service",
  "media": "http://74.208.50.178/media/reviews/review.jpg",
  "latitude": "48.856600",
  "longitude": "2.352200",
  "created_at": "2026-04-29T08:42:00Z"
}
```

---

## 5) Codes d'erreur standards

- `400 Bad Request` : payload invalide / champs manquants
- `401 Unauthorized` : token absent ou invalide
- `403 Forbidden` : action non autorisée
- `404 Not Found` : ressource inexistante
- `500 Internal Server Error` : erreur serveur inattendue

### Exemple d'erreur de validation (400)

```json
{
  "rating": [
    "Rating must be between 1 and 5."
  ]
}
```

---

## 6) Sécurité & bonnes pratiques client

- Stocker le `refresh` et `access` de manière sécurisée côté mobile.
- Renouveler l'access token avant expiration via `refresh`.
- Toujours envoyer `Authorization: Bearer <token>` pour les endpoints protégés.
- Gérer les retries réseau avec backoff.
- Ne jamais exposer de secrets backend dans l'app mobile.

---

## 7) Exemples cURL rapides

### Register

```bash
curl -X POST http://74.208.50.178/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","email":"alice@example.com","password":"StrongPass123"}'
```

### Login

```bash
curl -X POST http://74.208.50.178/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","password":"StrongPass123"}'
```

### Create video

```bash
curl -X POST http://74.208.50.178/api/videos \
  -H "Authorization: Bearer <access_token>" \
  -F "caption=Campus test video" \
  -F "video_url=@/path/video.mp4"
```

### Like video

```bash
curl -X POST http://74.208.50.178/api/videos/11/like \
  -H "Authorization: Bearer <access_token>"
```

### Create review

```bash
curl -X POST http://74.208.50.178/api/reviews \
  -H "Authorization: Bearer <access_token>" \
  -F "place_name=Cafeteria Centrale" \
  -F "rating=5" \
  -F "comment=Great food" \
  -F "media=@/path/image.jpg"
```

