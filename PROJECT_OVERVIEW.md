# Splashtop JP Website Monitor & Analyzer — 프로젝트 개요

> **목적**: Splashtop 일본 웹사이트(`www.splashtop.co.jp`)의 변화를 자동으로 감지하고, 신규/수정/삭제된 페이지를 시각적으로 보고하는 모니터링 시스템

---

## 1. 개발 배경

- Splashtop JP 웹사이트의 콘텐츠가 빈번하게 추가/변경되지만, 변경 사항을 수동으로 체크하기엔 페이지 수가 너무 많음
- WordPress 기반 사이트의 `wp-sitemap.xml`을 활용하여 효율적으로 전체 URL 목록을 확보하고, **차분(Diff) 조사**로 변화를 자동 감지하는 도구가 필요했음
- 최종적으로 **로컬 실행**과 **GitHub Pages 웹 대시보드** 두 가지 형태로 모두 사용 가능하게 개발함

---

## 2. 시스템 아키텍처

```
┌─────────────────────────────────────────────────────────────┐
│                     GitHub (Public Repo)                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │ GitHub Actions│  │  JSON 데이터  │  │   GitHub Pages   │  │
│  │  (매일 09:00) │  │  (site_*.json)│  │  (index.html)    │  │
│  └──────┬───────┘  └──────┬───────┘  └────────┬─────────┘  │
└─────────┼────────────────┼───────────────────┼────────────┘
          │                │                   │
          ▼                ▼                   ▼
   [자동 실행 스케줄]   [결과 저장소]      [웹 대시보드]
```

```
┌─────────────────────────────────────────────────────────────┐
│                         로컬 실행 모드                         │
│  ┌──────────────┐         ┌──────────────┐                   │
│  │  monitor_    │  HTTP   │   index.html  │                  │
│  │  server.py   │◄───────►│  (브라우저)   │                  │
│  │  (API 서버)   │         │              │                  │
│  └──────┬───────┘         └──────────────┘                  │
│         │                                                    │
│         ▼                                                    │
│  ┌──────────────┐                                            │
│  │ smart_monitor│  ──► site_state.json / site_summary.json  │
│  │    .py       │                                            │
│  └──────────────┘                                            │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. 핵심 기술 스택

| 영역 | 기술 |
|------|------|
| **Backend** | Python 3.9+ |
| **HTTP/Crawling** | `requests`, `beautifulsoup4` |
| **병렬 처리** | `concurrent.futures.ThreadPoolExecutor` (10 workers) |
| **Frontend** | 순수 HTML/CSS/JS (Vanilla) |
| **차트** | Chart.js (CDN) |
| **호스팅** | GitHub Pages |
| **CI/CD** | GitHub Actions (`cron: 0 0 * * *`) |
| **폰트** | Pretendard (CDN) |

---

## 4. 주요 기능

### 4.1 사이트맵 기반 차분 감지 (`smart_monitor.py`)
- `wp-sitemap.xml` 및 서브 사이트맵을 재귀적으로 파싱하여 전체 URL 목록 확보
- **이전 기준 데이터(`site_state_daily.json`)** 와 비교하여 변화 감지
- 감지 항목:
  - **NEW**: 사이트맵에 새로 추가된 페이지
  - **CHANGED**: 기존 페이지의 HTML 내용(SHA256 해시)이 변경됨
  - **DELETED**: 사이트맵에서 사라진 페이지
  - **STABLE**: 변화 없음

### 4.2 URL 정규화 & 노이즈 필터링
- 마케팅 파라미터(`?af=...`) 및 `#fragment` 제거하여 중복 체크 방지
- 무시 패턴 적용: `/page/`, `/tag/`, `/category/`, `/author/`, `/download_news/`, `/videos/`, 검색 결과, 오래된 뉴스(2010~2023년)
- 동적 콘텐츠 경로 우선 모니터링: `/news`, `/achievements`, `/products-service`, `/knowhow`, `/blog`

### 4.3 히스토리 및 통계
- `monitoring_history.json`에 매 실행 결과 누적 저장 (최대 2000개, 약 5.5년 분량)
- **7일/30일/90일/1년/전체** 누적 변화 요약 제공
- **Hotspot 분석**: 변동이 빈번한 URL 경로 분야 시각화 (Chart.js)
- 전체 URL 수 추이 그래프

### 4.4 다국어 지원
- 브라우저 언어 감지 (`navigator.language`)
- **한국어(ko)** / **일본어(ja)** UI 자동 전환

### 4.5 로컬 서버 모드 (`monitor_server.py`)
- `localhost:8080`에서 실행
- API 엔드포인트 제공:
  - `GET /api/data` — JSON 데이터 조회
  - `POST /api/scan` — 수동 분석 실행
  - `POST /api/cleanup` — 데이터 정제
  - `POST /api/reset` — 전체 데이터 초기화

---

## 5. 파일 구조 및 역할

