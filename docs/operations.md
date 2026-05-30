# 운영/개발 명령

이 문서는 로컬 실행, 테스트, 마이그레이션 확인, management command를 정리합니다.

## 로컬 실행

```bash
docker compose -f docker-compose.dev.yml up -d
```

Airflow, DB, FTP, MinIO, dummy ADFS는 유지하고 백엔드만 자주 재시작하려면 split compose를 사용합니다.

```bash
docker network create shared-net 2>/dev/null || true
docker compose -f docker-compose.dev.infra.yml up -d
docker compose -f docker-compose.dev.backend.yml up -d
docker compose -f docker-compose.dev.backend.yml restart api
```

백엔드만 끄고 다시 켤 때는 API compose만 조작합니다.

```bash
docker compose -f docker-compose.dev.backend.yml stop api
docker compose -f docker-compose.dev.backend.yml up -d api
```

백엔드 이미지 재빌드가 필요할 때는 API compose만 다시 올립니다.

```bash
docker compose -f docker-compose.dev.backend.yml up -d --build api
```

주요 주소:

| 서비스 | 주소 |
| --- | --- |
| Web | `http://localhost:3000` |
| API | `http://localhost:8000` |
| Nginx | `http://localhost` |
| Dummy ADFS/RAG/LLM/Mail/Jira | `http://localhost:9102` |
| MinIO | `http://localhost:9000`, `http://localhost:9001` |

## 프론트 명령

```bash
npm run web:dev
npm run web:build
npm run web:lint
npm run agent:audit
npm run agent:audit:docs
npm run agent:audit:web-boundary
npm run agent:audit:ui
```

## 백엔드 검증

백엔드는 Docker Compose `api` 컨테이너 기준입니다.

```bash
docker compose -f docker-compose.dev.yml exec -T api python manage.py check
docker compose -f docker-compose.dev.yml exec -T api python manage.py test
docker compose -f docker-compose.dev.yml exec -T api python manage.py makemigrations --check --dry-run
```

## Management command

| Command | 설명 |
| --- | --- |
| `seed_dummy_emails` | 개발용 샘플 메일 생성 |
| `process_email_outbox` | EmailOutbox RAG 작업 처리 |
| `load_m_tkin_prevent` | `m_tkin_prevent` incoming 파일 적재 |
| `load_ctttm_workorder_list` | `ctttm_workorder_list` incoming 파일 적재 |
| `load_ct_process_comment` | `ct_process_comment` incoming 파일 적재 |
| `seed_drone_dummy_data` | Drone 개발용 샘플 데이터 생성 |
| `seed_drone_targets_from_file` | JSON/CSV 기준 Drone SOP/발송 이력/알림 설정 초기화 후 target/channel/recipient seed |
| `prune_drone_sop` | 보관 기간 초과 Drone SOP 데이터 정리 |
| `purge_drone_sop` | Drone SOP 데이터 전체 삭제 또는 dry-run 확인 |

실행 예시:

```bash
docker compose -f docker-compose.dev.yml exec -T api python manage.py seed_dummy_emails
docker compose -f docker-compose.dev.yml exec -T api python manage.py process_email_outbox
docker compose -f docker-compose.dev.yml exec -T api python manage.py load_m_tkin_prevent
docker compose -f docker-compose.dev.yml exec -T api python manage.py load_ctttm_workorder_list
docker compose -f docker-compose.dev.yml exec -T api python manage.py load_ct_process_comment
docker compose -f docker-compose.dev.yml exec -T api python manage.py seed_drone_dummy_data
docker compose -f docker-compose.dev.yml exec -T api python manage.py seed_drone_targets_from_file --file /app/config/drone_targets.json --dry-run
docker compose -f docker-compose.dev.yml exec -T api python manage.py prune_drone_sop
docker compose -f docker-compose.dev.yml exec -T api python manage.py purge_drone_sop --dry-run
```

## Data Movement Airflow DAG

`airflow/dags/data_movement_file_load.py`는 기본 1분 주기로 아래 endpoint를 호출합니다.

```text
POST /api/v1/data-movement/m_tkin_prevent/load/
POST /api/v1/data-movement/ctttm_workorder_list/load/
POST /api/v1/data-movement/ct_process_comment/load/
```

`ct_process_comment`는 workorder 목록을 참조하므로 DAG에서 `ctttm_workorder_list` 이후 실행됩니다.
스케줄과 실행 옵션은 Airflow 환경 변수로 조정합니다.

```text
DATA_MOVEMENT_LOAD_SCHEDULE=*/1 * * * *
DATA_MOVEMENT_LOAD_HTTP_TIMEOUT=1800
DATA_MOVEMENT_LOAD_LIMIT=
DATA_MOVEMENT_LOAD_DRY_RUN=false
```

### Data Movement FTP

Compose의 `ftp` service는 API와 같은 host path를 공유합니다.
기본 host path는 `./data/data_movement`이며 API 컨테이너에서는 `/data/data_movement`로 보입니다.

```bash
docker compose -f docker-compose.dev.yml up -d ftp
```

FTP 접속 기본값:

```text
host=<compose host>
port=6380
user=ftpuser
password=ftp1234
passive ports=8076-8079
```

운영/공유 환경에서는 아래 값을 env로 반드시 바꿉니다.

