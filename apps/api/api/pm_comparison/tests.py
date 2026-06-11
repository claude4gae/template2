# =============================================================================
# 모듈: PM SPIDER 서비스 테스트
# 주요 대상: score_data rank와 raw_data 상세 row 계산
# 주요 가정: 테스트 데이터는 임시 Parquet 파일로 생성합니다.
# =============================================================================
from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from django.test import SimpleTestCase, override_settings

import pandas as pd

from . import services


class PmComparisonServiceTests(SimpleTestCase):
    """PM SPIDER 파일 기반 서비스 동작을 검증합니다."""

    def _raw_base(self, root: Path, *, data_source: str, trace_param_name: str) -> Path:
        """테스트용 raw_data partition 경로를 반환합니다."""

        return (
            root
            / "raw_data"
            / "line_id=L1"
            / "eqp_id=EQP1"
            / "fdc_bin=BIN1"
            / "dt=2026-06-01"
            / "pattern=NPW"
            / "ppid=PPID1"
            / "recipe_id=RCP1"
            / f"data_source={data_source}"
            / f"trace_param_name={trace_param_name}"
            / "batch=001"
        )

    def _score_base(self, root: Path, *, data_type: str) -> Path:
        """테스트용 score_data partition 경로를 반환합니다."""

        return (
            root
            / "score_data"
            / "line_id=L1"
            / "eqp_id=EQP1"
            / "pattern=NPW"
            / f"data_type={data_type}"
        )

    def _write_trace_sample(self, root: Path) -> None:
        """테스트용 trace raw_data와 score_data를 생성합니다."""

        raw_target = self._raw_base(root, data_source="trace", trace_param_name="PRESSURE")
        raw_target.mkdir(parents=True)
        pd.DataFrame(
            [
                {"날짜": "2026-04-01", "time": "2026-04-01T01:00:00Z", "value": 10.0},
                {"날짜": "2026-05-01", "time": "2026-05-01T01:00:00Z", "value": 12.0},
                {"날짜": "2026-06-01", "time": "2026-06-01T01:00:00Z", "value": 30.0},
            ]
        ).to_parquet(raw_target / "part-000.parquet", engine="pyarrow")

        score_target = self._score_base(root, data_type="trace")
        score_target.mkdir(parents=True)
        pd.DataFrame(
            [
                {
                    "line_id": "L1",
                    "eqp_id": "EQP1",
                    "날짜": "2026-04-01",
                    "pattern": "NPW",
                    "data_type": "trace",
                    "item_name": "PRESSURE",
                    "step": None,
                    "wavelength": None,
                    "score": 0.52,
                },
                {
                    "line_id": "L1",
                    "eqp_id": "EQP1",
                    "날짜": "2026-05-01",
                    "pattern": "NPW",
                    "data_type": "trace",
                    "item_name": "PRESSURE",
                    "step": None,
                    "wavelength": None,
                    "score": 0.42,
                },
                {
                    "line_id": "L1",
                    "eqp_id": "EQP1",
                    "날짜": "2026-06-01",
                    "pattern": "NPW",
                    "data_type": "trace",
                    "item_name": "PRESSURE",
                    "step": None,
                    "wavelength": None,
                    "score": 0.12,
                },
            ]
        ).to_parquet(score_target / "part-000.parquet", engine="pyarrow")

    def _write_oes_sample(self, root: Path) -> None:
        """테스트용 OES raw_data와 score_data를 생성합니다."""

        raw_target = self._raw_base(root, data_source="oes", trace_param_name="spectrum")
        raw_target.mkdir(parents=True)
        pd.DataFrame(
            [
                {"날짜": "2026-05-01", "rcp_step": "STEP_A", "wavelength": 200.0, "value": 100.0},
                {"날짜": "2026-05-01", "rcp_step": "STEP_A", "wavelength": 201.0, "value": 120.0},
                {"날짜": "2026-06-01", "rcp_step": "STEP_A", "wavelength": 200.0, "value": 160.0},
                {"날짜": "2026-06-01", "rcp_step": "STEP_A", "wavelength": 201.0, "value": 170.0},
            ]
        ).to_parquet(raw_target / "part-000.parquet", engine="pyarrow")

        score_target = self._score_base(root, data_type="oes")
        score_target.mkdir(parents=True)
        pd.DataFrame(
            [
                {
                    "line_id": "L1",
                    "eqp_id": "EQP1",
                    "날짜": "2026-06-01",
                    "pattern": "NPW",
                    "data_type": "oes",
                    "item_name": "STEP_A/200.0",
                    "step": "STEP_A",
                    "wavelength": 200.0,
                    "score": 0.08,
                }
            ]
        ).to_parquet(score_target / "part-000.parquet", engine="pyarrow")

    def test_compare_pm_window_returns_score_rank_and_raw_detail(self) -> None:
        """score rank와 raw ref/comp 상세 row가 함께 반환되는지 확인합니다."""

        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._write_trace_sample(root)
            self._write_oes_sample(root)
            selection = {
                "lineId": "L1",
                "eqpId": "EQP1",
                "fdcBin": "BIN1",
                "pattern": "NPW",
                "ppid": "PPID1",
                "recipeId": "RCP1",
                "pmTimestamp": "2026-06-01",
                "beforeHours": 2,
                "afterHours": 2,
                "traceParamNames": ["PRESSURE"],
                "dtValues": ["2026-06-01"],
                "traceDataSource": "trace",
                "oesDataSource": "oes",
                "limit": 200,
            }

            with override_settings(PM_COMPARISON_DATA_ROOT=str(root)):
                result = services.compare_pm_window(selection)
                selected_result = services.compare_pm_window(
                    {
                        **selection,
                        "refPmDates": ["2026-04-01"],
                    }
                )
                meta = services.get_meta()

        self.assertEqual(meta["lineIds"], ["L1"])
        self.assertIn("2026-06-01", meta["pmDates"])
        self.assertEqual(result["trace"]["worstSensor"]["traceSensor"], "PRESSURE")
        self.assertEqual(result["trace"]["worstSensor"]["score"], 0.12)
        self.assertEqual(result["trace"]["trendRows"][0]["cycleIndex"], -2)
        self.assertEqual(result["trace"]["trendRows"][1]["cycleIndex"], -1)
        self.assertEqual(result["trace"]["trendRows"][2]["cycleIndex"], 0)
        self.assertEqual(
            [row["cycleIndex"] for row in selected_result["trace"]["trendRows"]],
            [-2, 0],
        )
        self.assertEqual(
            [row["selected"] for row in selected_result["trace"]["refCycles"]],
            [False, True],
        )
        self.assertEqual(result["oes"]["worstStep"], "STEP_A")
        self.assertEqual(result["oes"]["worstWavelength"]["score"], 0.08)
        self.assertGreaterEqual(len(result["oes"]["detailRows"]), 2)
