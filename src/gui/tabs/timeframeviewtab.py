# todo doc

from PyQt6.QtWidgets import QWidget, QTableView

from gui.utils import DataFrameModel, EventData

from dsmanipulator import dscreator as dsc


class TimeFrameViewTab(QTableView):
    def __init__(self, parent: QWidget = None) -> None:
        """TODO

        Attributes
        ----------
        TODO

        """
        super().__init__(parent)

        self.df_model: DataFrameModel
        self.horizontalHeader().setStretchLastSection(True)
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)

    def update_model(self, data: EventData) -> None:
        if data.attribute_name:
            # filter rows TODO delete
            # filtered_pair_ids = dsa.get_connected_pairs(data.master_station_id, data.slave_station_ids, data.pair_ids)
            # tmpdf = data.df[data.df[data.fcn.pair_id].isin(filtered_pair_ids)]

            # filter columns

            tmpdf = data.filtered_df.loc[:, [data.fcn.timestamp, data.attribute_name]]

            tmpdf = dsc.convert_to_timeseries(tmpdf, data.fcn)
            tmpdf = dsc.expand_values_to_columns(tmpdf, data.attribute_name)
            tmpdf = tmpdf.resample(data.resample_rate).sum()
            tmpdf = tmpdf.rename(columns={og: og.lstrip(f"{data.attribute_name}:") for og in tmpdf.columns})

            self.df_model = DataFrameModel(tmpdf)
            self.setModel(self.df_model)
            self.update()
