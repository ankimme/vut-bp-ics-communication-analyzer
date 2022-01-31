import numpy as np
import pandas as pd

from bidict import bidict
from os.path import exists
from datetime import timedelta

from .utils.communicationpair import CommunicationPair


class DatasetCreator:

    def __init__(self, file_name: str):
        """Initialize a DatasetCreator instance and load data to dataframe from file.

        Parameters
        ----------
        file_name : str
            Path to csv file containing data.
        """
        self.file_name = file_name
        self.df = self._load_data()
        # self._add_communication_id_columns()
        # self._add_relative_days()

        # self.df = self.df.set_index(pd.DatetimeIndex(self.df['TimeStamp'])).drop(['TimeStamp'], axis=1)

    def _load_data(self) -> pd.DataFrame:
        # todo robustnejsi pres nejaky DataSetLoader
        # todo df must have 'srcIP', 'srcPort', 'dstIP', 'dstPort', 'TimeStamp'
        # todo TimeStamp ve fromatu format="%H:%M:%S.%f"
        # todo check if file exists

        if exists(self.file_name):
            return pd.read_csv(self.file_name, sep=";", dtype={'asduType': 'category', 'numix': 'category', 'cot': 'category', 'uType': 'category', 'oa': 'category'}, parse_dates=['TimeStamp'])
        else:
            raise FileNotFoundError()

    def convert_to_timeseries(self) -> None:
        """Create datetime index from Timestamp column
        """
        # time_series = pd.Series(a.TimeStamp.index, index=a.TimeStamp)
        # ts = time_series.resample('30min').count()
        # todo pristup primo k nazvu timestamp nemusi byt spravny
        self.df = self.df.set_index(pd.DatetimeIndex(self.df['TimeStamp'])).drop(['TimeStamp'], axis=1)

    def add_inter_arrival_time(self) -> None:
        """Add Inter arrival time column to dataframe.

        Use every packet in communication.
        """

        # convert to numpy array
        times = self.df['Relative Time'].values

        # create shifted array
        zero = np.array([0], dtype=np.float64)
        shifted = np.concatenate((zero, times[:-1]))

        # compute inter arrival time
        self.df['diffast'] = times - shifted

    def add_communication_id_columns(self) -> None:
        """Add L3 and L4 communication id columns to dataframe.
        """
        l3_pairs, l4_pairs = self.find_communication_pairs()

        self.df['l3comId'] = self.df.apply(lambda row: l3_pairs.inverse[CommunicationPair(row.srcIP, row.dstIP)], axis=1).astype("category")
        self.df['l4comId'] = self.df.apply(lambda row: l4_pairs.inverse[CommunicationPair(row.srcIP, row.dstIP, row.srcPort, row.dstPort)], axis=1).astype("category")

    def add_relative_days(self) -> None:
        """Add a realtive day column and update DateTime column.

        The relative day will be added to the DateTime column.
        The date will be wrong, but it will reflect the relative time .
        """

        # convert to numpy array
        dates = self.df['TimeStamp'].values

        # create shifted array
        zero = [np.datetime64(0, 's')]
        shifted = np.concatenate((zero, dates[:-1]))

        # compute relative days
        # first get ones on rows where the time is smaller than on the previous row
        # then use cumulative sum to get a relative day value for every row
        relative_days = np.where(dates < shifted, 1, 0).cumsum()
        self.df['relativeDay'] = relative_days

        # add relative day to timestamp column
        # todo dynamic name
        self.df['TimeStamp'] = self.df['TimeStamp'].values + relative_days * np.timedelta64(1, 'D')

    def add_relative_days_slow(self) -> None:
        """Add a realtive day column and update DateTime column.

        The relative day will be added to the DateTime column.
        The date will be wrong, but it will reflect the relative time .

        """
        def find_relative_days() -> list:
            """Create a list of relative days in dataframe.

            Returns
            -------
            list
                Of format [0..0, 1..1, 2..2, 3..3, ...]
            """

            # edge cases
            if len(self.df.index) == 0:
                return []
            if len(self.df.index) == 1:
                return [0]

            # core of computation
            res_list = [0]
            counter = 0
            for i in range(1, len(self.df.index)):
                if self.df['TimeStamp'][i].time() < self.df['TimeStamp'][i - 1].time():
                    counter += 1
                res_list.append(counter)
            return res_list

        self.df['relativeDay'] = find_relative_days()

        # add relative day to timestamp column
        self.df['TimeStamp'] = self.df.apply(lambda row: row.TimeStamp + timedelta(days=row.relativeDay), axis=1)

    def find_communication_pairs(self) -> tuple[bidict[int, CommunicationPair], bidict[int, CommunicationPair]]:
        """Find L3 and L4 communication pairs.

        Identify all unique communicaion pairs in a dataframe and assign an id.

        L3: ip to ip
        L4: ip:port to ip:port

        Returns
        -------
        tuple[bidict[int, CommunicationPair], bidict[int, CommunicationPair]]
            [description]

            Two bidirectional dictionaries (L3 and L4)
            Key: id of communication pair
            Value: communication pair
        """

        tmp_l3_dict = dict()
        tmp_l4_dict = dict()
        i, j = 1, 1
        for (srcIP, srcPort, dstIP, dstPort) in zip(self.df.srcIP, self.df.srcPort, self.df.dstIP, self.df.dstPort):
            # L3
            if (srcIP, dstIP) not in tmp_l3_dict:
                tmp_l3_dict[(srcIP, dstIP)] = i
                i = i + 1

            # L4
            if (srcIP, srcPort, dstIP, dstPort) not in tmp_l4_dict:
                tmp_l4_dict[(srcIP, srcPort, dstIP, dstPort)] = j
                j = j + 1

        l4_communication_pairs = bidict()
        l3_communication_pairs = bidict()

        for key, value in tmp_l3_dict.items():
            l3_communication_pairs[value] = CommunicationPair(key[0], key[1])

        for key, value in tmp_l4_dict.items():
            l4_communication_pairs[value] = CommunicationPair(key[0], key[2], key[1], key[3])

        return l3_communication_pairs, l4_communication_pairs

    def return_deepcopy(self) -> pd.DataFrame:
        """Create a deepcopy of the dataframe.

        Returns
        -------
        pd.Dataframe
            Deep copy of created dataframe
        """
        deep = self.df.copy()
        return deep
