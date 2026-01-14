# 계정 소속 로직

> 이 문서는 현재 코드베이스 기준으로 user_sdwt_prod 소속/권한/승인/재확인/메일함 접근/프론트 UI 흐름을 전체적으로 설명합니다.

## 0. 범위
- account 도메인뿐 아니라 auth(OIDC), emails, assistant, 프론트 UI까지 포함합니다.

## 1. 빠른 지도

### 1.1 핵심 모듈
- `apps/api/api/account/models.py` (User/UserProfile/소속/권한/변경/스냅샷 모델)
- `apps/api/api/account/selectors.py` (읽기 전용 조회 로직)
- `apps/api/api/account/serializers.py` (외부 동기화/재확인/승인 요청 스키마)
- `apps/api/api/account/services/access.py` (접근 권한 보장/부여/회수)
- `apps/api/api/account/services/affiliations.py` (소속 개요/재확인/옵션)
- `apps/api/api/account/services/affiliation_requests.py` (소속 변경 요청/승인/거절)
- `apps/api/api/account/services/external_sync.py` (외부 예측 동기화)
- `apps/api/api/account/services/overview.py` (계정 개요)
- `apps/api/api/account/services/users.py` (프로필 보장/사용자 조회)
- `apps/api/api/account/views.py` (API 엔드포인트)
- `apps/api/api/auth/services/oidc.py` (OIDC 클레임 매핑, 첫 로그인 자동 승인, `/api/v1/auth/me`)
- `apps/api/api/emails/selectors.py`, `apps/api/api/emails/services/mailbox.py` (메일함 멤버/요약)
- `apps/api/api/assistant/selectors.py` (assistant 접근 그룹 계산)
- `apps/web/src/features/auth/components/UserSdwtProdOnboardingDialog.jsx` (온보딩)
- `apps/web/src/features/auth/components/UserSdwtProdReconfirmDialog.jsx` (재확인)
- `apps/web/src/features/account/*` (계정/멤버/권한 화면)
- `apps/web/src/lib/profileImage.js` (avatarid 기반 아바타 URL)

### 1.2 주요 API 엔드포인트
| Method | Path | 설명 |
| --- | --- | --- |
| GET | `/api/v1/account/affiliation` | 소속 개요 + 소속 옵션 |
| POST | `/api/v1/account/affiliation` | 소속 변경 요청 |
| GET | `/api/v1/account/affiliation/requests` | 소속 변경 요청 목록 |
| POST | `/api/v1/account/affiliation/approve` | 승인/거절 |
| GET | `/api/v1/account/affiliation/reconfirm` | 재확인 상태 조회 |
| POST | `/api/v1/account/affiliation/reconfirm` | 재확인 응답 |
| POST | `/api/v1/account/access/grants` | 접근 권한 부여/회수 |
| GET | `/api/v1/account/access/manageable` | 관리 가능 그룹/멤버 |
| GET | `/api/v1/account/overview` | 계정 개요(통합) |
| GET | `/api/v1/account/line-sdwt-options` | line/user_sdwt_prod 옵션 |
| POST | `/api/v1/account/external-affiliations/sync` | 외부 예측 소속 동기화(Airflow 토큰) |
| GET | `/api/v1/auth/me` | 로그인 사용자 정보(소속 상태 포함) |

## 2. 용어
- **user_sdwt_prod** = 소속 그룹 식별자(권한/메일함/RAG 기준 값)
- **knox_id** = 사용자 로그인 식별자(OIDC `loginid`)
- **avatarid** = 사용자 아바타 식별자(OIDC `userid`)
- **Affiliation Option** = `(department, line, user_sdwt_prod)` 조합(사용자 선택용)
- **UserProfile.role** = 계정 프로필 역할(`admin | manager | viewer`, 접근 권한 role과 별도)

## 3. 데이터 모델

### 3.1 User (account User)
- `sabun` = 사용자 고유키(로그인 식별자)
- `knox_id`, `avatarid` = OIDC 클레임 저장
- `department`, `line`, `user_sdwt_prod` = 현재 조직/소속
- `requires_affiliation_reconfirm` = 외부 예측 변경 시 재확인 필요 플래그
- `affiliation_confirmed_at` = 소속 확정 시각

