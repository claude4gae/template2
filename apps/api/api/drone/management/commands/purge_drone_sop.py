# =============================================================================
# 모듈: Drone SOP 전체 삭제 커맨드
# 주요 기능: DroneSOP 전체 hard delete
# 불변 조건: 설정 테이블은 유지하고 SOP/발송 이력만 FK cascade로 삭제합니다.
# =============================================================================
from __future__ import annotations

from django.core.management.base import BaseCommand, CommandError

from api.drone.models import DroneSOP


class Command(BaseCommand):
    """DroneSOP 전체 데이터를 수동 삭제합니다."""

    help = "Purge all drone_sop rows and cascaded dispatch/delivery history."

    def add_arguments(self, parser) -> None:
        """커맨드 옵션을 등록합니다."""

        parser.add_argument(
            "--confirm-delete-all",
            action="store_true",
            help="실제 전체 삭제를 수행합니다. 없으면 삭제하지 않고 대상 수만 출력합니다.",
        )

    def handle(self, *args: object, **options: object) -> None:
        """DroneSOP 전체 삭제 또는 대상 수 확인을 실행합니다."""

        count = DroneSOP.objects.count()
        if not options.get("confirm_delete_all"):
            self.stdout.write(
                self.style.WARNING(
                    f"dry-run: drone_sop rows matched={count}. "
                    "실제 삭제는 --confirm-delete-all 옵션을 추가하세요."
                )
            )
            return

        if count <= 0:
            self.stdout.write(self.style.SUCCESS("drone_sop purge complete: deleted=0"))
            return

        deleted, detail = DroneSOP.objects.all().delete()
        if deleted <= 0:
            raise CommandError("drone_sop purge failed: no rows were deleted")
        self.stdout.write(
            self.style.SUCCESS(
                f"drone_sop purge complete: deleted={deleted} detail={dict(detail)}"
            )
        )
