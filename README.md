# weeklyblockchain-bot
# 위클리블록체인 → 텔레그램 자동 송출 봇

위클리블록체인 기사를 24시간 자동으로 텔레그램 채널(@weeklyblockchain)에 올리는 봇입니다.
GitHub Actions로 돌아가서 **무료**이고, PC를 켜둘 필요가 없습니다.

## 이 봇이 해주는 것
- ✅ 여러 카테고리 새 기사 자동 송출
- ✅ **Coinness(속보) 작성자 글 자동 제외**
- ✅ 같은 기사가 여러 카테고리에 있어도 **한 번만** (중복 제거)
- ✅ **제목/미리보기 이미지 클릭 → 기사로 바로 이동**
- ✅ 본문·"작성자:"·"키워드:" 줄 없이 깔끔

---

## 설정 순서 (한 번만 하면 됩니다)

### 1. 내 텔레그램 봇 만들기 (토큰 받기)
1. 텔레그램에서 **@BotFather** 검색 → 대화 시작
2. `/newbot` 입력 → 봇 이름과 사용자명(영문, `_bot`로 끝남) 입력
3. BotFather가 주는 **토큰**(예: `8123456789:AAH...`)을 복사해 둡니다. ← 비밀번호처럼 취급, 남에게 공유 금지

### 2. 그 봇을 채널 관리자로 추가
1. **@weeklyblockchain** 채널 → 관리자 → 관리자 추가
2. 방금 만든 **내 봇**을 추가하고 **"메시지 게시"** 권한 켜기

### 3. (중복 방지) 기존 RSStT 봇 정리
- 같은 채널에 RSStT(@RSStT_Bot)가 계속 올리면 중복됩니다.
- @RSStT_Bot 개인 대화에서 `/unsub_all @weeklyblockchain` 로 채널 구독 해제하거나,
  채널 관리자에서 @RSStT_Bot 을 제거하세요.

### 4. GitHub에 코드 올리기
1. https://github.com 가입/로그인
2. 우측 상단 **+** → **New repository**
3. 이름 입력(예: `wb-telegram-bot`) → **Public** 선택(공개여야 Actions가 무료 무제한)
   → **Create repository**
4. 만든 저장소 페이지에서 **Add file → Upload files**
5. 이 폴더의 파일들을 **드래그해서 업로드**:
   - `main.py`
   - `requirements.txt`
   - `seen.json`
   - `.github/workflows/post.yml` (폴더 구조 그대로 — 드래그 시 경로 유지됨)
   - `README.md` (선택)
6. **Commit changes** 클릭

> `.github` 폴더가 업로드 안 되면, 웹에서 **Add file → Create new file** 누르고
> 파일명에 `.github/workflows/post.yml` 을 그대로 입력한 뒤 내용 붙여넣기 하세요.

### 5. 비밀값(Secrets) 등록
1. 저장소 → **Settings** → **Secrets and variables** → **Actions**
2. **New repository secret** 으로 2개 추가:
   - 이름 `TELEGRAM_BOT_TOKEN` / 값: 1단계의 봇 토큰
   - 이름 `TELEGRAM_CHAT_ID` / 값: `@weeklyblockchain`

### 6. 작동 시작
1. 저장소 → **Actions** 탭 → (Actions 사용 확인 버튼 나오면 동의)
2. 왼쪽 **Post WeeklyBlockchain to Telegram** → **Run workflow** 로 수동 1회 실행
3. **첫 실행**: 기존 기사는 도배 방지로 안 보내고, **최신 1건만 테스트로** 채널에 올립니다.
   → 채널에 1건 뜨고 제목이 클릭되면 성공!
4. 이후 **10분마다 자동**으로 새 기사를 올립니다.

---

## 자주 바꾸는 설정 (`main.py` 위쪽)
- **카테고리 추가/제거**: `CATEGORY_CODES` 목록 수정
- **제외 작성자 추가**: `EXCLUDED_AUTHORS = {"coinness"}` 에 추가 (예: `{"coinness", "someone"}`)
- **속도/도배 한도**: `MAX_POST_PER_RUN`

## 문제 해결
- 안 올라오면: Actions 탭 → 최근 실행 로그 확인. `[fail]` 메시지에 원인이 나옵니다.
- "chat not found": `TELEGRAM_CHAT_ID` 값이 `@weeklyblockchain` 인지, 봇이 채널 관리자(게시권한)인지 확인.
- 사진이 안 뜨면: 텔레그램이 기사 페이지의 미리보기를 못 가져온 경우. 제목 링크는 그대로 작동합니다.
