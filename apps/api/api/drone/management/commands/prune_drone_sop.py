# =============================================================================
# 모듈: Drone SOP 보관 기간 정리 커맨드
# 주요 기능: created_at 기준 보관 기간 초과 DroneSOP hard delete
# 불변 조건: 보관 기간 초과 데이터는 상태와 무관하게 삭제합니다.
# =============================================================================
from __future__ import annotations

from typing import Any

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from api.drone.services.pop3.persistence import prune_old_drone_sop_rows


def _positive_int(value: Any, *, name: str) -> int:
    """양의 정수 옵션을 검증합니다."""

    try:
        normalized = int(value)
    except (TypeError, ValueError) as exc:
        raise CommandError(f"{name} must be a positive integer") from exc
    if normalized <= 0:
        raise CommandError(f"{name} must be a positive integer")
    return normalized


class Command(BaseCommand):
    """DroneSOP 보관 기간 초과 데이터를 삭제합니다."""

    help = "Prune drone_sop rows older than the retention window."

    def add_arguments(self, parser) -> None:
        """커맨드 옵션을 등록합니다."""

        parser.add_argument(
            "--days",
            type=int,
            default=getattr(settings, "DRONE_SOP_RETENTION_DAYS", 180),
            help="보관 일수입니다. 기본값은 DRONE_SOP_RETENTION_DAYS 또는 180입니다.",
        )
        parser.add_argument(
            "--batch-size",
            type=int,
            default=getattr(settings, "DRONE_SOP_PRUNE_BATCH_SIZE", 1000),
            help="한 번에 삭제할 DroneSOP 행 수입니다.",
        )
        parser.add_argument(
            "--max-batches",
            type=int,
            default=None,
            help="최대 삭제 배치 수입니다. 생략하면 후보가 없어질 때까지 삭제합니다.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="삭제하지 않고 삭제 후보 수만 출력합니다.",
        )

    def handle(self, *args: object, **options: object) -> None:
        """보관 기간 초과 DroneSOP 정리를 실행합니다."""

        days = _positive_int(options.get("days"), name="days")
        batch_size = _positive_int(options.get("batch_size"), name="batch_size")
        max_batches_raw = options.get("max_batches")
        max_batches = (
            _positive_int(max_batches_raw, name="max_batches")
            if max_batches_raw is not None
            else None
        )
        dry_run = bool(options.get("dry_run"))

        pruned = prune_old_drone_sop_rows(
            days=days,
            batch_size=batch_size,
            dry_run=dry_run,
            max_batches=max_batches,
        )
        label = "matched" if dry_run else "deleted"
        self.stdout.write(
            self.style.SUCCESS(
                f"drone_sop prune complete: {label}={pruned} days={days} batch_size={batch_size}"
            )
        )
