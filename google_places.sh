curl --get https://serpapi.com/search \
 -d api_key=$GOOGLE_API_KEY \
 -d engine="google_local" \
 -d google_domain="google.es" \
 -d q="RESTAURANTES" \
 -d hl="es" \
 -d gl="es" \
 -d location="Madrid,+Community+of+Madrid,+Spain"
 > restaurants.json