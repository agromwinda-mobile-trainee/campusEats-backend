# Prompt - Intégrer les routes « social / TikTok » (client mobile)

Copie-colle ce bloc dans ton assistant IA pour implémenter ou compléter **le client** (React Native / Expo recommandé) qui consomme les routes ajoutées au backend CampusEats : profils, follow, feeds `for_you` / `following`, commentaires en lecture, favoris, recherche, sons, notifications, refresh JWT.

**Référence normative côté contrat HTTP** : `docs/API_DOCUMENTATION.md` (en cas de doute sur un champ ou un code HTTP, s’y reporter).

---

## Prompt (à coller)

Tu es un **développeur mobile senior** (Expo, TypeScript, React Query). Tu dois **intégrer toutes les routes listées ci-dessous** dans une app existante ou un module dédié, avec une architecture propre (services API, hooks, types), sans recoder le backend.

### Règles communes

- **Base URL** configurable (ex. `http://74.208.50.178` en dev / prod).
- **Sans slash final** sur les chemins (ex. `/api/videos`, pas `/api/videos/`).
- **JWT** : en-tête `Authorization: Bearer <access_token>` sur toute route marquée *Auth: oui*.
- **401** : tenter `POST /api/auth/token/refresh` avec le `refresh` stocké, puis rejouer la requête une fois ; si échec, déconnexion / écran login.
- **Pagination curseur** : les réponses sont du type `{ next, previous, results }` ; pour charger la suite, **GET sur l’URL absolue `next`** (ne pas reconstruire le curseur à la main).
- **Pagination offset** (followers / following) : utiliser les paramètres standard DRF `limit` / `offset` si présents dans les réponses paginées.

---

### 1. Authentification — refresh

| Méthode | Chemin | Auth | Corps |
|--------|--------|------|--------|
| POST | `/api/auth/token/refresh` | Non | `{ "refresh": "<jwt_refresh>" }` |

**À faire côté app** : inter cepteur HTTP ou wrapper `fetch` qui, sur 401, appelle refresh, met à jour les tokens en secure storage, puis retry.

---

### 2. Vidéos — feeds étendus

Toutes en **GET** `/api/videos` avec query :

| `feed` | Comportement | Auth |
|--------|----------------|------|
| *(absent)* | Chronologique inverse | Non |
| `trending` | Tendance | Non |
| `for_you` | « Pour toi » (fenêtre récente + score) | Non |
| `following` | Vidéos des comptes suivis | **Oui** ; sans token le backend peut renvoyer une liste vide |

**Champs supplémentaires dans chaque vidéo** : `sound` peut être `null` ou un objet `{ id, title, file, created_at }`. Afficher un libellé son si présent ; à l’upload, permettre de choisir un `sound` (id) optionnel.

**Création** `POST /api/videos` (multipart) : champs existants + optionnel **`sound`** (id numérique du son).

---

### 3. Vidéos — commentaires en lecture

| Méthode | Chemin | Auth |
|--------|--------|------|
| GET | `/api/videos/{id}/comments` | Non |

Pagination curseur sur la liste. Utiliser pour un **panneau commentaires** (bottom sheet) avec infinite scroll vers le haut ou le bas selon le tri exposé par l’API.

*(Le POST commentaire existant reste `POST /api/videos/{id}/comment` avec JSON `{ "text": "..." }`.)*

---

### 4. Vidéos — favoris (bookmark)

| Méthode | Chemin | Auth | Réponse typique |
|--------|--------|------|------------------|
| POST | `/api/videos/{id}/bookmark` | Oui | `{ "saved": true }` |
| DELETE | `/api/videos/{id}/bookmark` | Oui | `{ "saved": false, "removed": ... }` |

**Liste globale des favoris** : `GET /api/bookmarks` (Auth oui, pagination curseur). Chaque item contient `video` enrichie + `created_at`.

**UX** : icône « sauvegarder » sur le lecteur + écran « Enregistrés » qui réutilise les cartes vidéo du feed.

---

### 5. Utilisateurs — profil et social

