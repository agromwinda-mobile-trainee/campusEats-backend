# CampusEats API Documentation

Documentation officielle de l’API backend CampusEats.

- **Base URL (VPS):** `http://74.208.50.178`
- **Version API:** `v1` (routes sous `/api`)
- **Format:** JSON (sauf uploads fichiers en `multipart/form-data`)
- **Auth:** JWT Bearer (`Authorization: Bearer <access_token>`)
- **URLs:** pas de slash final (ex. `/api/videos`, pas `/api/videos/`)

---

## 1) Authentification

Après login ou refresh, envoyez le jeton d’accès dans l’en-tête :

`Authorization: Bearer <access_token>`

### 1.1 Register

- **Endpoint:** `POST /api/auth/register`
- **Auth:** Non
- **Content-Type:** `application/json` ou `multipart/form-data` (si fichier `avatar`)

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

- Peut être envoyé en **`multipart/form-data`** si tu inclus un fichier `avatar`.

#### Success response (201)

Même contrat que **`GET /api/users/me`** (profil courant enrichi) :

```json
{
  "id": 1,
  "username": "alice",
  "email": "alice@example.com",
  "bio": "food lover",
  "avatar": "https://example.com/media/avatars/alice.jpg",
  "followers_count": 0,
  "following_count": 0,
  "videos_count": 0,
  "created_at": "2026-05-03T12:00:00Z",
  "latitude": "48.856600",
  "longitude": "2.352200"
}
```

- **`avatar`** : URL **absolue** lorsque la requête HTTP fournit un contexte (sinon préfixe cohérent avec la configuration médias).
- **`created_at`** : date de création du compte (champ `date_joined`).
- **`email`** : renseigné ; lecture seule côté API utilisateur (non modifiable via `PATCH /me` dans la version actuelle).

### 1.2 Login

- **Endpoint:** `POST /api/auth/login`
- **Auth:** Non
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

### 1.3 Rafraîchir les jetons

- **Endpoint:** `POST /api/auth/token/refresh`
- **Auth:** Non (envoyer le refresh dans le corps)
- **Content-Type:** `application/json`

#### Request body

```json
{
  "refresh": "<jwt_refresh>"
}
```

#### Success response (200)

Réponse standard Simple JWT (nouveau `access`, et souvent un nouveau `refresh` si rotation activée).

---

## 2) Vidéos

### 2.1 Lister le feed

- **Endpoint:** `GET /api/videos`
- **Auth:** Non (sauf `feed=following`, voir ci‑dessous)
- **Pagination:** curseur (`next` / `previous` / `results`)

#### Query params `feed`

| Valeur       | Description |
|-------------|-------------|
| *(absent)*  | Ordre chronologique inverse (récent d’abord). |
| `trending`  | Score tendance (vues, likes, commentaires). |
| `for_you`   | Fil type « Pour toi » : tendance limitée aux **30 derniers jours**. |
| `following` | Uniquement les vidéos des comptes que **vous** suivez. **JWT obligatoire** ; sans auth, réponse vide. |

#### Exemple de ligne dans `results`

```json
{
  "id": 10,
  "user": 1,
  "username": "alice",
  "video_url": "http://74.208.50.178/media/videos/clip.mp4",
  "thumbnail_url": null,
  "sound": null,
  "caption": "Best noodles near campus",
  "latitude": "48.856600",
  "longitude": "2.352200",
  "created_at": "2026-04-29T08:30:00Z",
  "views_count": 12,
  "likes_count": 4,
  "comments_count": 2
}
```

Si une vidéo utilise un son catalogue, `sound` est un objet `{ "id", "title", "file", "created_at" }` au lieu de `null`.

### 2.2 Créer une vidéo

- **Endpoint:** `POST /api/videos`
- **Auth:** Oui (JWT)
- **Content-Type:** `multipart/form-data`

#### Form fields

- `video_url` (fichier, obligatoire)
- `thumbnail` (image **optionnelle**, jpeg/png/webp — vignette grille profil / catalogue)
- `caption` (string, optionnel)
- `sound` (int, **optionnel** : id d’un son existant, voir section Sons)
- `latitude`, `longitude` (decimal, optionnels)

### 2.3 Détail d’une vidéo

- **Endpoint:** `GET /api/videos/{id}`
- **Auth:** Non
- **Effet:** incrémente `views_count`

### 2.4 Vidéos à proximité

- **Endpoint:** `GET /api/videos/nearby`
- **Auth:** Non

#### Query params requis

- `lat`, `lng`

#### Query params optionnels

- `radius_km` (défaut `3`)

#### Exemple

`GET /api/videos/nearby?lat=48.8566&lng=2.3522&radius_km=5`

### 2.5 Like / Unlike (toggle)

- **Endpoint:** `POST /api/videos/{id}/like`
- **Auth:** Oui

