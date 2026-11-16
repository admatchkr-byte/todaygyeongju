# 오늘, 경주 — 공연·축제·전시 API 자동 연동

## 이 파일의 상태

- API의 3개 **조회 경로**는 공공데이터포털 공식 문서로 확인했습니다.
- **인증키를 넣은 실제 응답은 테스트하지 못했습니다.** 각 서비스가 사용하는 실제 데이터 필드명에 맞게 `scripts/update_events.py`를 조정해야 할 수도 있습니다.
- 기존 `index.html` 디자인과 `coupons.html`, `hero.mp4`, `coupon.png` 등은 변경하지 않는 구성입니다.
- `index.html`에서 이미 사용 중인 `fetch('events.json')`에 맞춰 JSON 파일을 자동 생성합니다.

## 1. 기존 사이트 파일을 보존하세요

VS Code의 기존 사이트 폴더에 다음 파일이 남아 있는지 먼저 확인해 주세요.

```
todaygyeongju/
  index.html                ← 기존 파일 그대로
  coupons.html              ← 있다면 그대로
  hero.mp4                  ← 있다면 그대로
  coupon.png                ← 있다면 그대로
```

`index.html`이 없는 빈 GitHub 저장소에 이 패키지만 올리면 사이트가 만들어지지 않습니다. 기존 사이트 파일부터 복원해야 합니다.

## 2. 이 ZIP에서 딱 2개를 해당 경로에 넣으세요

```
todaygyeongju/
  .github/
    workflows/
      deploy.yml            ← 새 파일
  scripts/
    update_events.py        ← 새 파일
```

`.github`는 점으로 시작하는 폴더입니다. 압축을 해제할 때 숨김 파일 표시가 필요할 수 있습니다.

## 3. GitHub 인증키 등록

1. GitHub 저장소 **Settings → Secrets and variables → Actions**.
2. **New repository secret** 선택.
3. Name: `DATA_GO_KR_SERVICE_KEY` (철자 그대로).
4. Secret: 공공데이터포털에서 발급받은 **일반 인증키**를 붙여넣기.
5. Save. 인증키는 `index.html`에 넣지 말고, 채팅으로도 보내지 마세요.

기존에 다른 Secret 이름이 등록돼 있다면 새 이름과 다르므로 연결되지 않습니다. 필요하면 등록된 이름만 확인하고 키 값은 공유하지 마세요.

## 4. GitHub Pages 배포 설정

1. 저장소 **Settings → Pages**.
2. **Build and deployment → Source → GitHub Actions** 선택.
3. 두 새 파일을 포함해 VS Code에서 GitHub `main` 브랜치로 업로드합니다.
4. 저장소 **Actions → 경주 행사 API 갱신 및 사이트 배포 → Run workflow** 실행.
5. 초록 체크가 표시되면 배포 주소의 `/events.json`에 데이터 배열이 표시되는지 확인하세요.

## 5. 어떤 문제인지 확인하기

- `DATA_GO_KR_SERVICE_KEY`가 없다는 오류: Secret 이름 또는 저장 위치 문제.
- `HTTP 401/403` 또는 인증 오류: 인증키/서비스 승인·인코딩 확인.
- `HTTP 404`: 조회 주소 확인.
- `원본 데이터는 있지만 제목/날짜 필드명이 맞지 않음`: API **실제 응답 예시의 필드명** 확인이 필요. Actions 로그에 출력되는 키 목록을 보내주면 수정할 수 있습니다. 인증키와 개인정보는 보내지 마세요.
- `events.json`이 `[ ]`로 보임: 조회는 성공했지만 현재부터 1년 안에 끝나지 않은 날짜를 가진 행사가 없을 수도 있습니다. 데이터 자체가 과거 내역뿐인지 확인하세요.
- 홈페이지가 그대로임: Actions 배포 성공 여부 및 Pages Source가 GitHub Actions인지 확인하세요.
- `events.json` 404: 업로드/배포가 완료되지 않았거나 경로·배포 설정 문제.

## 6. 기존 `index.html`에서 유의할 점

- 코드는 이벤트를 시작일 오름차순으로 정리하고 **현재 진행 중이거나 향후 1년 안에 시작하는 행사**를 포함합니다. 따라서 제목을 `경주에서 열리는 공연·축제·전시`처럼 바꾸면 더 정확합니다. 기존 코드의 `events.slice(0, 3)`은 첫 세 건만 표시합니다.
- 붙여넣은 코드에 실제로 `[https://...](https://...)`, `&#x20;`, `\\<html>` 같은 문자열이 있다면 복사 과정에서 코드가 변형된 것입니다. VS Code의 실제 HTML은 일반 URL, 태그, JS 문법이어야 합니다.
- ‘현재 거리 혼잡도 약간 여유’는 기존 HTML에 고정된 문자열입니다. 현재 실제 혼잡도를 제공하는 연동은 아닙니다.
- GitHub Actions의 예약 실행은 지연될 수 있으므로 정각 업데이트를 보장하지 않습니다.

## 공식 확인 출처

- 공연 https://www.data.go.kr/data/15109402/openapi.do
- 축제 https://www.data.go.kr/data/15109399/openapi.do
- 전시 https://www.data.go.kr/data/15109412/openapi.do
- GitHub Pages Actions https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site
