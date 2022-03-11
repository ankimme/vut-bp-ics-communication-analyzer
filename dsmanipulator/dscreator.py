import numpy as np
import pandas as pd

from bidict import bidict

from .utils.dataobjects import CommunicationPair, FileColumnNames


# region Utilities


def convert_to_timeseries(df: pd.DataFrame, fcn: FileColumnNames) -> pd.DataFrame:
    """Convert timeStamp column to datetime index.

    Parameters
    ----------
    df : pd.DataFrame
        Input dataframe.
    fcn : FileColumnNames
        Real names of predefined columns.

    Returns
    -------
    pd.DataFrame
        Dataframe with converted index.

    Preconditions
    ------------
    Dataframe must have timeStamp column of np.datetime64 type (or its subtype).

    Notes
    -----
    Should be called after add_relative_days()
    """
    assert fcn.timestamp in df.columns
    assert np.issubdtype(df[fcn.timestamp].dtype, np.datetime64)

    df = df.set_index(pd.DatetimeIndex(df[fcn.timestamp])).drop([fcn.timestamp], axis=1)
    return df


def find_communication_pairs_l3(df: pd.DataFrame, fcn: FileColumnNames) -> bidict[int, CommunicationPair]:
    """Find all L3 communication pairs.

    Identify all unique L3 communicaion pairs in dataframe and assign an id.

    L3: ip to ip

    Parameters
    ----------
    df : pd.DataFrame
        Input dataframe.
    fcn : FileColumnNames
        Real names of predefined columns.

    Returns
    -------
    bidict[int, CommunicationPair]

        A dictionary containing every communication pair found in dataframe.
        Key: new id of communication pair
        Value: communication pair
    """
    assert all(col in df.columns for col in [fcn.src_ip, fcn.dst_ip])

    # get all combinations of ips occuring in the dataframe
    list_of_tuples = df.loc[:, [fcn.src_ip, fcn.dst_ip]].value_counts().index.values
    list_of_pairs = list(map(lambda x: CommunicationPair(x[0], x[1]), list_of_tuples))
    ids = np.arange(1, len(list_of_pairs) + 1, dtype=np.int64)

    return bidict(zip(ids, list_of_pairs))


def find_communication_pairs_l4(df: pd.DataFrame, fcn: FileColumnNames) -> bidict[int, CommunicationPair]:
    """Find all L4 communication pairs.

    Identify all unique L4 communicaion pairs in dataframe and assign an id.

    L4: ip:port to ip:port

    Parameters
    ----------
    df : pd.DataFrame
        Input dataframe.
    fcn : FileColumnNames
        Real names of predefined columns.

    Returns
    -------
    bidict[int, CommunicationPair]

        A dictionary containing every communication pair found in dataframe.
        Key: new id of communication pair
        Value: communication pair
    """
    assert all(col in df.columns for col in [fcn.src_ip, fcn.dst_ip, fcn.src_port, fcn.dst_port])

    # get all combinations of ips occuring in the dataframe
    list_of_tuples = df.loc[:, [fcn.src_ip, fcn.dst_ip, fcn.src_port, fcn.dst_port]].value_counts().index.values
    list_of_pairs = list(map(lambda x: CommunicationPair(x[0], x[1], x[2], x[3]), list_of_tuples))
    ids = np.arange(1, len(list_of_pairs) + 1, dtype=np.int64)

    return bidict(zip(ids, list_of_pairs))


# endregion


# region Custom column creators


def add_inter_arrival_time_ad(df: pd.DataFrame, fcn: FileColumnNames, inplace: bool = False) -> pd.DataFrame:
    """Add interArrivalTimeAD (all directions) column to dataframe.

    Use all packets. Direction does not matter.

    Parameters
    ----------
    df : pd.DataFrame
        Input dataframe.
    fcn : FileColumnNames
        Real names of predefined columns.
    inplace : bool, optional
        Whether to perform the operation in place on the data.
        by default False

    Returns
    -------
    pd.DataFrame
        Dataframe with interArrivalTimeAD column.
    """
    assert fcn.rel_time in df.columns

    if not inplace:
        df = df.copy()

    # convert to numpy array
    times = df[fcn.rel_time].values

    # create shifted array (first emlement is doubled and the rest is shifted right)
    shifted = np.concatenate((times[0:1], times[:-1]))

    # compute inter arrival time
    df["interArrivalTimeAD"] = times - shifted

    return df


