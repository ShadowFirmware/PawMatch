#!/bin/bash
# Ejecuta el análisis de SonarQube para ambos repos.
# Uso: ./scan.sh <token-de-sonarqube>
# El token se genera en: http://IP_SERVIDOR:9000 → My Account → Security

SONAR_TOKEN=${1:-""}
SONAR_HOST="http://sonarqube:9000"

if [ -z "$SONAR_TOKEN" ]; then
    echo "Uso: ./scan.sh <token>"
    echo "Genera tu token en http://IP_SERVIDOR:9000 → My Account → Security"
    exit 1
fi

echo "🔍 Escaneando backend..."
docker run --rm \
    --network pawmatch_default \
    -v "$(pwd)":/usr/src \
    sonarsource/sonar-scanner-cli \
    -Dsonar.host.url=$SONAR_HOST \
    -Dsonar.token=$SONAR_TOKEN \
    -Dsonar.projectBaseDir=/usr/src

echo ""
echo "🔍 Escaneando frontend..."
docker run --rm \
    --network pawmatch_default \
    -v "$(pwd)/../404-not-found":/usr/src \
    sonarsource/sonar-scanner-cli \
    -Dsonar.host.url=$SONAR_HOST \
    -Dsonar.token=$SONAR_TOKEN \
    -Dsonar.projectBaseDir=/usr/src

echo ""
echo "✅ Escaneo completado. Revisa los resultados en http://IP_SERVIDOR:9000"
