#!/usr/bin/with-contenv /bin/bash
set -eo pipefail

[[ $DEBUG == true ]] && set -x

export VNC_PASSWORD=''
export DISPLAY=:11

case ${1} in
  help)
    echo "No help!"
    ;;
  start)
    /bin/s6-svc -wu -T 5000 -u /var/run/s6/services/tigervnc
    sleep 2
    /bin/s6-svc -wu -T 5000 -u /var/run/s6/services/websocketify
    sleep 2
    /bin/s6-svc -wu -T 5000 -u /var/run/s6/services/nginx
    sleep 2
    sudo --preserve-env -Hu user /app/vncmain.sh "$@"
    ;;
  *)
    exec "$@"
    ;;
esac

exit 0
