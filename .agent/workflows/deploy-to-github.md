---
description: 로컬 프로젝트를 GitHub 저장소로 배포하고 GitHub Actions 자동화 설정하기
---

이 워크플로우는 로컬에서 개발한 프로젝트를 GitHub에 올리고, 매일 정해진 시간에 자동으로 실행되도록 설정하는 표준 절차입니다.

### 1단계: 프로젝트 구조 확인
- `requirements.txt`가 있는지 확인합니다.
- 메인 실행 스크립트(예: `smart_monitor.py`)가 있는지 확인합니다.
- 웹 UI용 `index.html`이 있는지 확인합니다.

### 2단계: GitHub Actions 워크플로우 파일 생성
`.github/workflows/monitor.yml` 파일을 생성합니다. (Python 실행 및 결과 Commmit/Push 로직 포함)
// turbo
```yaml
name: Automated Monitor Task
on:
  schedule:
    - cron: '0 0 * * *' # 매일 아침 9시(KST)
  workflow_dispatch:
permissions:
  contents: write
jobs:
  run-task:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: {python-version: '3.9'}
      - run: pip install -r requirements.txt
      - run: python your_script.py # 여기서 파일명 수정
      - run: |
          git config --local user.email "action@github.com"
          git config --local user.name "GitHub Action"
          git add .
          git commit -m "Auto-update data" || echo "No changes"
          git push
```

### 3단계: GitHub 저장소 연결 및 업로드
// turbo
```bash
git init
git add .
git commit -m "Initial Deployment"
git branch -M main
git remote add origin https://github.com/[유저네임]/[저장소명].git
git push -u origin main --force
```

### 4단계: 수동 설정 안내 (사용자 확인 필요)
1. **Settings > Actions > General**: `Workflow permissions`를 `Read and write permissions`로 변경.
2. **Settings > Pages**: `main` 브랜치를 배포 소스로 설정.
