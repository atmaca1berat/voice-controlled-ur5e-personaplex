#!/bin/bash
# Once PP health, ok ise trial calistir; degilse PP_DOWN yaz ve dur.
CODE=$(curl -s -m 5 -o /dev/null -w '%{http_code}' http://192.168.1.103:8081/health)
if [ "$CODE" != "200" ]; then
  echo "PP_DOWN (http=$CODE) — trial CALISTIRILMADI. Mac'te PP'yi restart et."
  exit 0
fi
echo "PP_OK (http=200) — trial baslatiliyor"
sed 's/\r$//' ~/test_scripts/trial_ppactive.sh | bash
