import numpy as np
import pandas as pd

from bidict import bidict
from os.path import exists
from datetime import timedelta

from .utils.communicationpair import CommunicationPair


class DatasetCreator:

    file_name: str
    df: pd.DataFrame
    comm_pairs_l3_bidict: bidict
    comm_pairs_l4_bidict: bidict

    def __init__(self, file_name: str):
        """Initialize a DatasetCreator instance and load data to dataframe from file.

        Parameters
        ----------
        file_name : str
            Path to csv file containing data.
        """
        self.file_name = file_name
        self.df = self._load_data()
        self.comm_pairs_l3_bidict = None
        self.comm_pairs_l4_bidict = None

    # region Utilities

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

    def find_communication_pairs_l3(self) -> bidict[int, CommunicationPair]:
        """Find all L3 communication pairs.

        Identify all unique L3 communicaion pairs in the dataframe and assign an id.

        L3: ip to ip

        Returns
        -------
        bidict[int, CommunicationPair]

            A dictionary containing every communication pair found in the dataframe.
            Key: new id of communication pair
            Value: communication pair
        """

        # get all combinations of ips occuring in the dataframe
        list_of_tuples = self.df.loc[:, ['srcIP', 'dstIP']].value_counts().index.values
        list_of_pairs = list(map(lambda x: CommunicationPair(x[0], x[1]), list_of_tuples))
        ids = np.arange(1, len(list_of_pairs) + 1, dtype=np.int64)

        return bidict(zip(ids, list_of_pairs))

    def find_communication_pairs_l4(self) -> bidict[int, CommunicationPair]:
        """Find all L4 communication pairs.

        Identify all unique L4 communicaion pairs in the dataframe and assign an id.

        L4: ip:port to ip:port

        Returns
        -------
        bidict[int, CommunicationPair]

            A dictionary containing every communication pair found in the dataframe.
            Key: new id of communication pair
            Value: communication pair
        """

        # get all combinations of ips occuring in the dataframe
        list_of_tuples = self.df.loc[:, ['srcIP', 'dstIP', 'srcPort', 'dstPort']].value_counts().index.values
        list_of_pairs = list(map(lambda x: CommunicationPair(x[0], x[1], x[2], x[3]), list_of_tuples))
        ids = np.arange(1, len(list_of_pairs) + 1, dtype=np.int64)

        return bidict(zip(ids, list_of_pairs))

    def return_deepcopy(self) -> pd.DataFrame:
        """Create a deepcopy of the dataframe.

        Returns
        -------
        pd.Dataframe
            Deep copy of created dataframe
        """
        deep = self.df.copy()
        return deep

    # endregion

    # region Custom column creators

    def add_inter_arrival_time_ad(self) -> None:
        """Add Inter arrival time all directions column to dataframe.

        Use all packets. Direction does not matter.
        """

        # convert to numpy array
        times = self.df['Relative Time'].values

        # create shifted array (first emlement is doubled and the rest is shifted right)
        shifted = np.concatenate((times[0:1], times[:-1]))

        # compute inter arrival time
        self.df['interArrivalTimeAD'] = times - shifted

    def add_inter_arrival_time_sd(self) -> None:
        """Add Inter arrival time single direction column to dataframe.

        Use only packets in same direction.
        """

        # M2S
        # filter only relative times of packets in master to slave direction
        times = self.df.loc[self.df['masterToSlave'], 'Relative Time'].values
        shifted = np.concatenate((times[0:1], times[:-1]))
        m2s = times - shifted

        # S2M
        times = self.df.loc[~self.df['masterToSlave'], 'Relative Time'].values
        shifted = np.concatenate((times[0:1], times[:-1]))
        s2m = times - shifted

        assert len(m2s) + len(s2m) == len(self.df.index)

        mask_m2s = self.df['masterToSlave'].values
        mask_s2m = np.invert(mask_m2s)
        df_len = len(self.df.index)

        assert np.count_nonzero(mask_m2s) == len(m2s) and np.count_nonzero(mask_s2m) == len(s2m)

        m2s_indices = np.nonzero(mask_m2s)
        s2m_indices = np.nonzero(mask_s2m)

        result = np.empty(df_len)

        result[m2s_indices] = m2s
        result[s2m_indices] = s2m

        self.df['interArrivalTimeSD'] = result

    def add_communication_id_l3(self) -> None:
        """Add L3 communication id column to dataframe.
        """

        self.comm_pairs_l3_bidict = self.find_communication_pairs_l3()

        srcIPs = self.df['srcIP'].values
        dstIPs = self.df['dstIP'].values

        def f(a, b):
            return self.comm_pairs_l3_bidict.inv[CommunicationPair(a, b)]

        vf = np.vectorize(f)

        self.df['l3commId'] = vf(srcIPs, dstIPs)

    def add_communication_id_l4(self) -> None:
        """Add L4 communication id column to dataframe.
        """

        self.comm_pairs_l4_bidict = self.find_communication_pairs_l4()

        srcIPs = self.df['srcIP'].values
        dstIPs = self.df['dstIP'].values
        srcPorts = self.df['srcPort'].values
        dstPorts = self.df['dstPort'].values

        def f(a, b, c, d):
            return self.comm_pairs_l4_bidict.inv[CommunicationPair(a, b, c, d)]

        vf = np.vectorize(f)

        self.df['l4commId'] = vf(srcIPs, dstIPs, srcPorts, dstPorts)

    def add_communication_direction(self, master_station) -> None:
        """Add column determining whether the packet was sent from master to slave

        Parameters
        ----------
        master_station : str
            ip address in string format of master station, use same format as ip address in dataset
        """
        srcIPs = self.df['srcIP'].values
        self.df['masterToSlave'] = srcIPs == master_station

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

    # endregion
