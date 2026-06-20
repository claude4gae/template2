"""racb_list 파일 적재 management command입니다."""

from __future__ import annotations

from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from api.data_movement.racb_list import services


class Command(BaseCommand):
    """Airflow에서 호출할 racb_list 파일 적재 command입니다."""

    help = "Load racb_list deflate CSV files into PostgreSQL."

    def add_arguments(self, parser) -> None:
        """command 옵션을 등록합니다."""

        parser.add_argument("--data-dir", dest="data_dir", help="incoming/processing을 포함할 테이블 root")
        parser.add_argument("--limit", dest="limit", type=int, help="처리할 최대 파일 수")
        parser.add_argument("--dry-run", dest="dry_run", action="store_true", help="DB 반영 없이 파싱만 수행")

    def handle(self, *args, **options) -> None:
        """racb_list 파일 적재를 실행합니다."""

        data_dir = Path(options["data_dir"]) if options.get("data_dir") else None
        summary = services.load_racb_list_files(
            data_dir=data_dir,
            dry_run=options["dry_run"],
            limit=options.get("limit"),
        )

        if summary.processed_count == 0:
            self.stdout.write("처리할 파일 없음")
            return

        for outcome in summary.outcomes:
            message = f"{outcome.status}: {outcome.file_name}, rows={outcome.row_count}"
            if outcome.error_message:
                message = f"{message}, error={outcome.error_message}"
            self.stdout.write(message)

        self.stdout.write(
            f"summary: processed={summary.processed_count}, "
            f"success={summary.success_count}, failed={summary.failure_count}"
        )
        if summary.failure_count:
            raise CommandError(f"racb_list 적재 실패 파일 수: {summary.failure_count}")
