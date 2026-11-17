#!/bin/sh
# Rebuild every picture and the PDF manual.
#   ./build.sh
# Needs: Python 3 with numpy and manifold3d, Node.js with the "playwright" and "three" packages
# (npm install three playwright; npx playwright install chromium).
set -e
cd "$(dirname "$0")"
THREE="${THREE:-$(node -e "console.log(require.resolve('three/build/three.min.js'))")}"
rm -rf .scenes && python3 scenes.py .scenes
node render.js "$THREE" .scenes img
rm -rf .scenes
python3 build_manual.py
node make_pdf.js