Comportement : crée le like s’il n’existe pas, sinon le supprime. Une notification « like » est envoyée au propriétaire de la vidéo (sauf si vous likez votre propre vidéo).

- **201** `{ "liked": true }` — like créé  
- **200** `{ "liked": false }` — like retiré  

### 2.6 Commentaires — liste

- **Endpoint:** `GET /api/videos/{id}/comments`
- **Auth:** Non
- **Pagination:** curseur

### 2.7 Commentaires — création

- **Endpoint:** `POST /api/videos/{id}/comment`
- **Auth:** Oui
- **Content-Type:** `application/json`

#### Request body

```json
{
  "text": "Excellent spot!"
}
```

Une notification « comment » est envoyée au propriétaire de la vidéo (sauf commentaire sur sa propre vidéo).

### 2.8 Favoris (bookmark)

- **Endpoint:** `POST /api/videos/{id}/bookmark` — enregistrer  
- **Endpoint:** `DELETE /api/videos/{id}/bookmark` — retirer  
- **Auth:** Oui  

Réponses typiques : `{ "saved": true }`, `{ "saved": false, "removed": true }`.

---

## 3) Utilisateurs et social

Règle **URLs médias** : `avatar`, `video_url`, `thumbnail_url` sont renvoyés en **URL absolue** lorsque la requête inclut un hôte (cas nominal navigateur / client avec `Host` ou reverse-proxy).

### 3.1 Profil connecté — lecture

- **Endpoint:** `GET /api/users/me`
- **Auth:** Oui (JWT)

#### Réponse (schéma)

```json
{
  "id": 1,
  "username": "alice",
  "email": "alice@example.com",
  "bio": "food lover",
  "avatar": "https://…/media/avatars/alice.jpg",
  "followers_count": 12,
  "following_count": 5,
  "videos_count": 8,
  "created_at": "2026-01-01T10:00:00Z",
  "latitude": "48.856600",
  "longitude": "2.352200"
}
```

Les **compteurs** sont alignés avec les agrégations en base (même source que les listes paginées).

### 3.2 Profil connecté — mise à jour

- **Endpoint:** `PATCH /api/users/me`
- **Auth:** Oui
- **Content-Type:** `application/json`

#### Corps JSON partiel accepté

| Champ       | Effet |
|------------|--------|
| `username` | Nouveau pseudo (unicité **insensible à la casse** ; erreur **400** si déjà pris). |
| `bio`      | Texte ou chaîne vide. |
| `avatar`   | `null`, `""` : efface fichier avatar **et** URL externe. Chaîne **`https://...`** ou **`http://...`** : enregistre une URL externe (`avatar_url`) et supprime un éventuel fichier uploadé (cas flux pré-signé). |

#### Réponse

Objet complet au même format que **`GET /api/users/me`**.

### 3.3 Upload photo de profil (multipart)

- **Endpoint:** `POST /api/users/me/avatar`
- **Auth:** Oui
- **Content-Type:** `multipart/form-data`

Champs fichier acceptés : **`avatar`** ou **`file`** (une image).

#### Contraintes

- Types MIME : `image/jpeg`, `image/png`, `image/webp`
- Taille max : **5 Mo**

#### Succès (200)

```json
{
  "avatar": "https://…/media/avatars/nouveau.jpg"
}
```

Le fichier stocké remplace tout fichier précédent, réinitialise `avatar_url` et met à jour le champ fichier **`avatar`**.

### 3.4 Profil public

- **Endpoint:** `GET /api/users/{id}`
- **Auth:** Non (invité autorisé)

```json
{
  "id": 2,
  "username": "bob",
  "bio": null,
  "avatar": "https://…/media/avatars/bob.jpg",
  "followers_count": 10,
  "following_count": 3,
  "videos_count": 4,
  "is_followed_by_me": false
}
```

- **`is_followed_by_me`** : **`false`** si vous n’êtes pas authentifié ou si vous consultez votre propre fiche ; **`true`** si vous êtes abonné à cet utilisateur.

### 3.5 Vidéos publiées d’un utilisateur (grille profil)

- **Endpoint:** `GET /api/users/{id}/videos`
- **Auth:** Non
- **Pagination:** curseur (`next`, `previous`, `results`)

Chaque élément de `results` suit ce contrat (optimisé affichage grille / TikTok-like) :

```json
{
  "id": 10,
  "caption": "Plat du jour",
  "video_url": "https://…/media/videos/clip.mp4",
  "thumbnail_url": null,
  "likes_count": 4,
  "comments_count": 2,
  "views_count": 100,
  "created_at": "2026-04-29T08:30:00Z",
  "user": { "id": 2, "username": "bob" }
}
```

### 3.6 Abonnés / Abonnements

- **GET** `/api/users/{id}/followers` — abonnés  
- **GET** `/api/users/{id}/following` — abonnements  
- **Auth:** Non  
- **Pagination:** `{ count, next, previous, results }` — query **`limit`** (défaut **30**) et **`offset`**

