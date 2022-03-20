# TODO doc

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure


class MplCanvas(FigureCanvasQTAgg):
    def __init__(self, parent=None, width=5, height=4, dpi=300) -> None:
        fig = Figure(figsize=(width, height), dpi=dpi)
        fig.set_tight_layout(True)

        super().__init__(fig)

        self.axes = fig.add_subplot(111)
        self.setParent(parent)
