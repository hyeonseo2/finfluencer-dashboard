# 핀플루언서 비교 분석 대시보드

유튜브 금융/거시 채널의 최신 영상을 수집해 토픽 중심으로 구조화하고, **정적 데이터(JSON)** 기반으로 GitHub Pages에서 탐색하는 프로젝트입니다.

## 프로젝트 모드

- **Pages Mode (기본)**
  - GitHub Actions가 주기적으로 데이터를 수집
  - `docs/data/latest.json` 생성/갱신
  - GitHub Pages가 해당 JSON을 읽어 대시보드 렌더링

## 핵심 기능

- Seed 채널 기반 최신 영상 수집 (YouTube RSS)
- 토픽 자동 분류 (주식, 원자재, 금리, 거시/경제, ETF, FX 등)
- 영상 리스트 탐색/검색
- 토픽 스탠스 라벨(현재 기본 neutral) 표시
- GitHub Pages 정적 배포

## 디렉토리

```text
.github/workflows/
  data-collection.yml   # 스케줄 수집 + JSON 갱신 커밋
  pages.yml             # GitHub Pages 배포
scripts/
  build_pages_data.py   # Pages용 데이터 생성 스크립트
docs/
  index.html            # Pages 대시보드
  data/latest.json      # 수집 결과 데이터
```

## GitHub Actions

### 1) 데이터 배치 수집
파일: `.github/workflows/data-collection.yml`

- 매시간 실행(UTC)
- `scripts/build_pages_data.py` 실행
- 변경 시 `docs/data/latest.json` 자동 커밋

### 2) GitHub Pages 배포
파일: `.github/workflows/pages.yml`

- `docs/` 변경 시 자동 배포
- `Settings → Pages → Source: GitHub Actions` 설정 필요

## 로컬에서 데이터 생성

```bash
python scripts/build_pages_data.py
```

생성 파일:
- `docs/data/latest.json`

## GitHub Pages 주소

배포 후:
- `https://<user-or-org>.github.io/<repo>/`

## 참고

본 서비스는 공개된 콘텐츠를 바탕으로 의견을 구조화해 제공하는 정보 서비스이며,
투자 권유 또는 투자자문을 제공하지 않습니다.
