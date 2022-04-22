# TODO doc

from matplotlib.backends.backend_qtagg import NavigationToolbar2QT
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTableView
from gui.components import MplCanvas
from gui.utils import DataFrameModel, EventData
from dsmanipulator import dsanalyzer as dsa


class AttributeStatsTab(QWidget):
    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)

        layout = QVBoxLayout()

        # CANVA
        self.canvas = MplCanvas(width=6, height=4.5, dpi=100, parent=self)
        toolbar = NavigationToolbar2QT(self.canvas, self)

        layout.addWidget(toolbar)
        layout.addWidget(self.canvas)

        # TABLE DATA
        self.attribute_stats_table = QTableView()
        self.attribute_stats_table.setSortingEnabled(True)
        self.attribute_stats_table.setAlternatingRowColors(True)
        self.attribute_stats_table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        layout.addWidget(self.attribute_stats_table)

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
            if len(data.df_filtered.index) > 0 and len(data.attribute_values) > 0:

                dsa.plot_attribute_values(
                    data.df_filtered[data.df_filtered[data.attribute_name].isin(data.attribute_values)],
                    data.fcn,
                    data.attribute_name,
                    data.resample_rate,
                    self.canvas.axes,
                )

            self.canvas.draw()

    def update_table_data(self, data: EventData) -> None:
        if data.attribute_name:
            x = dsa.get_attribute_stats(
                data.df_filtered,
                data.fcn,
                data.attribute_name,
                data.resample_rate,
            )
            self.attribute_stats_table.setModel(DataFrameModel(x))
            self.attribute_stats_table.resizeColumnsToContents()
        # self.table_data.update_model(data.df)

        # tmpdf = data.df_og.loc[:, data.df_og.columns]
        # self.df_model = DataFrameModel(tmpdf)
        # self.setModel(self.df_model)
        # self.update()


# class TableData(QTableView):
#     def __init__(self, parent: QWidget = None) -> None:
#         super().__init__(parent)

#         self.df_table_data: DataFrameModel

#         self.setSortingEnabled(True)
#         self.horizontalHeader().setStretchLastSection(True)
#         self.setAlternatingRowColors(True)
#         self.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)

#     def update_model(self, data: EventData) -> None:
#         tmpdf = data.df_og.loc[:, data.df_og.columns]
#         self.df_model = DataFrameModel(tmpdf)
#         self.setModel(self.df_model)
#         self.update()
