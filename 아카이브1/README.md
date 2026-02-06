# Splashtop JP Website Monitor & Analyzer

이 프로젝트는 Splashtop JP 웹사이트의 변화를 자동으로 감지하고 분석 보고서를 생성하는 도구입니다.

## 🚀 시작하기

### 🔹 Windows 사용자
1. **Python 설치 필수**: [python.org](https://www.python.org/downloads/)에서 최신 버전을 다운로드하여 설치합니다.
   - **중요**: 설치 시 반드시 **"Add Python to PATH"** 옵션에 체크하세요! (이걸 안 하면 실행이 안 됩니다.)
2. `run_monitor.bat` 파일을 더블 클릭합니다.
3. 자동으로 필요한 라이브러리를 설치하고 분석을 시작하며, 대시보드가 브라우저에서 열립니다.

### 🔹 macOS 사용자
1. 터미널을 열고 프로젝트 폴더로 이동합니다.
2. `chmod +x start_monitor.command` 명령어로 실행 권한을 부여합니다 (최초 1회).
3. `start_monitor.command` 파일을 더블 클릭하여 실행합니다.

---

## 🛠️ 주요 기능
- **보고서 형식의 변화 감지**: 이전 조사 시점 대비 수정, 신규, 삭제된 페이지를 체계적으로 리포트합니다.
- **자동 URL 발견 (Discovery)**: 모니터링 중 섹션 내에 새로운 링크가 생기면 자동으로 감시 명단에 추가합니다.
- **URL 정규화**: 마케팅 파라미터(`?af=...`) 등으로 인한 중복 체크를 방지합니다.
- **수동 URL 추가**: 대시보드 상단에서 특정 URL을 직접 추가하여 즉시 감시할 수 있습니다.

---

## 📂 파일 구조
- `smart_monitor.py`: 실제 분석 및 모니터링 엔진 (병렬 처리 지원)
- `server.py`: 대시보드 서빙 및 URL 추가 API 서버
- `index.html`: 분석 보고서 및 대시보드 프론트엔드
- `site_structure.json`: 모니터링 대상 URL 명단
- `site_report_meta.json`: 사이트 분석 요약 정보
- `requirements.txt`: 필요한 Python 라이브러리 목록

---

## ⚠️ 주의 사항
- 분석 도중 터미널 창(검은 창)을 닫으면 대시보드 서버가 종료됩니다. 분석 및 대시보드 확인이 끝난 후 닫아주세요.
