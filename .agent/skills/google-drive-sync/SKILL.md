# Google Drive & Sheets Integration Skill

이 스킬은 서비스 계정을 활용하여 Google Drive 폴더에 파일을 업로드하거나, Google Sheets 데이터를 관리하는 표준 방식입니다.

## 🛠️ 사전 설정 (Setup Context)
1. **중앙 폴더 운영**: `antigravity`라는 이름의 공유 드라이브 또는 폴더를 생성합니다.
2. **서비스 계정 초대**: 스크린샷에 나온 서비스 계정(`sync-bot@...`)을 해당 폴더의 **'콘텐츠 관리자(Content Manager)'**로 초대합니다.
3. **인증**: `master.env`에 저장된 서비스 계정 JSON 키값을 사용하여 권한을 획득합니다.

## 📄 표준 구현 템플릿 (Python)

```python
import gspread
from google.oauth2.service_account import Credentials

class GoogleDriveSync:
    def __init__(self, credentials_path="config/google_service_account.json"):
        # 권한 범위 설정 (Drive 및 Sheets)
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        self.creds = Credentials.from_service_account_file(credentials_path, scopes=scopes)
        self.client = gspread.authorize(self.creds)

    def write_to_sheet(self, sheet_id, data):
        """구글 시트에 데이터를 기록합니다."""
        sh = self.client.open_by_key(sheet_id)
        worksheet = sh.get_worksheet(0)
        worksheet.append_row(data)

    def upload_file(self, folder_id, file_path):
        """특정 폴더 ID로 파일을 업로드합니다. (Google Drive API 필요)"""
        # ... (Drive API 업로드 로직)
```

## 🚀 활용 노하우
- **파일 이름**: `[ProjectName]_Result_YYYYMMDD` 형식을 권장합니다.
- **폴더 ID 관리**: 프로젝트마다 `GOOGLE_FOLDER_ID`를 `.env`에 정의하여 사용합니다.
- **안티그래비티 지시어**: "이 분석 결과를 `google-drive-sync` 스킬을 써서 내 구글 드라이브 `antigravity` 폴더에 시트로 남겨줘."
