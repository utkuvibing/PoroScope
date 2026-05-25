"""PoroScope napari plugin for interactive microstructure analysis."""

from __future__ import annotations

from pathlib import Path

import napari
import numpy as np
from magicgui import magicgui
from qtpy.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
from skimage import io as skio


class PoroScopeWidget(QWidget):
    """napari dock widget for microstructure analysis."""

    def __init__(self, viewer: napari.Viewer) -> None:
        super().__init__()
        self.viewer = viewer
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout()

        # ── Porosity Section ──
        porosity_group = QGroupBox("Porosity Analysis")
        p_layout = QVBoxLayout()

        self.pores_dark_btn = QPushButton("Analyze Porosity (Dark Pores)")
        self.pores_dark_btn.clicked.connect(lambda: self._run_porosity("dark"))
        p_layout.addWidget(self.pores_dark_btn)

        self.pores_bright_btn = QPushButton("Analyze Porosity (Bright Pores)")
        self.pores_bright_btn.clicked.connect(lambda: self._run_porosity("bright"))
        p_layout.addWidget(self.pores_bright_btn)

        porosity_group.setLayout(p_layout)
        layout.addWidget(porosity_group)

        # ── Grain Size Section ──
        grain_group = QGroupBox("Grain Size Analysis")
        g_layout = QVBoxLayout()

        self.grain_btn = QPushButton("Segment Grains (Watershed)")
        self.grain_btn.clicked.connect(self._run_grains)
        g_layout.addWidget(self.grain_btn)

        grain_group.setLayout(g_layout)
        layout.addWidget(grain_group)

        # ── Phase Section ──
        phase_group = QGroupBox("Phase Analysis")
        ph_layout = QVBoxLayout()

        self.phase_3_btn = QPushButton("3-Phase Segmentation")
        self.phase_3_btn.clicked.connect(lambda: self._run_phases(3))
        ph_layout.addWidget(self.phase_3_btn)

        self.phase_4_btn = QPushButton("4-Phase Segmentation")
        self.phase_4_btn.clicked.connect(lambda: self._run_phases(4))
        ph_layout.addWidget(self.phase_4_btn)

        phase_group.setLayout(ph_layout)
        layout.addWidget(phase_group)

        # ── Particle Section ──
        particle_group = QGroupBox("Particle Analysis")
        pt_layout = QVBoxLayout()

        self.particle_dark_btn = QPushButton("Analyze Particles (Dark)")
        self.particle_dark_btn.clicked.connect(lambda: self._run_particles("dark"))
        pt_layout.addWidget(self.particle_dark_btn)

        self.particle_bright_btn = QPushButton("Analyze Particles (Bright)")
        self.particle_bright_btn.clicked.connect(lambda: self._run_particles("bright"))
        pt_layout.addWidget(self.particle_bright_btn)

        particle_group.setLayout(pt_layout)
        layout.addWidget(particle_group)

        # ── Info Section ──
        self.info_label = QLabel("Open an image, then click an analysis button.")
        self.info_label.setWordWrap(True)
        layout.addWidget(self.info_label)

        layout.addStretch()
        self.setLayout(layout)

    def _get_active_layer(self) -> np.ndarray | None:
        """Get the currently selected image layer as a numpy array."""
        layer = self.viewer.active_layer
        if layer is None:
            self.info_label.setText("⚠ No layer selected. Open an image first.")
            return None

        data = np.asarray(layer.data)
        if data.ndim == 3 and data.shape[-1] in (3, 4):
            from skimage.color import rgb2gray
            gray = (rgb2gray(data) * 255).astype(np.uint8)
        elif data.ndim == 2:
            gray = data.astype(np.uint8)
        else:
            self.info_label.setText(f"⚠ Unsupported data shape: {data.shape}")
            return None
        return gray

    def _cleanup_layers(self, prefix: str) -> None:
        """Remove previous analysis layers with the given prefix."""
        for layer in list(self.viewer.layers):
            if isinstance(layer.name, str) and layer.name.startswith(prefix):
                self.viewer.layers.remove(layer)

    def _run_porosity(self, pores: str) -> None:
        gray = self._get_active_layer()
        if gray is None:
            return

        from .pipeline import analyze_image as _analyze
        from .config import AnalysisConfig
        from pathlib import Path
        import tempfile

        # Save temp file for pipeline
        tmp = Path(tempfile.mktemp(suffix=".png"))
        try:
            skio.imsave(str(tmp), gray)
            config = AnalysisConfig(pixel_size=1.0, unit="px", pores=pores)
            result = _analyze(tmp, config=config)
        finally:
            tmp.unlink(missing_ok=True)

        # Add layers
        self._cleanup_layers("poroscope_porosity")
        self.viewer.add_labels(
            result.labels.astype(np.int32),
            name=f"poroscope_porosity_labels",
            colormap="hsv",
        )
        overlay_rgb = np.dstack([gray] * 3).astype(np.uint8)
        overlay_rgb[result.mask] = [255, 0, 0]  # Red overlay
        self.viewer.add_image(
            overlay_rgb,
            name=f"poroscope_porosity_overlay",
            blending="translucent",
            opacity=0.4,
        )

        s = result.summary
        self.info_label.setText(
            f"Porosity ({pores}): {s['porosity_percent']:.2f}% | "
            f"Pores: {s['pore_count']} | "
            f"Density: {s.get('mean_pore_area_unit2', 'N/A'):.1f}"
        )

    def _run_grains(self) -> None:
        gray = self._get_active_layer()
        if gray is None:
            return

        from .grains import analyze_grains

        result = analyze_grains(grayscale=gray, pixel_size=1.0, unit="px")

        self._cleanup_layers("poroscope_grains")
        self.viewer.add_labels(
            result.labels.astype(np.int32),
            name="poroscope_grains",
            colormap="hsv",
        )

        s = result.summary
        astm = s.get("astm_grain_size_number")
        astm_str = f" | ASTM G: {astm:.2f}" if astm is not None else ""
        self.info_label.setText(
            f"Grains: {s['grain_count']} | "
            f"Mean Ø: {s['mean_grain_diameter_unit']:.2f} px | "
            f"Median Ø: {s['median_grain_diameter_unit']:.2f} px{astm_str}"
        )

    def _run_phases(self, n_classes: int) -> None:
        gray = self._get_active_layer()
        if gray is None:
            return

        from .phases import analyze_phases

        result = analyze_phases(gray, n_classes=n_classes, pixel_size=1.0, unit="px")

        self._cleanup_layers("poroscope_phases")
        self.viewer.add_labels(
            result.labels.astype(np.int32),
            name=f"poroscope_phases_{n_classes}",
            colormap="tab10",
        )

        s = result.summary
        dominant = s["dominant_phase_index"]
        self.info_label.setText(
            f"Phases: {s['n_phases']} | "
            f"Dominant: Phase {dominant} ({s['dominant_phase_fraction'] * 100:.1f}%)"
        )

    def _run_particles(self, pores: str) -> None:
        gray = self._get_active_layer()
        if gray is None:
            return

        from .particles import analyze_particles
        from .segmentation import threshold_image

        binary, _ = threshold_image(gray, method="otsu", pores=pores)
        result = analyze_particles(binary, pixel_size=1.0, unit="px", min_size=10)

        self._cleanup_layers("poroscope_particles")
        self.viewer.add_labels(
            result.labels.astype(np.int32),
            name=f"poroscope_particles_{pores}",
            colormap="hsv",
        )

        s = result.summary
        self.info_label.setText(
            f"Particles ({pores}): {s['particle_count']} | "
            f"Mean Ø: {s['mean_diameter_unit']:.2f} px | "
            f"Circularity: {s['mean_circularity']:.3f} | "
            f"Convexity: {s['mean_convexity']:.3f}"
        )


def poroscope_plugin():
    """Return the PoroScope widget for napari."""
    from napari import Viewer

    return PoroScopeWidget
