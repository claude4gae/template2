# Data Movement API

파일 기반 DB 적재를 Airflow에서 트리거하는 내부 API입니다.

## 인증

모든 endpoint는 `Authorization: Bearer <AIRFLOW_TRIGGER_TOKEN>` 헤더가 필요합니다.

## 파일 적재 트리거

```http
POST /api/v1/data-movement/<table_name>/load/
```

지원 `table_name`:

| table_name | 처리 대상 |
| --- | --- |
| `m_tkin_prevent` | `/data/data_movement/m_tkin_prevent/incoming/*.csv.deflate` |
| `ctttm_workorder_list` | `/data/data_movement/ctttm_workorder_list/incoming/CT_*_WORKORDER_*.csv.deflate` |
| `ct_process_comment` | `/data/data_movement/ct_process_comment/incoming/*_CT_PROCESS_COMMENT_*.csv.deflate` |

요청 바디는 선택입니다.

```json
{
  "limit": 10,
  "dry_run": false
}
```

응답 예시:

```json
{
  "table_name": "ctttm_workorder_list",
  "processed_count": 1,
  "success_count": 1,
  "failure_count": 0,
  "outcomes": [
    {
      "file_name": "CT_MST_WORKORDER_20260529_1400.csv.deflate",
      "status": "success",
      "row_count": 120,
      "source_type": "MST"
    }
  ]
}
```

실패 파일이 하나라도 있으면 응답은 `500`이며, `outcomes`에 파일별 `error_message`가 포함됩니다.
