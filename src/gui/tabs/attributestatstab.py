from PyQt6.QtWidgets import QWidget, QHBoxLayout, QTableView
from gui.components import MplCanvas
from gui.utils import DataFrameModel, EventData
from dsmanipulator import dscreator as dsc
from dsmanipulator import dsanalyzer as dsa


class AttributeStatsTab(QWidget):
    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)

        layout = QHBoxLayout()

        # CANVA
        self.canvas = MplCanvas(width=5, height=5, dpi=100, parent=self)
        layout.addWidget(self.canvas)

        # TABLE DATA
        # self.table_data = TableData()
        # layout.addWidget(self.table_data)

        self.setLayout(layout)

    def update_tab(self, data: EventData) -> None:
        self.update_plot(data)
        self.update_table_data(data)
        self.update()

    def update_plot(self, data: EventData) -> None:
        # return
        # TODO assert
        if data.attribute_name:

            self.canvas.axes.cla()
            if len(data.filtered_df.index) == 0:
                return

            dsa.plot_attribute_values(
                data.filtered_df, data.fcn, self.canvas.axes, data.attribute_name, data.resample_rate
            )

            self.canvas.draw()

    def update_table_data(self, data: EventData) -> None:
        # self.table_data.update_model(data.df)
        return
        tmpdf = data.df_og.loc[:, data.df_og.columns]
        self.df_model = DataFrameModel(tmpdf)
        self.setModel(self.df_model)
        self.update()


class TableData(QTableView):
    def __init__(self, parent: QWidget = None) -> None:
        super().__init__(parent)

        self.df_table_data: DataFrameModel

        self.setSortingEnabled(True)
        self.horizontalHeader().setStretchLastSection(True)
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)

    def update_model(self, data: EventData) -> None:
        tmpdf = data.df_og.loc[:, data.df_og.columns]
        self.df_model = DataFrameModel(tmpdf)
        self.setModel(self.df_model)
        self.update()