| Méthode | Chemin | Auth | Notes |
|--------|--------|------|--------|
| GET | `/api/users/me` | Oui | `CurrentUser` : `email`, `bio`, **`avatar` URL absolue**, **`followers_count` / `following_count` / `videos_count`**, **`created_at`**, lat/long |
| PATCH | `/api/users/me` | Oui | JSON partiel : **`username`**, **`bio`**, **`avatar`** (`""` ou `null` pour effacer ; `https://…` pour URL externe après upload pré-signé). Réponse = même forme que GET `/me`. Erreur **400** si pseudo pris. |
| POST | `/api/users/me/avatar` | Oui | **Multipart** : champ fichier **`avatar`** ou **`file`** (jpeg/png/webp, max **5 Mo**). Réponse `{ "avatar": "<url absolue>" }`. |
| GET | `/api/users/{id}` | Non | Profil public ; **`is_followed_by_me`** toujours présent (`false` si anonyme ou self-view). |
| GET | `/api/users/{id}/videos` | Non | Grille profil : chaque item a **`user`: `{ id, username }`**, **`video_url`**, **`thumbnail_url`**, compteurs, etc. (curseur `next`/`results`). |
| GET | `/api/users/{id}/followers` | Non | Pagination **`limit`** (défaut 30) / **`offset`** ; `results[]` avec **`avatar` absolu**. |
| GET | `/api/users/{id}/following` | Non | Idem. |
| POST | `/api/users/{id}/follow` | Oui | Suivre |
| DELETE | `/api/users/{id}/follow` | Oui | Ne plus suivre |

**Navigation** : depuis une vidéo, tap sur l’auteur → écran profil → onglets ou sections « Vidéos » / infos follower.

**Vidéos (feed général)** : les objets incluent aussi **`thumbnail_url`** (nullable) et **`video_url`** en URL absolue lorsque la requête porte un `Host` valide.

**Création vidéo** : champ multipart optionnel **`thumbnail`** (image) pour alimenter la vignelle profil / cartes.

---

### 6. Recherche

| Méthode | Chemin | Query |
|--------|--------|--------|
| GET | `/api/search` | `q` (obligatoire), `type` optionnel : `all` \| `users` \| `videos` |

Réponse : `{ query, type, users: [...], videos: [...] }`. Prévoir **debounce** sur le champ de recherche (ex. 300 ms).

---

### 7. Sons

| Méthode | Chemin | Auth |
|--------|--------|------|
| GET | `/api/sounds` | Lecture publique |
| GET | `/api/sounds/{id}` | Lecture publique |
| POST | `/api/sounds` | Création : Auth, multipart `title` + `file` |

**À faire** : écran ou modal « Choisir un son » avant publication (liste paginée si volumineuse), et envoi de `sound` = id dans `POST /api/videos`.

---

### 8. Notifications

| Méthode | Chemin | Auth |
|--------|--------|------|
| GET | `/api/notifications` | Oui (liste paginée) |
| GET | `/api/notifications/{id}` | Oui |
| POST | `/api/notifications/{id}/read` | Oui |
| POST | `/api/notifications/read-all` | Oui |

Champs utiles : `kind` (`like` \| `comment` \| `follow`), `actor`, `actor_username`, `video`, `read_at`, `created_at`.

**À faire** : écran cloche + badge non lu ; pas de WebSocket dans ce backend — **polling** raisonnable (ex. toutes les 30–60 s quand l’app est active) ou refresh au focus.

---

### 9. Livrables attendus (génère le code)

1. **Types TypeScript** alignés sur les JSON (User public, Video avec `sound`, Notification, Bookmark row, paginations).
2. **Client HTTP** centralisé (base URL, headers, refresh token).
3. **Hooks React Query** : `useFeed`, `useVideoComments`, `useBookmarks`, `useUserProfile`, `useFollow`, `useNotifications`, `useSearch`, `useSounds`, avec invalidation de cache cohérente (ex. après follow → invalider profil + feed `following`).
4. **Écrans ou composants** minimalistes mais utilisables : profil créateur, recherche, favoris, notifications, sélecteur de son à la publication.

### Contraintes

- Pas de logique métier dans les composants UI purs si possible.
- Gestion explicite des états loading / error / empty.
- Respect strict des chemins et méthodes ci-dessus.

---

## Références projet

- Contrat détaillé et exemples : `docs/API_DOCUMENTATION.md`
- Feed vidéo + lecteur : `docs/PROMPT_RECUPERER_LIRE_VIDEOS_MOBILE.md` et `docs/PROMPT_REACT_NATIVE_TIKTOK_APP.md` si présents
