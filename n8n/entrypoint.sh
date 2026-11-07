#!/bin/sh
# Import dan publish workflow sekali saja, lalu jalankan n8n.
MARK=/home/node/.n8n/.workflow_imported

if [ ! -f "$MARK" ]; then
  [ -z "$APIFY_TOKEN" ] && echo ">> PERINGATAN: APIFY_TOKEN kosong di file .env"
  sed "s|GANTI_DENGAN_TOKEN_APIFY|${APIFY_TOKEN}|g" /workflow/workflow_facebook_apify.json > /tmp/wf.json
  if n8n import:workflow --input=/tmp/wf.json && n8n publish:workflow --id=hargaPasaranHp1; then
    touch "$MARK"
    echo ">> Workflow berhasil diimpor dan dipublish."
  else
    echo ">> Import/publish otomatis gagal. Impor manual lewat editor n8n (lihat DOCKER.md)."
  fi
  rm -f /tmp/wf.json
fi

exec n8n start