Chaque entrée de `results` :

```json
{
  "id": 3,
  "username": "carol",
  "avatar": "https://…/media/avatars/carol.jpg"
}
```

### 3.7 Suivre / ne plus suivre

- **POST** `/api/users/{id}/follow` — suivre (notification « follow » chez la cible si nouvel abonnement)
- **DELETE** `/api/users/{id}/follow` — ne plus suivre  
- **Auth:** Oui  

Interdit de suivre son propre compte (`400`).

---

## 4) Recherche

- **Endpoint:** `GET /api/search`
- **Auth:** Non

#### Query params

- `q` (string, **obligatoire**) — terme recherché  
- `type` (optionnel) : `all` (défaut), `users`, ou `videos`  

`users` : filtre sur le **username** (insensible à la casse).  
`videos` : filtre sur la **légende** (`caption`).

#### Exemple

`GET /api/search?q=noodles&type=all`

#### Réponse (schéma)

```json
{
  "query": "noodles",
  "type": "all",
  "users": [],
  "videos": []
}
```

---

## 5) Sons (catalogue audio)

- **GET** `/api/sounds` — liste  
- **GET** `/api/sounds/{id}` — détail  
- **POST** `/api/sounds` — créer (JWT, `multipart/form-data` : `title`, `file`)  

Les fichiers sont exposés comme les autres médias (URL MinIO / média public selon config).

---

## 6) Favoris (liste globale)

- **Endpoint:** `GET /api/bookmarks`
- **Auth:** Oui
- **Pagination:** curseur  

Chaque élément inclut la vidéo complète et la date d’enregistrement :

```json
{
  "id": 1,
  "created_at": "2026-05-03T10:00:00Z",
  "video": { }
}
```

---

## 7) Notifications

- **GET** `/api/notifications` — liste (JWT), pagination curseur  
- **GET** `/api/notifications/{id}` — détail  

Types possibles (`kind`) : `like`, `comment`, `follow`.

### 7.1 Marquer comme lue

- **POST** `/api/notifications/{id}/read`

### 7.2 Tout marquer comme lu

- **POST** `/api/notifications/read-all`

---

## 8) Reviews

### 8.1 Lister les reviews

- **Endpoint:** `GET /api/reviews`
- **Auth:** Non
- **Pagination:** activée

### 8.2 Créer une review

- **Endpoint:** `POST /api/reviews`
- **Auth:** Oui
- **Content-Type:** `multipart/form-data`

#### Form fields

- `place_name` (obligatoire)
- `rating` (1 à 5)
- `comment`, `media`, `latitude`, `longitude` (optionnels)

---

## 9) Codes d’erreur standards

- `400` — payload invalide  
- `401` — token absent ou invalide  
- `403` — action interdite  
- `404` — ressource absente  
- `500` — erreur serveur  

---

## 10) Sécurité & bonnes pratiques client

- Stocker `refresh` et `access` de façon sécurisée.
- Renouveler l’`access` avant expiration via `/api/auth/token/refresh`.
- Envoyer `Authorization: Bearer` sur les routes protégées.
- Retries avec backoff ; ne pas embarquer de secrets backend dans l’app.

---

## 11) Exemples cURL rapides

### Refresh token

```bash
curl -X POST http://74.208.50.178/api/auth/token/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh":"<jwt_refresh>"}'
```

### Feed « Pour toi »

```bash
curl "http://74.208.50.178/api/videos?feed=for_you"
```

### Feed abonnements (JWT)

```bash
curl "http://74.208.50.178/api/videos?feed=following" \
  -H "Authorization: Bearer <access_token>"
```

### Liste des commentaires

```bash
curl "http://74.208.50.178/api/videos/10/comments"
```

### Mon profil et mise à jour

```bash
curl "http://74.208.50.178/api/users/me" \
  -H "Authorization: Bearer <access_token>"

curl -X PATCH "http://74.208.50.178/api/users/me" \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"bio":"Nouvelle bio","username":"nouveau_pseudo"}'

curl -X POST "http://74.208.50.178/api/users/me/avatar" \
  -H "Authorization: Bearer <access_token>" \
  -F "avatar=@/path/photo.jpg"
```

### Profil tiers et follow

```bash
curl "http://74.208.50.178/api/users/2"
curl "http://74.208.50.178/api/users/2/videos"
curl "http://74.208.50.178/api/users/2/followers?limit=30&offset=0"
curl -X POST "http://74.208.50.178/api/users/2/follow" \
  -H "Authorization: Bearer <access_token>"
```

### Recherche

```bash
curl "http://74.208.50.178/api/search?q=campus&type=videos"
```

### Notifications

```bash
curl "http://74.208.50.178/api/notifications" \
  -H "Authorization: Bearer <access_token>"
```

### Create video (existant)

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