def add_inter_arrival_time_sd(df: pd.DataFrame, fcn: FileColumnNames, inplace: bool = False) -> pd.DataFrame:
    """Add interArrivalTimeSD (single direction) column to dataframe.

    Use only packets in same direction.

    Parameters
    ----------
    df : pd.DataFrame
        Input dataframe.
    fcn : FileColumnNames
        Real names of predefined columns.
    inplace : bool, optional
        Whether to perform the operation in place on the data.
        by default False

    Returns
    -------
    pd.DataFrame
        Dataframe with interArrivalTimeSD column.

    Notes
    -----
    Should be called after add_communication_direction()
    """
    assert all(col in df.columns for col in [fcn.rel_time, "masterToSlave"])

    if not inplace:
        df = df.copy()

    # M2S inter arrival times
    # filter only relative times of packets in master to slave direction
    times = df.loc[df["masterToSlave"], fcn.rel_time].values
    shifted = np.concatenate((times[0:1], times[:-1]))
    m2s = times - shifted

    # S2M inter arrival times
    times = df.loc[~df["masterToSlave"], fcn.rel_time].values
    shifted = np.concatenate((times[0:1], times[:-1]))
    s2m = times - shifted

    assert len(m2s) + len(s2m) == len(df.index)

    # get masks
    mask_m2s = df["masterToSlave"].values
    mask_s2m = np.invert(mask_m2s)
    df_len = len(df.index)

    # get indices based on masks
    m2s_indices = np.nonzero(mask_m2s)
    s2m_indices = np.nonzero(mask_s2m)

    # fill resulting array
    result = np.empty(df_len)
    result[m2s_indices] = m2s
    result[s2m_indices] = s2m

    df["interArrivalTimeSD"] = result

    return df


def add_communication_id_l3(df: pd.DataFrame, fcn: FileColumnNames, inplace: bool = False) -> pd.DataFrame:
    """Add L3 communication id column to dataframe.

    Parameters
    ----------
    df : pd.DataFrame
        Input dataframe.
    fcn : FileColumnNames
        Real names of predefined columns.
    inplace : bool, optional
        Whether to perform the operation in place on the data.
        by default False

    Returns
    -------
    pd.DataFrame
        Dataframe with new L3 communication ID column.
    """
    assert all(col in df.columns for col in [fcn.src_ip, fcn.dst_ip])

    if not inplace:
        df = df.copy()

    comm_pairs_l3_bidict = find_communication_pairs_l3(df, fcn)

    srcIPs = df[fcn.src_ip].values
    dstIPs = df[fcn.dst_ip].values

    def f(a, b):
        return comm_pairs_l3_bidict.inv[CommunicationPair(a, b)]

    vf = np.vectorize(f)

    df[fcn.l3_communication_id] = vf(srcIPs, dstIPs)

    return df


def add_communication_id_l4(df: pd.DataFrame, fcn: FileColumnNames, inplace: bool = False) -> pd.DataFrame:
    """Add L4 communication id column to dataframe.

    Parameters
    ----------
    df : pd.DataFrame
        Input dataframe.
    fcn : FileColumnNames
        Real names of predefined columns.
    inplace : bool, optional
        Whether to perform the operation in place on the data.
        by default False

    Returns
    -------
    pd.DataFrame
        Dataframe with new L4 communication ID column.
    """
    assert all(col in df.columns for col in [fcn.src_ip, fcn.dst_ip, fcn.src_port, fcn.dst_port])

    if not inplace:
        df = df.copy()

    comm_pairs_l4_bidict = find_communication_pairs_l4(df, fcn)

    srcIPs = df[fcn.src_ip].values
    dstIPs = df[fcn.dst_ip].values
    srcPorts = df[fcn.src_port].values
    dstPorts = df[fcn.dst_port].values

    def f(a, b, c, d):
        return comm_pairs_l4_bidict.inv[CommunicationPair(a, b, c, d)]

    vf = np.vectorize(f)

    df[fcn.l4_communication_id] = vf(srcIPs, dstIPs, srcPorts, dstPorts)

    return df


def add_communication_direction(df: pd.DataFrame, fcn: FileColumnNames, master_station_ip: str, inplace: bool = False) -> pd.DataFrame:
    """Add a bool column 'masterToSlave' determining whether the packet was sent from master to slave.

    True: master -> slave
    False: slave -> master

    Parameters
    ----------
    df : pd.DataFrame
        Input dataframe.
    fcn : FileColumnNames
        Real names of predefined columns.
    master_station : str
        Ip address of master station, use same format as ip address in dataset.
    inplace : bool, optional
        Whether to perform the operation in place on the data.
        by default False

    Returns
    -------
    pd.DataFrame
        Dataframe with new 'masterToSlave' column.
    """
    assert fcn.src_ip in df.columns

    if not inplace:
        df = df.copy()

    srcIPs = df[fcn.src_ip].values
    df["masterToSlave"] = srcIPs == master_station_ip

    return df


