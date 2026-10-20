#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SERVICES_DIR="${ROOT_DIR}/services"

if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
    cat <<'EOF'
Build all Docker images for services under services/.

Usage:
  ./scripts/build_services.sh

Environment:
  DOCKER_IMAGE_PREFIX  Image prefix, default: rta
EOF
    exit 0
fi

if ! command -v docker >/dev/null 2>&1; then
    echo "Error: Docker is not installed or not available on PATH." >&2
    exit 1
fi

if [ ! -d "${SERVICES_DIR}" ]; then
    echo "Error: services directory not found: ${SERVICES_DIR}" >&2
    exit 1
fi

found_service=0

while IFS= read -r dockerfile; do
    found_service=1
    service_dir="$(dirname "${dockerfile}")"
    service_name="$(basename "${service_dir}")"
    image_name="${DOCKER_IMAGE_PREFIX:-rta}-${service_name}"

    echo "Building ${image_name} from ${service_dir}..."
    docker build \
        --file "${dockerfile}" \
        --tag "${image_name}" \
        "${service_dir}"
done < <(find "${SERVICES_DIR}" -mindepth 2 -maxdepth 2 -type f -name Dockerfile -print | sort)

if [ "${found_service}" -eq 0 ]; then
    echo "No service Dockerfiles found under ${SERVICES_DIR}." >&2
    exit 1
fi

echo "Service image builds completed successfully."