### 3.2 UserProfile
- `role` = `admin | manager | viewer` (계정 UI에서 사용하는 프로필 역할)
- UserProfile은 사용자당 1개를 유지하며 없으면 생성합니다.

### 3.3 Affiliation (옵션 테이블)
- `(department, line, user_sdwt_prod)` 조합을 제공
- `user_sdwt_prod`는 유니크 제약

### 3.4 UserSdwtProdAccess (접근 권한)
- `user` + `user_sdwt_prod` 조합에 대한 역할 저장
- `role` = `viewer | member | manager`
- `granted_by`, `created_at` 포함

### 3.5 UserSdwtProdChange (소속 변경 이력)
- `from_user_sdwt_prod` → `to_user_sdwt_prod` 변경 기록
- `status` = `PENDING | APPROVED | REJECTED | SUPERSEDED`
- `effective_from` = 적용 기준 시각
- `approved`, `applied`, `approved_by`, `approved_at`, `created_by`로 승인/적용 상태를 보조

### 3.6 ExternalAffiliationSnapshot (외부 예측)
- `knox_id` 기준으로 `predicted_user_sdwt_prod` 저장
- 예측값이 바뀌면 (현재 소속 있음 + pending 없음) 재확인 플래그를 세웁니다.

## 4. 역할 모델

### 4.1 접근 권한 role
| Role | 권한 요약 |
| --- | --- |
| viewer | 조회만 가능 |
| member | 승인 가능 |
| manager | 승인 + 권한 관리 |

- 역할 우선순위는 `viewer < member < manager` 입니다.
- `ensure_self_access`는 현재 소속에 대한 `viewer` 요청을 `member`로 승급합니다.
- superuser/staff는 승인/관리에서 항상 관리자급으로 취급됩니다.

### 4.2 UserProfile.role
- 접근 권한(role)과 별도이며, 계정 화면의 기본 역할 표시용으로 사용합니다.

## 5. 상태 모델
| Status | 의미 |
| --- | --- |
| PENDING | 승인 대기 |
| APPROVED | 승인/적용 완료 |
| REJECTED | 거절 |
| SUPERSEDED | 대체됨(이전 요청 폐기) |

- `REJECTED` 필터는 `SUPERSEDED`도 포함하도록 동작합니다.
- `APPROVED` 필터는 `approved/applied` 플래그도 포함합니다.

## 6. 조회 로직 (Selectors)

### 6.1 접근 가능한 그룹 집합
**Function**: `get_accessible_user_sdwt_prods_for_user`
- 인증 사용자라면 본인 소속 + 접근 권한 행을 합쳐 반환합니다.
- 소속이 없으면 “대기 중 변경(to_user_sdwt_prod)”도 포함합니다.
- superuser는 옵션/권한/사용자에 존재하는 user_sdwt_prod 값을 합쳐 반환합니다.

### 6.2 관리 가능한 그룹
**Function**: `list_manageable_user_sdwt_prod_values`
- role이 `manager`인 그룹만 반환합니다.

### 6.3 승인 가능한 그룹
**Function**: `list_approvable_user_sdwt_prod_values`
- role이 `member` 또는 `manager`인 그룹 반환

### 6.4 승인자 존재 여부
**Function**: `has_approver_for_user_sdwt_prod`
- 특정 그룹에 `member/manager` 접근 권한이 존재하는지 확인

### 6.5 변경 요청 목록 필터
**Function**: `list_affiliation_change_requests`
- `allowed_user_sdwt_prods`, `status`, `search`, `user_sdwt_prod`로 필터
- 검색은 username/email/sabun/knox_id/givenname/surname에 대해 수행

## 7. 쓰기 로직 (Services)

### 7.1 ensure_self_access
**목적**: 현재 소속에 대한 접근 권한 행 보장
- 현재 소속이 없으면 아무 것도 하지 않습니다.
- 존재하지 않으면 생성, 존재하면 상향(upgrade)만 수행합니다.

