# Aniimax r13 · Web edition

[웹페이지 주소](https://korgenta.github.io/annimaxtokr.github.io/)

애니모 캠핑 생산 최적화 도구입니다. 지원 RV 레벨·시설 수·모듈 레벨·레시피는 공개 데이터 파일에서 읽습니다.
방문자용 데이터 편집 기능과 로컬 카탈로그 덮어쓰기는 포함하지 않습니다.
단일/병행 생산, 시설별 애니모 설정, 이벤트 작물, 레시피 최대 생산 비교 및 한국어/영어 표시를 지원합니다.

All calculations run in the browser using WebAssembly. No backend or analytics is used.
MathJax and HiGHS are bundled locally. The data editor and local catalog overrides are excluded.
Saved settings stay in the visitor’s browser. Sharing a setup creates a URL fragment containing that setup;
anyone receiving the complete link can read it. See [privacy.html](https://korgenta.github.io/annimaxtokr.github.io/privacy.html).

## 데이터 업데이트

1. 최신 `main`에서 [data/game-data.json](data/game-data.json)을 수정합니다. 새 RV 행에는 모든 시설의 최대 수·레벨, 네 모듈의 최대 레벨, `aniimo_max`를 입력합니다. `level_up_cost`는 그 RV에 도달하는 비용이며, 모르면 비워 둡니다.
2. 레시피는 `recipes`에 추가합니다. 시설·재료 ID, 생산 수치, `facility_level`, `module_requirement`, 필요한 경우 `min_rv_level`과 `special_unlock`, 번역을 함께 확인합니다. 건물을 추가하면 `facilities`와 모든 RV 행의 해당 시설 항목도 추가합니다(미해금은 `count: 0`).
3. 변경 사항을 `main`에 커밋합니다. Actions가 데이터 유효성·비공개 경로를 검사하고, RV 목록·상한·레시피 개수 안내를 반영하여 자동 게시합니다. 데이터만 바꿀 때 ZIP이나 SHA-256을 수정할 필요는 없습니다.
4. Actions의 성공 여부와 사이트의 새 레벨·시설·레시피를 확인합니다. 검사가 실패하면 새 버전은 게시되지 않습니다.

현재 파일에 없는 레벨과 수치는 추정하지 않습니다. 기존 생산 규칙을 사용하는 데이터 확장은 코드 수정 없이 반영됩니다. 새 능력·모듈 종류·기후 동작 등 계산 규칙이 바뀌면 엔진 수정이 필요할 수 있습니다. 공개 파일이므로 게임 원본, 개인 메모·경로·계정 정보는 넣지 마세요.

로컬 확인에는 Python 3와 Node.js가 필요합니다:

```sh
python scripts/build_site.py
node --test tests/catalog.test.mjs
python -m unittest discover -s tests -p test_build.py
```

`--catalog <JSON 경로>`와 `--output <출력 폴더>`로 별도 검증용 빌드를 만들 수도 있습니다. 편집기의 저장 버튼은 브라우저에만 저장하므로, 관리용 편집기를 사용했다면 JSON 내보내기로 공개용 데이터를 준비해야 합니다.

## 배포 구조

`data/game-data.json`이 유일한 배포 데이터 원본입니다. `site.zip`에는 검증된 r13 실행 파일과 자체 포함 라이브러리만 들어 있으며, 데이터 파일과 편집기는 없습니다. `site.sha256`은 실행 파일 ZIP의 무결성을 확인합니다. 실행 코드를 변경할 때만 ZIP과 해시를 함께 갱신합니다.

GitHub Pages의 Source는 **GitHub Actions**로 유지합니다. 워크플로는 `scripts/build_site.py`로 `_site`를 만들고 테스트를 통과한 `_site`만 게시합니다. 빌드 스크립트·테스트·원본 ZIP은 사이트에 포함되지 않습니다.

The repo contains public site assets, data and build checks; no desktop executables, raw game archives, local saves, credentials or build-machine paths.
Source files and the calculator’s game reference data are public as part of the web site.

Original project: [ae-bii/aniimax](https://github.com/ae-bii/aniimax). MIT license retained.
Third-party licenses: [THIRD_PARTY_NOTICES.txt](THIRD_PARTY_NOTICES.txt).
