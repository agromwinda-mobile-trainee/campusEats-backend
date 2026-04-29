#!/usr/bin/env bash

set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost:8000}"
API_URL="${BASE_URL}/api"
TMP_DIR="$(mktemp -d)"

cleanup() {
  rm -rf "${TMP_DIR}"
}
trap cleanup EXIT

log() {
  printf "\n[%s] %s\n" "$(date +"%H:%M:%S")" "$1"
}

fail() {
  echo "ERREUR: $1" >&2
  exit 1
}

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || fail "Commande requise absente: $1"
}

http_json() {
  # Usage: http_json METHOD URL DATA_FILE OUT_FILE
  local method="$1"
  local url="$2"
  local data_file="$3"
  local out_file="$4"
  local code

  code="$(
    curl -sS -o "${out_file}" -w "%{http_code}" \
      -X "${method}" "${url}" \
      -H "Content-Type: application/json" \
      --data @"${data_file}"
  )"
  echo "${code}"
}

http_auth_json() {
  # Usage: http_auth_json METHOD URL TOKEN DATA_FILE OUT_FILE
  local method="$1"
  local url="$2"
  local token="$3"
  local data_file="$4"
  local out_file="$5"
  local code

  code="$(
    curl -sS -o "${out_file}" -w "%{http_code}" \
      -X "${method}" "${url}" \
      -H "Authorization: Bearer ${token}" \
      -H "Content-Type: application/json" \
      --data @"${data_file}"
  )"
  echo "${code}"
}

http_auth_multipart() {
  # Usage: http_auth_multipart URL TOKEN OUT_FILE [curl -F ...]
  local url="$1"
  local token="$2"
  local out_file="$3"
  shift 3
  local code

  code="$(
    curl -sS -o "${out_file}" -w "%{http_code}" \
      -X POST "${url}" \
      -H "Authorization: Bearer ${token}" \
      "$@"
  )"
  echo "${code}"
}

extract_json_field() {
  # Usage: extract_json_field FILE FIELD
  local file="$1"
  local field="$2"
  python3 -c "import json; import sys; d=json.load(open(sys.argv[1])); print(d.get(sys.argv[2], ''))" "${file}" "${field}"
}

assert_code() {
  local got="$1"
  local expected="$2"
  local context="$3"
  if [[ "${got}" != "${expected}" ]]; then
    echo "Réponse inattendue pour ${context}: attendu ${expected}, reçu ${got}" >&2
    return 1
  fi
  return 0
}

wait_api() {
  log "Attente de disponibilité de l'API sur ${BASE_URL}..."
  for _ in $(seq 1 45); do
    if curl -sS "${API_URL}/videos" >/dev/null 2>&1; then
      log "API joignable."
      return 0
    fi
    sleep 2
  done
  fail "API indisponible après 90 secondes. Vérifie 'docker compose up --build'."
}

main() {
  require_cmd curl
  require_cmd python3

  wait_api

  local rand
  rand="$(date +%s)"
  local username="smoke_${rand}"
  local email="${username}@example.com"
  local password="StrongPass123"

  local register_body="${TMP_DIR}/register.json"
  local register_out="${TMP_DIR}/register.out.json"
  cat > "${register_body}" <<EOF
{"username":"${username}","email":"${email}","password":"${password}","bio":"smoke test"}
EOF

  log "1/9 Register utilisateur"
  local code
  code="$(http_json POST "${API_URL}/auth/register" "${register_body}" "${register_out}")"
  assert_code "${code}" "201" "register" || fail "$(cat "${register_out}")"

  local login_body="${TMP_DIR}/login.json"
  local login_out="${TMP_DIR}/login.out.json"
  cat > "${login_body}" <<EOF
{"username":"${username}","password":"${password}"}
EOF

  log "2/9 Login utilisateur"
  code="$(http_json POST "${API_URL}/auth/login" "${login_body}" "${login_out}")"
  assert_code "${code}" "200" "login" || fail "$(cat "${login_out}")"

  local token
  token="$(extract_json_field "${login_out}" "access")"
  [[ -n "${token}" ]] || fail "Token JWT access absent."

  local video_file="${TMP_DIR}/video.mp4"
  printf "fake-mp4-content\n" > "${video_file}"
  local create_video_out="${TMP_DIR}/create_video.out.json"

  log "3/9 Création vidéo"
  code="$(
    http_auth_multipart "${API_URL}/videos" "${token}" "${create_video_out}" \
      -F "caption=Video smoke test" \
      -F "latitude=48.8566" \
      -F "longitude=2.3522" \
      -F "video_url=@${video_file};type=video/mp4"
  )"
  assert_code "${code}" "201" "create video" || fail "$(cat "${create_video_out}")"

  local video_id
  video_id="$(extract_json_field "${create_video_out}" "id")"
  [[ -n "${video_id}" ]] || fail "ID vidéo absent."

  local list_out="${TMP_DIR}/list_videos.out.json"
  log "4/9 Lecture feed vidéos"
  code="$(curl -sS -o "${list_out}" -w "%{http_code}" "${API_URL}/videos")"
  assert_code "${code}" "200" "list videos" || fail "$(cat "${list_out}")"

  local retrieve_out="${TMP_DIR}/retrieve_video.out.json"
  log "5/9 Lecture détail vidéo"
  code="$(curl -sS -o "${retrieve_out}" -w "%{http_code}" "${API_URL}/videos/${video_id}")"
  assert_code "${code}" "200" "retrieve video" || fail "$(cat "${retrieve_out}")"

  local like_out="${TMP_DIR}/like.out.json"
  log "6/9 Like vidéo"
  code="$(curl -sS -o "${like_out}" -w "%{http_code}" -X POST "${API_URL}/videos/${video_id}/like" -H "Authorization: Bearer ${token}")"
  assert_code "${code}" "201" "like video" || fail "$(cat "${like_out}")"

  local comment_body="${TMP_DIR}/comment.json"
  local comment_out="${TMP_DIR}/comment.out.json"
  cat > "${comment_body}" <<EOF
{"text":"Comment smoke test"}
EOF

  log "7/9 Comment vidéo"
  code="$(http_auth_json POST "${API_URL}/videos/${video_id}/comment" "${token}" "${comment_body}" "${comment_out}")"
  assert_code "${code}" "201" "comment video" || fail "$(cat "${comment_out}")"

  local review_media="${TMP_DIR}/review.jpg"
  printf "fake-jpg-content\n" > "${review_media}"
  local review_out="${TMP_DIR}/review.out.json"

  log "8/9 Création review"
  code="$(
    http_auth_multipart "${API_URL}/reviews" "${token}" "${review_out}" \
      -F "place_name=Cafeteria Smoke Test" \
      -F "rating=5" \
      -F "comment=Top quality" \
      -F "latitude=48.8566" \
      -F "longitude=2.3522" \
      -F "media=@${review_media};type=image/jpeg"
  )"
  assert_code "${code}" "201" "create review" || fail "$(cat "${review_out}")"

  local nearby_out="${TMP_DIR}/nearby.out.json"
  log "9/9 Feed nearby"
  code="$(curl -sS -o "${nearby_out}" -w "%{http_code}" "${API_URL}/videos/nearby?lat=48.8566&lng=2.3522&radius_km=3")"
  assert_code "${code}" "200" "nearby feed" || fail "$(cat "${nearby_out}")"

  log "SMOKE TEST OK - tous les endpoints critiques répondent correctement."
}

main "$@"