### 7.2 grant_or_revoke_access
**목적**: 권한 부여/회수
- 관리 권한 검증 후 grant/revoke 수행
- revoke 시 현재 소속(user_sdwt_prod) 권한은 제거할 수 없습니다.
- revoke로 마지막 manager가 사라지면 거부합니다.

### 7.3 request_affiliation_change
**목적**: 소속 변경 요청 생성
- 기존 PENDING이 있으면 새 요청을 만들고 이전 요청은 SUPERSEDED 처리
- 자동 적용 조건 = (예측값 일치) 또는 (승인자 없음)
- `force_pending=true`이거나 기존 PENDING이 있으면 자동 적용을 하지 않습니다.
- 자동 적용이면 `effective_from`을 현재 시각으로 덮어씁니다.

### 7.4 approve_affiliation_change / reject_affiliation_change
- 승인자는 member/manager 또는 privileged 사용자
- 승인 시 사용자 소속을 갱신하고 change를 APPROVED로 바꿉니다.
- 승인 시 이전 소속의 member 권한은 viewer로 강등될 수 있습니다.
- 거절 시 REJECTED로 변경하고 거절 사유를 저장합니다.

### 7.5 submit_affiliation_reconfirm_response
- 재확인 플래그가 없으면 409 반환
- accepted=false면 기존 유지(플래그 해제)
- accepted=true면 선택한 user_sdwt_prod로 변경 요청 생성
- 선택값이 예측값과 다르면 승인 대기(force pending)로 처리합니다.
- 선택값이 비어 있으면 예측값을 사용합니다.

### 7.6 auto_approve_affiliation_from_snapshot
- 신규 사용자 최초 로그인 시 예측 소속으로 자동 적용 시도

### 7.7 sync_external_affiliations
- 외부 예측 변경 감지 시 사용자에 재확인 플래그 설정
- 현재 소속이 없거나 pending이 있으면 플래그를 세우지 않습니다.

## 8. API 상세 흐름

### 8.1 GET `/api/v1/account/affiliation`
- 현재 소속 정보 + 접근 목록 + 소속 옵션 반환

**예시 응답**
```json
{
  "currentUserSdwtProd": "G-A",
  "currentDepartment": "Dept",
  "currentLine": "Line",
  "timezone": "Asia/Seoul",
  "accessibleUserSdwtProds": [
    {
      "userSdwtProd": "G-A",
      "role": "manager",
      "source": "self",
      "grantedBy": null,
      "grantedAt": null
    }
  ],
  "manageableUserSdwtProds": ["G-A"],
  "affiliationOptions": [
    {"department": "Dept", "line": "Line", "user_sdwt_prod": "G-A"}
  ]
}
```

### 8.2 POST `/api/v1/account/affiliation`
- 소속 변경 요청(자동 적용 또는 PENDING)
- 입력 키는 `user_sdwt_prod` 또는 `userSdwtProd` 지원
- `effective_from`이 타임존 없이 들어오면 KST로 해석 후 UTC로 변환됩니다.

**예시 요청**
```json
{
  "user_sdwt_prod": "G-B",
  "effective_from": "2025-12-28T10:00:00+09:00"
}
```

**예시 응답 (대기)**
```json
{
  "status": "pending",
  "changeId": 101,
  "userSdwtProd": "G-B",
  "effectiveFrom": "2025-12-28T01:00:00Z"
}
```

**예시 응답 (자동 적용)**
```json
{
  "status": "applied",
  "changeId": 102,
  "userId": 1,
  "userSdwtProd": "G-B",
  "effectiveFrom": "2025-12-28T01:05:00Z"
}
```

### 8.3 GET `/api/v1/account/affiliation/requests`
- 승인 대상 요청 목록 반환
- `status=all`이면 상태 필터를 적용하지 않습니다.
- 쿼리 키: `status`, `q`/`search`, `user_sdwt_prod`/`userSdwtProd`, `page`, `page_size`/`pageSize`
- 승인 가능 범위가 없으면 403을 반환합니다.

