# =============================================================================
# 모듈 설명: Auto S/P용 메일 본문/제목 템플릿을 제공합니다.
# - 주요 대상: TEMPLATE_KEY, SUBJECT_TEMPLATE, BODY_TEMPLATE, build_subject
# - 불변 조건: 제목은 요청된 대괄호 구분 형식을 유지합니다.
# =============================================================================

"""Auto S/P 메일 템플릿 정의 모음."""
from __future__ import annotations

from typing import Any

TEMPLATE_KEY = "auto_sp"
SUBJECT_TEMPLATE = "[Auto S/P][{step_seq}][{eqpid}-{chamber_ids}][{lot_id}][{ppid}]"
BODY_TEMPLATE = """<div>
  <div style="margin:8px 0;">
    <table style="border:1px solid #ccc; border-collapse:collapse; width:auto;">
      <caption style="caption-side:bottom; text-align:right; font-size:11px; color:#888; margin:0; padding:0;">
        SOP by : {{ knoxid|default:"-" }} ({{ user_sdwt_prod|default:"-" }})
      </caption>
      <thead>
        <tr>
          <th style="border:1px solid #ccc; background-color:#F2F2F2; text-align:center; padding:4px; padding-left:8px; padding-right:8px; font-size:12px;">Step_seq</th>
          <th style="border:1px solid #ccc; background-color:#F2F2F2; text-align:center; padding:4px; padding-left:8px; padding-right:8px; font-size:12px;">PPID</th>
          <th style="border:1px solid #ccc; background-color:#F2F2F2; text-align:center; padding:4px; padding-left:8px; padding-right:8px; font-size:12px;">EQP_CB</th>
          <th style="border:1px solid #ccc; background-color:#F2F2F2; text-align:center; padding:4px; padding-left:8px; padding-right:8px; font-size:12px;">Lot_id</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td style="border:1px solid #ccc; text-align:center; padding:4px; padding-left:8px; padding-right:8px; font-size:14px;">{{ main_step|default:"-" }}</td>
          <td style="border:1px solid #ccc; text-align:center; padding:4px; padding-left:8px; padding-right:8px; font-size:14px;">{{ ppid|default:"-" }}</td>
          <td style="border:1px solid #ccc; text-align:center; padding:4px; padding-left:8px; padding-right:8px; font-size:14px;">{{ eqp_cb|default:"-" }}</td>
          <td style="border:1px solid #ccc; text-align:center; padding:4px; padding-left:8px; padding-right:8px; font-size:14px;">{{ lot_id|default:"-" }}</td>
        </tr>
      </tbody>
    </table>
  </div>

  <div style="margin:4px 0;">
    <div style="font-size:14px;">
      📄 CTTTM URL :
      {% if ctttm_urls %}
        {% for item in ctttm_urls %}
          <a href="{{ item.url }}" target="_blank" rel="noopener noreferrer" style="font-size:14px;">{{ item.label }}</a>{% if not forloop.last %},{% endif %}
        {% endfor %}
      {% else %}
        <span style="font-size:14px; color:#999;">-</span>
      {% endif %}
    </div>
  </div>

  {% if comment_raw %}
    <div style="margin:4px 0;">
      <div style="font-size:14px; margin-top:12px; white-space:pre-wrap;">🎨 Comment : {{ comment_raw }}</div>
      <div style="font-size:14px; margin-top:12px; white-space:pre-wrap;">💬 답변  :&nbsp; </div>
    </div>
  {% endif %}

  <div style="margin:4px 0;">
    <div style="font-size:14px; margin-top:12px;">💿 Defect Image :</div>
    {% if defect_urls %}
      <div style="margin-top:6px;">
        {% for item in defect_urls %}
          {% if item.image_urls %}
            {% for image_url in item.image_urls %}
              <a href="{{ item.map_url }}" target="_blank" rel="noopener noreferrer" style="display:inline-block; margin:0 8px 8px 0; text-decoration:none;">
                <img src="{{ image_url }}" alt="Defect {{ item.label }}" width="250" style="display:block; max-width:250px; width:100%; height:auto; border:1px solid #ddd;" />
              </a>
            {% endfor %}
          {% else %}
            <a href="{{ item.map_url }}" target="_blank" rel="noopener noreferrer" style="font-size:14px;">{{ item.label }}</a>{% if not forloop.last %},{% endif %}
          {% endif %}
        {% endfor %}
      </div>
    {% else %}
      <span style="font-size:14px; color:#999;">-</span>
    {% endif %}
  </div>
</div>
"""


def _first_row_value(row: dict[str, Any], *keys: str) -> str:
    """행 데이터에서 첫 번째 유효 문자열 값을 반환합니다."""

    for key in keys:
        value = str(row.get(key) or "").strip()
        if value:
            return value
    return "-"


def build_subject(row: dict[str, Any]) -> str:
    """Auto S/P 메일 제목 문자열을 생성합니다.

    인자:
        row: Drone SOP 행 dict(행 데이터).

    반환:
        메일 제목 문자열.

    부작용:
        없음. 순수 문자열 구성입니다.
    """

    context = {
        "step_seq": _first_row_value(row, "step_seq", "main_step"),
        "eqpid": _first_row_value(row, "eqpid", "eqp_id"),
        "chamber_ids": _first_row_value(row, "chamber_ids"),
        "lot_id": _first_row_value(row, "lot_id"),
        "ppid": _first_row_value(row, "ppid"),
    }
    return SUBJECT_TEMPLATE.format_map(context)


__all__ = ["TEMPLATE_KEY", "SUBJECT_TEMPLATE", "BODY_TEMPLATE", "build_subject"]
