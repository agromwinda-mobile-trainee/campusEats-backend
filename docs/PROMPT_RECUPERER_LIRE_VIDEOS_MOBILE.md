# Prompt - Recuperer et Lire les Videos (React Native)

Copie/colle ce prompt dans ton assistant IA pour generer uniquement la partie mobile qui consomme et lit les videos depuis l'API CampusEats.

---

## Prompt

Tu es un **Senior React Native Engineer** expert en **Expo**, **TypeScript**, **React Query**, **gestion reseau mobile** et **lecture video performante**.

Ta mission: implementer une solution robuste pour **recuperer le feed video depuis l'API** et **lire les videos dans une UI verticale style TikTok**.

## 1) Contexte API (a respecter strictement)

Base URL backend:
- `http://74.208.50.178`

Endpoints utiles:
- `GET /api/videos` (feed principal)
- `GET /api/videos?feed=trending` (trending)
- `GET /api/videos/nearby?lat=...&lng=...&radius_km=3` (nearby)
- `GET /api/videos/{id}` (detail)

Format reponse attendu (DRF pagination possible):
- soit un tableau direct
- soit un objet `{ next, previous, results }`

Champs importants d'une video:
- `id`
- `video_url` (URL HTTP publique du fichier MP4 a passer au lecteur)
- `caption`
- `username`
- `views_count`
- `likes_count`
- `comments_count`

### URLs fichiers video (comportement backend attendu)

Sur le deploiement VPS avec Nginx + MinIO:

- L'API renvoie une URL **absolue** du type `http://<HOST>/media/videos/<fichier>.mp4`.
- Le prefix `/media/` est servi par **Nginx**, qui proxifie vers le bucket MinIO (`campuseats-media`). Le mobile ne doit **pas** appeler directement le port MinIO (9000), sauf configuration exceptionnelle exposee publiquement.

Cote backend (reference pour debug, pas a coder dans l'app):

- Variables `.env`: `MEDIA_PUBLIC_DOMAIN=<IP_OU_DOMAINE>/media` et `MEDIA_PUBLIC_PROTOCOL=http:` (ou `https:` si TLS).
- Les uploads existants en base doivent correspondre a des objets presents dans MinIO; sinon `video_url` renverra 404 meme si l'API est OK.

### Lecture dans l'app

- Utiliser **`video_url` tel quel** comme `uri` du lecteur (`expo-av` / `Video`) lorsque l'URL est deja absolue (cas nominal VPS).
- Garder un helper `toAbsoluteMediaUrl(video_url, API_BASE_URL)` **uniquement** si `video_url` est parfois **relatif** (ex. `/media/videos/foo.mp4` sur un autre environnement): dans ce cas prefixer avec `API_BASE_URL` sans slash double.

## 2) Objectif exact

Construire un module mobile qui:
1. recupere une liste de videos depuis l'API
2. normalise la reponse paginee/non paginee
3. normalise `video_url` (absolu ou prefixe avec la base API si relatif)
4. affiche un feed vertical plein ecran
5. lit automatiquement la video visible
6. preload la video suivante pour fluidite
7. gere loading, erreur et empty state proprement

## 3) Contraintes techniques

- Expo + TypeScript strict
- `@tanstack/react-query` pour fetch/cache/pagination
- `expo-av` (ou `expo-video` si tu justifies)
- `FlatList` verticale avec `pagingEnabled`
- code modulaire et maintenable
- aucune logique metier dans les composants UI si possible

## 4) Ce que tu dois implementer

Genere le code **pret a copier/coller** pour:

1. `src/shared/config/env.ts`
   - `API_BASE_URL`

2. `src/shared/types/video.ts`
   - types `VideoItem`, `PaginatedResponse<T>`

3. `src/features/feed/api/videos.api.ts`
   - fonction `fetchVideos(params)` pour:
     - feed principal
     - trending
     - nearby
   - normalisation pagination (`results` vs array)
   - helper `toAbsoluteMediaUrl(video_url, API_BASE_URL)`

4. `src/features/feed/hooks/useVideosFeed.ts`
   - hook React Query (`useInfiniteQuery`)
   - support pagination via `next`
   - expose `videos`, `fetchNextPage`, `hasNextPage`, `isLoading`, `isError`, `refetch`

5. `src/features/feed/components/VideoFeedItem.tsx`
   - composant lecture video
   - props `isActive` pour play/pause automatique
   - `resizeMode="cover"`
   - fallback UI en cas d'erreur de lecture

6. `src/features/feed/screens/FeedScreen.tsx`
   - `FlatList` verticale plein ecran
   - detecte item visible (`onViewableItemsChanged`)
   - active uniquement la video visible
   - infinite scroll (`onEndReached`)
   - loading / error / empty states

7. `src/features/feed/utils/flattenInfinitePages.ts`
   - utilitaire pour aplatir proprement les pages React Query

## 5) Points de robustesse obligatoires

- timeout reseau raisonnable
- gestion des erreurs HTTP (message utilisateur + retry)
- pas de crash si `video_url` absent: ignorer item ou afficher placeholder
- si lecture echoue (404 reseau): afficher message ou retry — verifier d'abord que `HEAD` ou `GET` sur `video_url` retourne 200 depuis un client externe
- **Android / HTTP cleartext**: si `video_url` est en `http://`, l'app doit autoriser le traffic HTTP pour ce host (network security config / cleartext), ou le backend doit servir en HTTPS
- nettoyage memo/callback pour limiter les re-renders
- keyExtractor stable base sur `id`

## 6) UX minimale requise

- scroll snap vertical fluide
- auto-play uniquement sur item actif
- pull-to-refresh
- indicateur de chargement bas de liste
- affichage `caption` + `username` en overlay

## 7) Format de ta reponse

Reponds dans cet ordre:
1. arborescence fichiers
2. code complet fichier par fichier
3. explication courte des choix techniques
4. etapes de test manuel sur mobile

Ne donne pas une reponse theorique. Donne du code executable, propre et directement utilisable.

## 8) Checklist tests (API + fichiers)

A executer depuis une machine qui voit le backend (pas obligatoirement le telephone):

1. `GET http://<HOST>/api/videos` — verifier `200` et que chaque item contient `video_url`.
2. Pour une URL extraite: `curl -I "<video_url>"` — attendre `200` et un `Content-Type` video (`video/mp4` ou `application/octet-stream` selon serveur).
3. Sur appareil reel ou emulateur: charger la meme `video_url` dans le lecteur; si echec, distinguer probleme reseau/DNS/HTTP cleartext vs URL invalide.

Si l'etape 1 OK mais l'etape 2 en **404**, le probleme est **cote stockage / proxy / env** (`MEDIA_PUBLIC_DOMAIN`, Nginx `/media/`, bucket MinIO), pas le client mobile.