**예시 응답**
```json
{
  "results": [
    {
      "id": 201,
      "status": "PENDING",
      "department": "Dept",
      "line": "Line",
      "fromUserSdwtProd": "G-A",
      "toUserSdwtProd": "G-B",
      "effectiveFrom": "2025-12-28T01:00:00Z",
      "approvedAt": null,
      "requestedAt": "2025-12-20T02:00:00Z",
      "approvedBy": null,
      "requestedBy": {"id": 1, "username": "홍길동"},
      "rejectionReason": null,
      "role": "member",
      "user": {
        "id": 1,
        "username": "홍길동",
        "email": "hong@example.com",
        "sabun": "S123",
        "knoxId": "KNOX-1",
        "department": "Dept",
        "line": "Line",
        "userSdwtProd": "G-A"
      }
    }
  ],
  "page": 1,
  "pageSize": 20,
  "total": 1,
  "totalPages": 1
}
```

### 8.4 POST `/api/v1/account/affiliation/approve`
- 승인/거절 처리
- `changeId` 필수, `decision` 기본값 `approve`
- `rejectionReason` 또는 `rejection_reason` 지원

**예시 요청 (승인)**
```json
{"changeId": 201, "decision": "approve"}
```

**예시 응답 (승인)**
```json
{
  "status": "approved",
  "changeId": 201,
  "userId": 1,
  "userSdwtProd": "G-B",
  "effectiveFrom": "2025-12-28T01:00:00Z"
}
```

**예시 요청 (거절)**
```json
{"changeId": 201, "decision": "reject", "rejectionReason": "권한 없음"}
```

**예시 응답 (거절)**
```json
{"status": "rejected", "changeId": 201}
```

### 8.5 GET/POST `/api/v1/account/affiliation/reconfirm`
- GET: 재확인 대상 여부와 예측/현재 소속을 반환합니다.
- POST: 요청 바디는 snake_case만 허용합니다.

**예시 응답 (GET)**
```json
{
  "requiresReconfirm": true,
  "predictedUserSdwtProd": "G-NEW",
  "currentUserSdwtProd": "G-OLD"
}
```

**예시 요청 (POST, 기존 유지)**
```json
{"accepted": false}
```

**예시 요청 (POST, 변경 적용)**
```json
{"accepted": true, "user_sdwt_prod": "G-NEW"}
```

### 8.6 POST `/api/v1/account/access/grants`
- 대상 사용자 키: `userId` 또는 `user_id` 또는 `knox_id`
- role 키: `role` 또는 `accessRole`
- action: `grant`(기본) / `revoke`

**예시 요청**
```json
{"user_sdwt_prod": "G-A", "userId": 55, "action": "grant", "role": "manager"}
```

**예시 응답**
```json
{
  "userId": 55,
  "username": "kim",
  "name": "kim",
  "knoxId": "KNOX-55",
  "userSdwtProd": "G-A",
  "role": "manager",
  "grantedBy": 1,
  "grantedAt": "2025-12-20T02:00:00Z"
}
```

### 8.7 GET `/api/v1/account/access/manageable`
- 관리 가능한 그룹과 해당 멤버 목록을 반환합니다.

**예시 응답**
```json
{
  "groups": [
    {
      "userSdwtProd": "G-A",
      "members": [
        {
          "userId": 1,
          "username": "kim",
          "name": "kim",
          "knoxId": "KNOX-1",
          "userSdwtProd": "G-A",
          "role": "manager",
          "grantedBy": 2,
          "grantedAt": "2025-12-20T02:00:00Z"
        }
      ]
    }
  ]
}
```

### 8.8 GET `/api/v1/account/overview`
- 계정 화면 통합 데이터 반환
- `user`, `affiliation`, `affiliationReconfirm`, `affiliationHistory`, `manageableGroups`, `mailboxAccess` 포함
- `mailboxAccess`는 `accessSource`, `role`, `grantedBy`, `grantedAt`를 함께 제공합니다.

### 8.9 GET `/api/v1/account/line-sdwt-options`
- line/user_sdwt_prod 선택 옵션을 반환합니다.