def add_pair_id(df: pd.DataFrame, fcn: FileColumnNames, inplace: bool = False) -> pd.DataFrame:
    """Add a pairId column determining the id of a communication pair. Direction does not matter.

        Parameters
    ----------
    df : pd.DataFrame
        Input dataframe.
    fcn : FileColumnNames
        Real names of predefined columns.
    inplace : bool, optional
        Whether to perform the operation in place on the data.
        by default False

    Returns
    -------
    pd.DataFrame
        Dataframe with new 'pairId' column.
    """
    assert all(col in df.columns for col in [fcn.src_ip, fcn.dst_ip, fcn.src_port, fcn.dst_port])

    def reversed_comm_pair(comm_pair: CommunicationPair) -> CommunicationPair:
        return CommunicationPair(src_ip=comm_pair.dst_ip, dst_ip=comm_pair.src_ip, src_port=comm_pair.dst_port, dst_port=comm_pair.src_port)

    if not inplace:
        df = df.copy()

    comm_pairs_l4_bidict = find_communication_pairs_l4(df, fcn)

    x = {}

    i = 0
    for comm_pair in comm_pairs_l4_bidict.values():
        if comm_pair not in x.values():
            x[comm_pair] = i
            x[reversed_comm_pair(comm_pair)] = i
            i += 1

    srcIPs = df[fcn.src_ip].values
    dstIPs = df[fcn.dst_ip].values
    srcPorts = df[fcn.src_port].values
    dstPorts = df[fcn.dst_port].values

    def f(a, b, c, d):
        return x[CommunicationPair(a, b, c, d)]

    vf = np.vectorize(f)

    df[fcn.l4_pair_id] = vf(srcIPs, dstIPs, srcPorts, dstPorts)

    return df


def add_relative_days(df: pd.DataFrame, fcn: FileColumnNames, inplace: bool = False) -> pd.DataFrame:
    """Add a realtive day column and update dateTime column.

    The relative day will be added to the dateTime column.
    The date will be wrong, but it will reflect the relative time .

    Parameters
    ----------
    df : pd.DataFrame
        Input dataframe.
    fcn : FileColumnNames
        Real names of predefined columns.
    inplace : bool, optional
        Whether to perform the operation in place on the data.
        by default False

    Returns
    -------
    pd.DataFrame
        Dataframe with new relativeDay column and updated timeStamp column.

    Preconditions
    ------------
    Dataframe must have timeStamp column of np.datetime64 type (or its subtype).

    Notes
    -----
    Should be called before convert_to_timeseries()
    """
    assert fcn.timestamp in df.columns
    assert fcn.rel_day not in df.columns

    if not inplace:
        df = df.copy()

    # convert to numpy array
    dates = df[fcn.timestamp].values

    # create shifted array
    zero = [np.datetime64(0, "s")]
    shifted = np.concatenate((zero, dates[:-1]))

    # compute relative days
    # first get ones on rows where the time is smaller than on the previous row
    # then use cumulative sum to get a relative day value for every row
    relative_days = np.where(dates < shifted, 1, 0).cumsum()
    df[fcn.rel_day] = relative_days

    # add relative day to timestamp column
    df[fcn.timestamp] = df[fcn.timestamp].values + relative_days * np.timedelta64(1, "D")

    return df


def expand_values_to_columns(df: pd.DataFrame, col_name: str, inplace: bool = False, drop_column: bool = True) -> pd.DataFrame:
    """Expand column values to independent columns.

    Parameters
    ----------
    df : pd.DataFrame
        Input dataframe.
    col_name : str
        Name of column to be expanded.
    inplace : bool, optional
        Whether to perform the operation in place on the data.
        by default False
    drop_column : bool, optional
        Drop the original column.
        by default True

    Returns
    -------
    pd.DataFrame
        Dataframe with a new column for each values of the original column.

    Notes
    -----
    NaN values are ignored.
    """
    assert col_name in df.columns

    if not inplace:
        df = df.copy()

    original_values = df[col_name].values

    unique_values = np.unique(original_values)

    # drop nans in arrays of all types
    unique_values = unique_values[unique_values == unique_values]

    for value in unique_values:
        df[f"{col_name}:{value}"] = original_values == value

    if drop_column:
        df.drop(col_name, axis=1)

    return df


# endregion

# region Filters

# Vraci df vyfiltrovany podle absolutniho casu (vcetne hranicnich hodnot)
# def filter_by_time_abs(df: pd.DataFrame, start: datetime, end: datetime) -> pd.DataFrame:
#     return df[(df['TimeStamp'] >= start) & (df['TimeStamp'] <= end)]

# # Vraci df vyfiltrovany podle relativniho casu (vcetne hranicnich hodnot)
# def filter_by_time_rel(df: pd.DataFrame, end: float) -> pd.DataFrame:
#     return filter_by_time_rel(df, 0.0, end)

# def filter_by_time_rel(df: pd.DataFrame, start: float, end: float) -> pd.DataFrame:
#     return df[(df['Relative Time'] >= start) & (df['Relative Time'] <= end)]

# endregion
