# =============================================================================
# 모듈: PM SPIDER 서비스 테스트
# 주요 대상: result rank와 data 상세 row 계산
# 주요 가정: 테스트 데이터는 임시 Parquet 파일로 생성합니다.
# =============================================================================
from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from django.test import SimpleTestCase, override_settings

import pandas as pd

from . import selectors, services


class PmComparisonServiceTests(SimpleTestCase):
    """PM SPIDER 파일 기반 서비스 동작을 검증합니다."""

    def _raw_base(
        self,
        root: Path,
        *,
        data_source: str,
        trace_param_name: str,
        raw_dir: str = selectors.RAW_DIR_NAME,
    ) -> Path:
        """테스트용 raw partition 경로를 반환합니다."""

        return (
            root
            / raw_dir
            / "line_id=L1"
            / "eqp_id=EQP1"
            / "fdc_bin=BIN1"
            / "dt=2026-06-01"
            / "type=ag"
            / "ppid=PPID1"
            / "recipe_id=RCP1"
            / f"data_source={data_source}"
            / f"trace_param_name={trace_param_name}"
            / "batch=001"
        )

    def _score_base(self, root: Path, *, data_type: str, score_dir: str = selectors.SCORE_DIR_NAME) -> Path:
        """테스트용 score partition 경로를 반환합니다."""

        return (
            root
            / score_dir
            / "line_id=L1"
            / "eqp_id=EQP1"
            / "type=ag"
            / f"data_type={data_type}"
        )

    def _plain_raw_base(
        self,
        root: Path,
        *,
        data_source: str,
        trace_param_name: str,
        raw_dir: str = selectors.RAW_DIR_NAME,
    ) -> Path:
        """plain raw layout 테스트 경로를 반환합니다."""

        return (
            root
            / raw_dir
            / "L1"
            / "EQP1"
            / "BIN1"
            / "2026-06-01"
            / data_source
            / "type=ag"
            / "ppid=PPID1"
            / "recipe_id=RCP1"
            / "priority=1"
            / f"trace_param_name={trace_param_name}"
        )

    def _write_trace_sample(
        self,
        root: Path,
        *,
        raw_dir: str = selectors.RAW_DIR_NAME,
        score_dir: str = selectors.SCORE_DIR_NAME,
    ) -> None:
        """테스트용 trace raw와 score 데이터를 생성합니다."""

        raw_target = self._raw_base(
            root,
            data_source="trace",
            trace_param_name="PRESSURE",
            raw_dir=raw_dir,
        )
        raw_target.mkdir(parents=True)
        pd.DataFrame(
            [
                {"날짜": "2026-04-01", "time": "2026-04-01T01:00:00Z", "value": 10.0},
                {"날짜": "2026-05-01", "time": "2026-05-01T01:00:00Z", "value": 12.0},
                {"날짜": "2026-06-01", "time": "2026-06-01T01:00:00Z", "value": 30.0},
            ]
        ).to_parquet(raw_target / "part-000.parquet", engine="pyarrow")

        score_target = self._score_base(root, data_type="trace", score_dir=score_dir)
        score_target.mkdir(parents=True)
        pd.DataFrame(
            [
                {
                    "line_id": "L1",
                    "eqp_id": "EQP1",
                    "날짜": "2026-04-01",
                    "type": "ag",
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
                    "type": "ag",
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
                    "type": "ag",
                    "data_type": "trace",
                    "item_name": "PRESSURE",
                    "step": None,
                    "wavelength": None,
                    "score": 0.12,
                },
            ]
        ).to_parquet(score_target / "part-000.parquet", engine="pyarrow")

    def _write_plain_trace_sample(self, root: Path) -> None:
        """plain raw layout trace와 기존 score 데이터를 생성합니다."""

        raw_target = self._plain_raw_base(
            root,
            data_source="trace",
            trace_param_name="PRESSURE",
        )
        raw_target.mkdir(parents=True)
        pd.DataFrame(
            [
                {"날짜": "2026-04-01", "time": "2026-04-01T01:00:00Z", "value": 10.0},
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
                    "날짜": "2026-06-01",
                    "type": "ag",
                    "data_type": "trace",
                    "item_name": "PRESSURE",
                    "score": 0.12,
                },
            ]
        ).to_parquet(score_target / "part-000.parquet", engine="pyarrow")

    def _write_oes_sample(
        self,
        root: Path,
        *,
        raw_dir: str = selectors.RAW_DIR_NAME,
        score_dir: str = selectors.SCORE_DIR_NAME,
    ) -> None:
        """테스트용 OES raw와 score 데이터를 생성합니다."""

        raw_target = self._raw_base(
            root,
            data_source="oes",
            trace_param_name="spectrum",
            raw_dir=raw_dir,
        )
        raw_target.mkdir(parents=True)
        pd.DataFrame(
            [
                {"날짜": "2026-05-01", "rcp_step": "STEP_A", "wavelength": 200.0, "value": 100.0},
                {"날짜": "2026-05-01", "rcp_step": "STEP_A", "wavelength": 201.0, "value": 120.0},
                {"날짜": "2026-06-01", "rcp_step": "STEP_A", "wavelength": 200.0, "value": 160.0},
                {"날짜": "2026-06-01", "rcp_step": "STEP_A", "wavelength": 201.0, "value": 170.0},
            ]
        ).to_parquet(raw_target / "part-000.parquet", engine="pyarrow")

        score_target = self._score_base(root, data_type="oes", score_dir=score_dir)
        score_target.mkdir(parents=True)
        pd.DataFrame(
            [
                {
                    "line_id": "L1",
                    "eqp_id": "EQP1",
                    "날짜": "2026-06-01",
                    "type": "ag",
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
                "type": "ag",
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

    def test_single_mount_uses_data_and_result_dir_names(self) -> None:
        """단일 mount 아래 data/result 폴더명을 사용하는지 확인합니다."""

        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._write_trace_sample(root)

            with override_settings(PM_COMPARISON_DATA_ROOT=str(root)):
                raw_root = selectors.ensure_dataset_root(selectors.RAW_DIR_NAME)
                score_root = selectors.ensure_dataset_root(selectors.SCORE_DIR_NAME)
                meta = services.get_meta()

        self.assertEqual(raw_root.name, "data")
        self.assertEqual(score_root.name, "result")
        self.assertEqual(meta["lineIds"], ["L1"])

    def test_plain_raw_layout_returns_meta_and_trace_rows(self) -> None:
        """plain raw layout에서도 메타와 trace 상세 row를 반환해야 합니다."""

        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._write_plain_trace_sample(root)
            selection = {
                "lineId": "L1",
                "eqpId": "EQP1",
                "fdcBin": "BIN1",
                "type": "ag",
                "ppid": "PPID1",
                "recipeId": "RCP1",
                "pmTimestamp": "2026-06-01",
                "traceParamNames": ["PRESSURE"],
                "traceDataSource": "trace",
                "oesDataSource": "oes",
            }

            with override_settings(PM_COMPARISON_DATA_ROOT=str(root)):
                meta = services.get_meta()
                result = services.compare_pm_window(selection)

        self.assertEqual(meta["lineIds"], ["L1"])
        self.assertEqual(meta["eqpIds"], ["EQP1"])
        self.assertEqual(meta["fdcBins"], ["BIN1"])
        self.assertEqual(result["trace"]["summaryRows"][0]["traceSensor"], "PRESSURE")
        self.assertEqual(len(result["trace"]["trendRows"]), 1)

    def test_compare_pm_window_returns_empty_response_without_score_rows(self) -> None:
        """result 파일이 없을 때도 pm_date KeyError 없이 빈 응답을 반환합니다."""

        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / selectors.RAW_DIR_NAME).mkdir()
            (root / selectors.SCORE_DIR_NAME).mkdir()
            selection = {
                "lineId": "L1",
                "eqpId": "EQP1",
                "fdcBin": "BIN1",
                "type": "ag",
                "ppid": "PPID1",
                "recipeId": "RCP1",
                "pmTimestamp": "2026-06-01",
                "traceParamNames": ["PRESSURE"],
                "dtValues": ["2026-06-01"],
                "traceDataSource": "trace",
                "oesDataSource": "oes",
            }

            with override_settings(PM_COMPARISON_DATA_ROOT=str(root)):
                result = services.compare_pm_window(selection)

        self.assertEqual(result["trace"]["summaryRows"], [])
        self.assertEqual(result["oes"]["summaryRows"], [])
        self.assertEqual(result["window"]["pmDate"], "2026-06-01")