**예시 응답**
```json
{
  "lines": [
    {"lineId": "L1", "userSdwtProds": ["G-A", "G-B"]}
  ],
  "userSdwtProds": ["G-A", "G-B"]
}
```

### 8.10 POST `/api/v1/account/external-affiliations/sync`
- Airflow 토큰 필요
- 요청 바디는 snake_case만 허용합니다.

**예시 요청**
```json
{
  "records": [
    {
      "knox_id": "KNOX-1",
      "user_sdwt_prod": "G-NEW",
      "source_updated_at": "2025-12-01T00:00:00Z"
    }
  ]
}
```

**예시 응답**
```json
{"created": 1, "updated": 0, "unchanged": 0, "flagged": 1}
```

### 8.11 GET `/api/v1/auth/me`
- 사용자 정보 + pending 상태 제공

**예시 응답**
```json
{
  "id": 1,
  "usr_id": "KNOX-1",
  "avatarid": "U-12345",
  "username": "홍길동",
  "email": "hong@example.com",
  "is_superuser": false,
  "is_staff": false,
  "roles": [],
  "department": "Dept",
  "line": "Line",
  "user_sdwt_prod": "G-A",
  "pending_user_sdwt_prod": null,
  "has_pending_affiliation": false
}
```

## 9. 프론트엔드 흐름

### 9.1 온보딩 다이얼로그
- `user_sdwt_prod`가 없고 pending이 없으면 소속 선택을 강제합니다.
- `/api/v1/account/affiliation`에서 옵션을 가져옵니다.
- 사용자 department가 있으면 동일 department 옵션을 우선 노출합니다.
- 선택된 옵션의 `user_sdwt_prod`로 `/api/v1/account/affiliation`을 POST 합니다.

### 9.2 재확인 다이얼로그
- `requiresReconfirm=true`이고 pending이 없으면 재확인 다이얼로그 표시
- `/api/v1/account/affiliation`에서 옵션을 가져와 예측값을 기본 선택합니다.
- 예측값이 목록에 없으면 선택값이 승인 대기 요청으로 처리될 수 있음을 안내합니다.
- 사용자는 다이얼로그를 닫고 나중에 진행할 수 있습니다.

### 9.3 멤버/요청 화면
- `/api/v1/emails/mailboxes/members`로 멤버 목록을 로드합니다.
- `/api/v1/account/affiliation/requests`의 `role`로 승인 버튼 활성화 여부를 결정합니다.

### 9.4 계정 개요 화면
- `/api/v1/account/overview`로 소속/이력/메일함/관리 그룹을 한 번에 표시합니다.

## 10. 이메일/어시스턴트 연동
- 메일함 요약은 account 접근 권한과 이메일 멤버 정보를 병합해 반환합니다.
- superuser/staff는 모든 메일함을 조회하며, 권한 없는 경우 UNASSIGNED가 제외될 수 있습니다.
- assistant 권한 그룹은 `get_accessible_user_sdwt_prods_for_user`를 사용합니다.

## 11. 대표 시나리오

### 시나리오 A: 신규 사용자 자동 적용
- 사용자 생성 → 외부 예측 존재 → 자동 승인/적용

### 시나리오 B: 승인자 존재로 대기
- 예측 불일치 + 승인자 존재 → PENDING 생성 → 승인자 승인

### 시나리오 C: 재확인 플래그 발생
- 외부 예측 변경 → requires_affiliation_reconfirm=true → 사용자가 재확인 응답

### 시나리오 D: 권한 위임
- manager가 `/access/grants`로 member/manager 권한 부여

## 12. 에러/엣지 케이스
- 현재 소속의 권한은 revoke로 제거할 수 없습니다.
- 마지막 manager를 제거하려는 revoke는 거부됩니다.
- 기존 PENDING이 있으면 새 요청이 기존 요청을 SUPERSEDED 처리합니다.
- 자동 적용 시 effective_from은 현재 시각으로 덮어씁니다.
- 승인 가능 범위가 없으면 변경 요청 목록이 403을 반환합니다.
- 재확인 대상이 아니면 409를 반환합니다.
- 외부 동기화는 Airflow 토큰이 없으면 401/403을 반환합니다.
