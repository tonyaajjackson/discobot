if [ -z "$1" ]; then
    echo "No file specified"
    exit 1
fi

set -a
source $1
set +a