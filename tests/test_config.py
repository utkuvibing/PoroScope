import pytest

from poroscope.config import AnalysisConfig


def test_manual_threshold_validation_uses_normalized_0_to_255_range():
    with pytest.raises(ValueError, match="normalized to 0-255"):
        AnalysisConfig(
            pixel_size=1,
            unit="um",
            threshold="manual",
            threshold_value=300,
        ).validate()

