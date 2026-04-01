# 📊 Finfluencer Dashboard

YouTube 금융 및 거시경제 채널의 최신 영상을 수집하고, 이를 토픽 기준으로 구조화하여 탐색할 수 있도록 제공하는 정적 데이터 기반 대시보드입니다.

---

## Overview

본 프로젝트는 YouTube 금융 및 거시경제 콘텐츠를 기반으로,
주요 시장 토픽별로 영상을 분류하고
사용자가 관련 콘텐츠를 탐색할 수 있도록 지원하는 대시보드입니다.

### Dashboard Preview
<img width="1153" height="458" alt="image" src="https://github.com/user-attachments/assets/f112f69f-4387-444e-b0e2-2fbf6395d52c" />
<img width="1113" height="655" alt="image" src="https://github.com/user-attachments/assets/cd664e92-09f3-465b-b53d-ceefb186f4b9" />
<img width="1139" height="653" alt="image" src="https://github.com/user-attachments/assets/3b78d2c0-b64b-4eda-8507-36c9cd5a5074" />

---

## Features

* YouTube RSS 기반 최신 영상 수집
* 금융 토픽 기반 자동 분류
  * 주식
  * 금리
  * ETF
  * 원자재
  * 외환(FX)
  * 거시경제
* 영상 리스트 탐색 및 검색 기능
* 토픽별 의견(관점) 라벨 제공


---

## Architecture

```text
YouTube RSS
   ↓
GitHub Actions (Batch)
   ↓
scripts/build_pages_data.py
   ↓
docs/data/latest.json
   ↓
GitHub Pages (Static Dashboard)
```

---

## Project Structure

```text
.github/workflows/
  data-collection.yml   # 데이터 수집 및 JSON 생성
  pages.yml             # GitHub Pages 배포

scripts/
  build_pages_data.py   # 데이터 처리 스크립트

docs/
  index.html            # 대시보드 UI
  data/latest.json      # 최종 데이터
```

---

## GitHub Actions

### Data Collection

* 파일: `.github/workflows/data-collection.yml`
* 주기적으로 실행 (매시간)
* `scripts/build_pages_data.py` 실행
* 결과(`latest.json`) 자동 커밋

### Pages Deployment

* 파일: `.github/workflows/pages.yml`
* `docs/` 변경 시 자동 배포

---

## Local Development

```bash
python scripts/build_pages_data.py
```

생성 파일:

```bash
docs/data/latest.json
```

---

## 🔧 Customize: Channels

채널 목록을 변경하려면 `sample_seed_channels.json` 파일을 수정하면 됩니다.

### 수정 방법

1. `sample_seed_channels.json`에서 채널 추가 / 삭제 / 수정
2. GitHub에 push
3. GitHub Actions (`data-collection.yml`) 실행
4. `docs/data/latest.json` 자동 재생성
5. GitHub Pages에 자동 반영

### 채널 데이터 형식

```json
{
  "channel_id": "UCxxxx...",
  "channel_avatar_url": "https://yt3.googleusercontent.com/....",
  "handle": "@channelhandle",
  "display_name": "채널명",
  "category_primary": "macro",
  "country": "KR",
  "language": "ko",
  "is_interview_heavy": false,
  "active": true
}
```

* `active: false`로 설정하면 목록에는 유지되지만 수집에서는 제외됩니다.
* `display_name`은 화면에 표시되는 이름입니다.

---

## Deployment

GitHub Pages 설정:

* Settings → Pages
* Source: GitHub Actions

배포 주소:

```
https://<user-or-org>.github.io/<repo>/
```

---

## Notes

* 본 프로젝트는 공개된 YouTube 콘텐츠를 기반으로 데이터를 구성합니다.
* 제공되는 정보는 참고용이며, 투자 판단의 근거로 사용되어서는 안 됩니다.