| 파일 | 역할 |
|------|------|
| `smart_monitor.py` | **메인 모니터링 엔진**. 사이트맵 파싱, 병렬 크롤링, 해시 비교, 결과 JSON 생성 |
| `monitor.py` | 기본 모니터 (구버전). 단순 해시 비교 방식 |
| `crawler.py` | DFS 기반 웹 크롤러. 내부 링크 탐색 및 구조화 |
| `summarizer.py` | 페이지별 메타데이터(title, description) 수집 |
| `monitor_server.py` | 로컬 HTTP 서버 + REST API. 브라우저 자동 실행 포함 |
| `index.html` | **대시보드 프론트엔드**. 순수 JS로 JSON 데이터 시각화 |
| `cleanup.py` | 데이터 정제 (오래된/깨진 데이터 클리닝) |
| `requirements.txt` | Python 의존성 목록 (`requests`, `beautifulsoup4`) |
| `.github/workflows/monitor.yml` | GitHub Actions 워크플로우. 매일 09:00(KST) 자동 실행 |

### 생성되는 데이터 파일

| 파일 | 내용 |
|------|------|
| `site_state.json` | 모든 모니터링 대상 URL의 최신 해시 및 메타데이터 (마스터 상태) |
| `site_state_daily.json` | 당일 최초 실행 시점의 스냅샷 (일일 기준점) |
| `site_summary.json` | 최신 실행 결과의 상세 리포트 (NEW/CHANGED/DELETED 목록) |
| `site_report_meta.json` | 실행 메타정보 (URL 개수, 실행 시간 등) |
| `monitoring_history.json` | 모든 과거 실행 이력 누적 |
| `site_structure.json` | 모니터링 대상 URL 전체 목록 (외부 노출용) |

---

## 6. 작동 흐름

```
1. 사이트맵 가져오기
   └── https://www.splashtop.co.jp/wp-sitemap.xml
       └── 서브 사이트맵 재귀 파싱 → 전체 URL 목록 확보

2. 기준점 로드
   ├── site_state.json (마스터 상태)
   └── site_state_daily.json (오늘 첫 실행 기준)
       └── 날짜가 바뀌면 site_state_daily.json 자동 갱신

3. 차분 계산
   ├── NEW    : site_state_daily 에 없는 URL
   ├── DELETED: site_state_daily 에 있지만 사이트맵에 없는 URL
   └── STABLE : 공통 URL (중 priority 경로만 해시 비교)

4. 병렬 콘텐츠 Fetch (10개 동시)
   ├── STABLE 중 동적 경로 → 해시 비교 → CHANGED 감지
   └── NEW URL → 메타데이터(title, description) 수집

5. 결과 저장
   ├── site_summary.json      → 리포트
   ├── site_state.json        → 마스터 상태 갱신
   ├── monitoring_history.json→ 이력 추가
   └── site_structure.json    → URL 목록 갱신

6. 대시보드 표시
   └── index.html 이 JSON 파일을 fetch하여 시각화
```

---

## 7. 실행 방법

### 7.1 GitHub Pages (권장 — 자동화)
- 저장소가 Public이면 `https://[user].github.io/sp-monitor/` 에서 자동 접속
- GitHub Actions가 매일 아침 9시(KST)에 자동 분석 및 데이터 갱신
- 별도 조작 없이 웹 브라우저로 확인만 하면 됨

### 7.2 로컬 실행

**Windows:**
```batch
run_monitor.bat
```

**macOS:**
```bash
chmod +x start_monitor.command
./start_monitor.command
```

**직접 실행:**
```bash
pip install -r requirements.txt
python monitor_server.py
# 브라우저가 http://localhost:8080 자동 열림
```

---

## 8. GitHub Actions 자동화 설정

`.github/workflows/monitor.yml`:

```yaml
on:
  schedule:
    - cron: '0 0 * * *'  # 매일 UTC 00:00 (KST 09:00)
  workflow_dispatch:      # 수동 실행도 가능

permissions:
  contents: write         # 결과 JSON 커밋/푸시 권한
```

- 실행 후 생성된 JSON 파일들이 자동으로 `main` 브랜치에 커밋됨
- GitHub Pages는 `main` 브랜치의 `index.html`과 JSON 파일을 즉시 반영

---

## 9. 보안 고려사항

- `.gitignore`에 민감 파일(`.env`, `config/`, `*.key`, `*.pem`) 등록 완료
- 실제 API 키나 토큰은 소스코드에 하드코딩되지 않음
- GitHub Actions는 `contents: write` 권한만 사용 (최소 권한 원칙)

---

## 10. 향후 확장 아이디어

- Slack/Discord 웹훅 연동 (변화 감지 시 알림)
- Google Sheets 자동 동기화 (`.agent/skills/google-drive-sync` 스킬 활용)
- Gemini API 연동하여 변경 페이지 요약 자동 생성
- 다중 사이트 모니터링 지원 (현재는 splashtop.co.jp 전용)
