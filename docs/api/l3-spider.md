# L3 Spider API

L3 Spider API는 read-only mount된 `daily_anomaly` Parquet 파일을 조회해 반도체 이상감지 대시보드 데이터를 반환합니다.

## 공통

| 항목 | 값 |
| --- | --- |
| Prefix | `/api/v1/l3_spider/` |
| Auth | Django session 로그인 필요 |
| Data root | `L3_SPIDER_DATA_ROOT` |
| Request/Response | camelCase |
| Side effect | 없음. 파일 read-only 조회만 수행 |

## Data Layout

`L3_SPIDER_DATA_ROOT` 아래 파일은 아래 구조로 조회합니다.

```text
{date}/{lineId}/{processId}/{edsStep}/{filename}
```

파일명은 확장자 없는 `step_seq#ppid#index` 형식을 기본으로 지원합니다.

```text
2025-01-15/L1/P1/EDS_M/S1#PPID_A#0
```

호환을 위해 `S1#PPID_A#0.parquet`도 같은 방식으로 파싱합니다. `data.parquet`처럼 파싱할 수 없는 파일명은 Parquet 내부의 `step_seq`, `ppid` 컬럼을 사용합니다.

## Endpoints

| Method | Path | 설명 |
| --- | --- | --- |
| `GET` | `meta` | 선택 가능한 날짜, Line, Process, EDS Step과 availability를 반환 |
| `POST` | `summary` | 선택 조건 기준 통계, step/PPID, bin, High Risk 목록을 반환 |
| `POST` | `data` | 선택 조건과 차트 필터 기준 Plotly 표시용 row 목록을 반환 |

## Summary Response 주요 필드

| 필드 | 설명 |
| --- | --- |
| `ppidEqcs` | PPID별 전체 EQPCH 후보 |
| `ppidHighRiskEqcs` | PPID별 High Risk가 발생한 EQPCH 후보. EQPCH 선택 패널은 이 값을 사용 |
| `eqcAnomalyBins` | EQPCH별 Warning 또는 High Risk가 발생한 bin 후보 |
| `eqcHighRiskBins` | EQPCH별 High Risk가 발생한 bin 후보. EQPCH 선택 패널의 숫자 hint는 이 값의 개수를 사용 |

## Request Body

`summary`와 `data`는 아래 기본 선택값을 사용합니다.

```json
{
  "dates": ["2025-01-15"],
  "lineIds": ["L1"],
  "processIds": ["P1"],
  "edsSteps": ["EDS_M"]
}
```

`data`는 추가 차트 필터를 받을 수 있습니다.

```json
{
  "selectedEqcs": ["EQC_A"],
  "selectedStepBins": ["S1|||BIN_A"],
  "selectedPpidBins": ["S1|||PPID_A|||BIN_A"],
  "selectedSteps": ["S1"],
  "checkedPpids": ["PPID_A"],
  "checkedBins": ["BIN_A"]
}
```

## 오류

| Status | 조건 |
| --- | --- |
| 400 | 안전하지 않은 경로 segment 또는 폴더가 아닌 데이터 root |
| 401 | 로그인하지 않은 사용자 |
| 404 | `L3_SPIDER_DATA_ROOT` 경로 없음 |
