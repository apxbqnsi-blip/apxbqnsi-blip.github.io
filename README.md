# Aniimax r13 · RV 22 web edition

[웹페이지 주소](https://korgenta.github.io/annimaxtokr.github.io/)

애니모 캠핑 생산 최적화 도구입니다. RV 1–22 고정 데이터를 사용하며 데이터 편집 기능은 포함하지 않습니다.
단일/병행 생산, 시설별 애니모 설정, 이벤트 작물, 레시피 최대 생산 비교 및 한국어/영어 표시를 지원합니다.

All calculations run in the browser using WebAssembly. No backend or analytics is used.
MathJax and HiGHS are bundled locally. The data editor and local catalog overrides are excluded.
Saved settings stay in the visitor’s browser. Sharing a setup creates a URL fragment containing that setup;
anyone receiving the complete link can read it. See [privacy.html](https://korgenta.github.io/privacy.html).

GitHub Pages uses the repository Actions workflow to verify and unpack `site.zip`, then publish only the static site files. `.nojekyll` keeps the site static.
The repo contains only public site assets; no desktop executables, raw archives, local saves, credentials or build-machine paths.
Source files and the calculator’s game reference data are public as part of the web site.

Original project: [ae-bii/aniimax](https://github.com/ae-bii/aniimax). MIT license retained.
Third-party licenses: [THIRD_PARTY_NOTICES.txt](THIRD_PARTY_NOTICES.txt).