```text
FTP_USER
FTP_PASS
FTP_PASV_ADDRESS
FTP_PASV_MIN_PORT
FTP_PASV_MAX_PORT
DATA_MOVEMENT_HOST_PATH
```

### Drone JSON/CSV target seed

`seed_drone_targets_from_file`은 JSON/CSV의 `department`, `line`, `user_sdwt_prod` 목록을 기준으로
Drone SOP/발송 이력/알림 설정을 초기화한 뒤 다시 생성합니다.

입력 샘플은 `docs/examples/drone_targets.sample.json`,
`docs/examples/drone_targets.sample.csv`,
`docs/examples/drone_targets.multi_mapping.sample.csv`에 있습니다.

```json
{
  "targets": [
    {
      "department": "ENGR",
      "line": "L1",
      "target_user_sdwt_prod": "ETCH_A",
      "recipient_user_sdwt_prod": "ETCH_A",
      "channels": {
        "jira": {
          "enabled": false,
          "template_key": "common",
          "jira_project_key": "DRONE"
        },
        "messenger": {
          "enabled": true,
          "template_key": "common",
          "chatroom_id": null,
          "force_new_chatroom": true
        },
        "mail": {
          "enabled": true,
          "template_key": "common"
        }
      },
      "mappings": [
        {
          "sdwt_prod": "ETCH_A",
          "user_sdwt_prod": "ETCH_A"
        }
      ],
      "needtosend_rule": {
        "enabled": false,
        "comment_keyword": "$SETUP_EQP",
        "ignore_sample_type": false
      }
    }
  ]
}
```

주요 필드:

- `target_user_sdwt_prod`: `drone_sop_target.target_user_sdwt_prod`
- `recipient_user_sdwt_prod`: 수신인 자동 수집에 사용할 account 소속값
- `channels`: `drone_sop_target_channel_config` 생성값
- `mappings`: `drone_sop_target_mapping` 생성값
- `needtosend_rule`: `drone_sop_needtosend_rule` 생성값

사용 순서:

```bash
docker compose -f docker-compose.dev.yml exec -T api \
  python manage.py seed_drone_targets_from_file \
  --file /app/config/drone_targets.json \
  --dry-run

docker compose -f docker-compose.dev.yml exec -T api \
  python manage.py seed_drone_targets_from_file \
  --file /app/config/drone_targets.csv \
  --dry-run

docker compose -f docker-compose.dev.yml exec -T api \
  python manage.py seed_drone_targets_from_file \
  --file /app/config/drone_targets.json
```

초기화 범위:

- `drone_sop`
- `drone_sop_target_dispatch`
- `drone_sop_delivery`
- `drone_sop_target`
- `drone_sop_target_mapping`
- `drone_sop_target_channel_config`
- `drone_sop_needtosend_rule`
- `drone_sop_target_recipient`

CSV에서 하나의 target에 mapping이 여러 개인 경우 target row는 하나만 작성하고 `mappings`
컬럼에 JSON 배열을 넣습니다. 같은 `target_user_sdwt_prod`가 여러 행에 반복되면 command가
오류로 중단됩니다.

JSON/CSV 파일은 `api` 컨테이너가 읽을 수 있는 경로에 배치해야 합니다.
실제 실행 전에는 반드시 `--dry-run` 출력의 삭제/생성 카운트를 확인합니다.

## 환경 변수 파일

| 파일 | 역할 |
| --- | --- |
| `env/api.common.env` | API 공통 설정 |
| `env/api.dev.env` | API 개발 오버라이드 |
| `env/web.dev.env` | Web 개발 설정 |
| `env/minio.env` | MinIO 설정 |

## 주의할 점

- backend 테스트와 Django 명령은 `api` 컨테이너에서 실행합니다.
- 외부 연동 URL은 하드코딩하지 않고 env로 관리합니다.
- auth/RAG/assistant/mail 계약을 바꾸면 `apps/adfs_dummy`도 함께 갱신합니다.

## 문서 검증

문서가 실제 route/model/env inventory와 크게 어긋나지 않는지 확인합니다.

```bash
npm run agent:audit:docs
```

검증 대상:

- backend API prefix와 주요 endpoint
- frontend route와 feature facade
- 주요 Django model class
- management command
- env group

## 장애 확인 순서

| 증상 | 먼저 확인할 것 |
| --- | --- |
| 화면이 API를 못 부름 | `VITE_BACKEND_URL`, Nginx proxy, Django allowed hosts/CORS/CSRF |
| 로그인 redirect 실패 | `OIDC_REDIRECT_URI`, `ALLOWED_REDIRECT_HOSTS`, session cookie secure/samesite |
| Emails 수집 실패 | POP3 env, Airflow token, `seed_dummy_emails`/dummy mail 동작 |
| RAG/Assistant 실패 | `ASSISTANT_*`, `RAG_*`, dummy RAG endpoint, permission group |
| Drone 알림 실패 | SOP 수집 결과, target/channel/recipient 설정, Jira/Mail/Messenger env |
| Timeline 조회 실패 | `TIMELINE_DB_*`, `TIMELINE_QUERY_DAYS`, 기준 정보 endpoint |
| 파일/이미지 실패 | MinIO env, bucket 접근, asset sequence |
