import numpy as np
import pandas as pd

from bidict import bidict

from .utils.dataobjects import CommunicationPair


# region Utilities

def convert_to_timeseries(df: pd.DataFrame) -> pd.DataFrame:
    """Convert timeStamp column to datetime index.

    Parameters
    ----------
    df : pd.DataFrame
        Input dataframe.

    Returns
    -------
    pd.DataFrame
        Dataframe with converted index.

    Precondition
    ------------
    Dataframe must have column 'timeStamp' of np.datetime64 type (or its subtype).

    Notes
    -----
    Should be called after add_relative_days()
    """
    assert 'timeStamp' in df.columns
    assert np.issubdtype(df['timeStamp'].dtype, np.datetime64)

    df = df.set_index(pd.DatetimeIndex(df['timeStamp'])).drop(['timeStamp'], axis=1)
    return df


def find_communication_pairs_l3(df: pd.DataFrame) -> bidict[int, CommunicationPair]:
    """Find all L3 communication pairs.

    Identify all unique L3 communicaion pairs in dataframe and assign an id.

    L3: ip to ip

    Parameters
    ----------
    df : pd.DataFrame
        Input dataframe.

    Returns
    -------
    bidict[int, CommunicationPair]

        A dictionary containing every communication pair found in dataframe.
        Key: new id of communication pair
        Value: communication pair
    """
    assert all(col in df.columns for col in ['srcIp', 'dstIp'])

    # get all combinations of ips occuring in the dataframe
    list_of_tuples = df.loc[:, ['srcIp', 'dstIp']].value_counts().index.values
    list_of_pairs = list(map(lambda x: CommunicationPair(x[0], x[1]), list_of_tuples))
    ids = np.arange(1, len(list_of_pairs) + 1, dtype=np.int64)

    return bidict(zip(ids, list_of_pairs))


def find_communication_pairs_l4(df: pd.DataFrame) -> bidict[int, CommunicationPair]:
    """Find all L4 communication pairs.

    Identify all unique L4 communicaion pairs in dataframe and assign an id.

    L4: ip:port to ip:port

    Parameters
    ----------
    df : pd.DataFrame
        Input dataframe.

    Returns
    -------
    bidict[int, CommunicationPair]

        A dictionary containing every communication pair found in dataframe.
        Key: new id of communication pair
        Value: communication pair
    """
    assert all(col in df.columns for col in ['srcIp', 'dstIp', 'srcPort', 'dstPort'])

    # get all combinations of ips occuring in the dataframe
    list_of_tuples = df.loc[:, ['srcIp', 'dstIp', 'srcPort', 'dstPort']].value_counts().index.values
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

    # M2S inter arrival times
    # filter only relative times of packets in master to slave direction
    times = self.df.loc[self.df['masterToSlave'], 'Relative Time'].values
    shifted = np.concatenate((times[0:1], times[:-1]))
    m2s = times - shifted

    # S2M inter arrival times
    times = self.df.loc[~self.df['masterToSlave'], 'Relative Time'].values
    shifted = np.concatenate((times[0:1], times[:-1]))
    s2m = times - shifted

    assert len(m2s) + len(s2m) == len(self.df.index)

    # get masks
    mask_m2s = self.df['masterToSlave'].values
    mask_s2m = np.invert(mask_m2s)
    df_len = len(self.df.index)

    # get indices based on masks
    m2s_indices = np.nonzero(mask_m2s)
    s2m_indices = np.nonzero(mask_s2m)

    # fill resulting array
    result = np.empty(df_len)
    result[m2s_indices] = m2s
    result[s2m_indices] = s2m

    self.df['interArrivalTimeSD'] = result


def add_communication_id_l3(df: pd.DataFrame) -> pd.DataFrame:
    """Add L3 communication id column to dataframe.

    Parameters
    ----------
    df : pd.DataFrame
        Input dataframe.

    Returns
    -------
    pd.DataFrame
        Dataframe with new L3 communication ID column.
    """
    assert all(col in df.columns for col in ['srcIp', 'dstIp'])

    comm_pairs_l3_bidict = find_communication_pairs_l3(df)

    srcIPs = df['srcIp'].values
    dstIPs = df['dstIp'].values

    def f(a, b):
        return comm_pairs_l3_bidict.inv[CommunicationPair(a, b)]

    vf = np.vectorize(f)

    df['l3commId'] = vf(srcIPs, dstIPs)

    return df


def add_communication_id_l4(df: pd.DataFrame) -> pd.DataFrame:
    """Add L4 communication id column to dataframe.

    Parameters
    ----------
    df : pd.DataFrame
        Input dataframe.

    Returns
    -------
    pd.DataFrame
        Dataframe with new L4 communication ID column.
    """
    assert all(col in df.columns for col in ['srcIp', 'dstIp', 'srcPort', 'dstPort'])

    comm_pairs_l4_bidict = find_communication_pairs_l4(df)

    srcIPs = df['srcIp'].values
    dstIPs = df['dstIp'].values
    srcPorts = df['srcPort'].values
    dstPorts = df['dstPort'].values

    def f(a, b, c, d):
        return comm_pairs_l4_bidict.inv[CommunicationPair(a, b, c, d)]

    vf = np.vectorize(f)

    df['l4commId'] = vf(srcIPs, dstIPs, srcPorts, dstPorts)

    return df


def add_communication_direction(self, master_station) -> None:
    """Add column determining whether the packet was sent from master to slave

    Parameters
    ----------
    master_station : str
        ip address in string format of master station, use same format as ip address in dataset
    """
    srcIPs = self.df['srcIP'].values
    self.df['masterToSlave'] = srcIPs == master_station


def add_relative_days(df: pd.DataFrame) -> pd.DataFrame:
    """Add a realtive day column and update dateTime column.

    The relative day will be added to the dateTime column.
    The date will be wrong, but it will reflect the relative time .

    Parameters
    ----------
    df : pd.DataFrame
        Input dataframe.

    Returns
    -------
    pd.DataFrame
        Dataframe with new 'relativeDay' column and updated 'timeStamp' column.

    Precondition
    ------------
    Dataframe must have column 'timeStamp' of np.datetime64 type (or its subtype).

    Notes
    -----
    Should be called before convert_to_timeseries()
    """

    assert 'timeStamp' in df.columns

    # convert to numpy array
    dates = df['timeStamp'].values

    # create shifted array
    zero = [np.datetime64(0, 's')]
    shifted = np.concatenate((zero, dates[:-1]))

    # compute relative days
    # first get ones on rows where the time is smaller than on the previous row
    # then use cumulative sum to get a relative day value for every row
    relative_days = np.where(dates < shifted, 1, 0).cumsum()
    df['relativeDay'] = relative_days

    # add relative day to timestamp column
    df['timeStamp'] = df['timeStamp'].values + relative_days * np.timedelta64(1, 'D')

    return df

# endregion
