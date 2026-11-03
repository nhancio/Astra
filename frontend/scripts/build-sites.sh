#!/usr/bin/env bash
# Builds unified Astra AI static export (Landing + in-place App Hub):
#   out/ -> tryastra.web.app & astra.nhancio.com
#   out-admin/ -> astraadmin.web.app
set -euo pipefail
cd "$(dirname "$0")/.."

rm -rf out out-app out-admin
npx next build
mkdir -p out-admin
cp out/admin.html out-admin/index.html
cp -R out/_next out-admin/_next
cp -R out/brand out-admin/brand
printf 'User-agent: *\nDisallow: /\n' > out-admin/robots.txt
echo "Built out/ (Astra AI) and out-admin/ (admin portal)"
