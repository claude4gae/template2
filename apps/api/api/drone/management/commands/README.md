# Drone Management Commands

이 폴더의 command는 Django `manage.py`로 실행합니다.

```bash
docker compose -f docker-compose.dev.yml exec -T api python manage.py <command> [options]
```

## `seed_drone_affiliation_notifications`

`account_affiliation`과 `account_external_affiliation_snapshot` 기준으로 Drone SOP 알림 기본 설정을 생성합니다.

### 동작

- `account_affiliation.line/user_sdwt_prod`별 `DroneSopTarget`을 생성합니다.
- `sdwt_prod == user_sdwt_prod == account_affiliation.user_sdwt_prod`인 `DroneSopTargetMapping`을 생성합니다.
- 새 target의 채널 기본값을 생성합니다.
  - Jira: 비활성
  - Messenger/Teams: 활성
  - Mail: 활성
  - `template_key`: 기본 `common`
- 자동예약 규칙을 생성합니다.
  - `comment_keyword`: 기본 `$SETUP_EQP`
  - `enabled`: `false`
- 같은 `user_sdwt_prod`의 가입 사용자를 Mail/Messenger 수신인으로 추가합니다.
- 같은 `predicted_user_sdwt_prod`의 외부 snapshot 사용자를 `external_knox_id` 수신인으로 추가합니다.
- 기존 target, mapping, channel config, rule, recipient는 덮어쓰지 않고 없는 row만 추가합니다.

### 사용법

```bash
docker compose -f docker-compose.dev.yml exec -T api python manage.py seed_drone_affiliation_notifications --dry-run
docker compose -f docker-compose.dev.yml exec -T api python manage.py seed_drone_affiliation_notifications
docker compose -f docker-compose.dev.yml exec -T api python manage.py seed_drone_affiliation_notifications --line-id L1
```

### 옵션

| 옵션 | 기본값 | 설명 |
| --- | --- | --- |
| `--line-id` | 전체 | 특정 `account_affiliation.line`만 처리합니다. |
| `--template-key` | `common` | 새 채널 설정의 template key입니다. |
| `--comment-keyword` | `$SETUP_EQP` | 새 자동예약 규칙의 comment keyword입니다. |
| `--dry-run` | off | 생성 결과를 계산한 뒤 DB 변경을 롤백합니다. |

## `seed_drone_dummy_data`

개발 환경에서 Drone 모듈 end-to-end 검증용 더미 데이터를 생성합니다.

### 동작

- 더미 `account_affiliation` row를 생성합니다.
- 더미 target, mapping, channel config, needtosend rule을 생성합니다.
- 더미 early inform 설정을 생성합니다.
- 여러 상태의 `DroneSOP` 샘플 row를 생성합니다.
- `prefix` 기반 데이터만 다뤄 운영 데이터와 충돌을 줄입니다.
- `ENVIRONMENT=development` 및 `DRONE_SEED_ALLOWED=1`일 때만 실행됩니다.

### 사용법

```bash
docker compose -f docker-compose.dev.yml exec -T api python manage.py seed_drone_dummy_data
docker compose -f docker-compose.dev.yml exec -T api python manage.py seed_drone_dummy_data --prefix DEMO
docker compose -f docker-compose.dev.yml exec -T api python manage.py seed_drone_dummy_data --prefix DEMO --reset
```

### 옵션

| 옵션 | 기본값 | 설명 |
| --- | --- | --- |
| `--prefix` | `DUMMY` | 생성 데이터 식별 prefix입니다. |
| `--reset` | off | 동일 prefix 더미 데이터를 먼저 삭제한 뒤 다시 생성합니다. |

## `prune_drone_sop`

보관 기간을 초과한 `drone_sop` row를 `created_at` 기준으로 삭제합니다.

### 동작

- `created_at < now - days`인 `DroneSOP` row를 대상으로 합니다.
- 상태와 무관하게 삭제합니다.
- `DroneSOP` FK cascade로 연결된 dispatch/delivery 이력도 함께 삭제됩니다.
- `dry-run`이면 삭제하지 않고 대상 수만 출력합니다.

### 사용법

```bash
docker compose -f docker-compose.dev.yml exec -T api python manage.py prune_drone_sop --dry-run
docker compose -f docker-compose.dev.yml exec -T api python manage.py prune_drone_sop --days 180 --batch-size 1000
docker compose -f docker-compose.dev.yml exec -T api python manage.py prune_drone_sop --days 90 --max-batches 5
```

### 옵션

| 옵션 | 기본값 | 설명 |
| --- | --- | --- |
| `--days` | `DRONE_SOP_RETENTION_DAYS` 또는 `180` | 보관 일수입니다. |
| `--batch-size` | `DRONE_SOP_PRUNE_BATCH_SIZE` 또는 `1000` | 한 번에 삭제할 row 수입니다. |
| `--max-batches` | 제한 없음 | 최대 삭제 배치 수입니다. |
| `--dry-run` | off | 삭제하지 않고 대상 수만 출력합니다. |

## `purge_drone_sop`

모든 `drone_sop` row를 삭제합니다.

### 동작

- 전체 `DroneSOP` row를 대상으로 합니다.
- FK cascade로 dispatch/delivery 이력도 함께 삭제됩니다.
- target, channel config, mapping, recipient 같은 설정 테이블은 유지합니다.
- `--confirm-delete-all` 없이는 삭제하지 않고 대상 수만 출력합니다.

### 사용법

```bash
docker compose -f docker-compose.dev.yml exec -T api python manage.py purge_drone_sop
docker compose -f docker-compose.dev.yml exec -T api python manage.py purge_drone_sop --confirm-delete-all
```

### 옵션

| 옵션 | 기본값 | 설명 |
| --- | --- | --- |
| `--confirm-delete-all` | off | 실제 전체 삭제를 수행합니다. |
