# 트렌드 대시보드 — 매일 08:00 KST 자동 갱신

컴퓨터가 꺼져 있어도 GitHub Actions가 매일 아침 8시에 데이터를 수집해서 사이트를 갱신합니다.

## 구성
- index.html : 대시보드 (data.json 우선, 없으면 자체 수집)
- scripts/update_data.py : 데이터 수집 스크립트 (의존성 없음)
- .github/workflows/update.yml : 매일 08:00 KST 자동 실행 스케줄
- data.json : 매일 자동 생성되는 데이터

## 접속
https://nadoo88.github.io/trend-dashboard/

## 수집 시간 변경
update.yml의 cron 수정 (UTC 기준, KST-9시간). 예: 07:00 KST = 0 22 * * *
