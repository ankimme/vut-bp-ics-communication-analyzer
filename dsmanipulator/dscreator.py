from collections import namedtuple
import numpy as np
import pandas as pd

from bidict import bidict

from .utils.dataobjects import CommunicationPair, Direction, FileColumnNames, Station


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


def create_station_ids(df: pd.DataFrame, fcn: FileColumnNames) -> bidict[int, Station]:
    """Create a dictionary of all stations in dataframe and give them an id.

    Parameters
    ----------
    df : pd.DataFrame
        Input dataframe.
    fcn : FileColumnNames
        Real names of predefined columns.

    Returns
    -------
    bidict[int, Station]
        Key : ID of station
        Value : Station

    Notes
    -----
    Depending on the fcn.double_column_station value.
    Either both ip/port columns will be used, or only ip column.
    """

    # select whether to use only ip column or both ip and port
    if fcn.double_column_station:
        src_cols = [fcn.src_ip, fcn.src_port]
        dst_cols = [fcn.dst_ip, fcn.dst_port]
    else:
        src_cols = [fcn.src_ip]
        dst_cols = [fcn.dst_ip]

    src_stations = df.loc[:, src_cols].value_counts().index.values
    dst_stations = df.loc[:, dst_cols].value_counts().index.values
    # list of tuples (ip, port)
    all_stations = np.unique(np.concatenate([src_stations, dst_stations]))

    if fcn.double_column_station:
        stations = [Station(ip, port) for ip, port in all_stations]
    else:
        # ip[0] is used because the strange tuple (ip,) in all_stations
        stations = [Station(ip[0]) for ip in all_stations]

    return bidict({i: v for i, v in enumerate(stations)})


def create_pair_ids(df: pd.DataFrame, fcn: FileColumnNames) -> bidict[int, frozenset]:
    """Create a dictionary of all pairs in dataframe and give them an id.

    Communication direction does not matter.

    Parameters
    ----------
    df : pd.DataFrame
        Input dataframe.
    fcn : FileColumnNames
        Real names of predefined columns.

    Returns
    -------
    bidict[int, frozenset]
        Key : ID of station
        Value : Pair of station ids.
    """
    assert all(col in df.columns for col in [fcn.src_station_id, fcn.dst_station_id])

    # filter only relevant columns
    tmpdf = df.loc[:, [fcn.src_station_id, fcn.dst_station_id]]

    # create a list of pairs (i.e. find all combinations in dataframe of src and dst stations)
    pairs: list[frozenset] = [frozenset(x) for x in tmpdf.value_counts().index.values]

    # remove duplicates
    pairs = [*{*pairs}]

    return bidict({i: v for i, v in enumerate(pairs)})


def create_direction_ids(df: pd.DataFrame, fcn: FileColumnNames) -> bidict[int, Direction]:
    """Create a dictionary of all communication directions in dataframe and give them an id.

    Communication direction does matter.

    Parameters
    ----------
    df : pd.DataFrame
        Input dataframe.
    fcn : FileColumnNames
        Real names of predefined columns.

    Returns
    -------
    bidict[int, Direction]
        Key : ID of station.
        Value : Pair of station ids. Source and destination.
    """
    assert all(col in df.columns for col in [fcn.src_station_id, fcn.dst_station_id])

    # filter only relevant columns
    tmpdf = df.loc[:, [fcn.src_station_id, fcn.dst_station_id]]

    # create a list of pairs (i.e. find all combinations in dataframe of src and dst stations)
    directions = [Direction(*x) for x in tmpdf.value_counts().index.values]

    return bidict({i: v for i, v in enumerate(directions)})


# def find_communication_pairs(df: pd.DataFrame, fcn: FileColumnNames) -> bidict[int, CommunicationPair]:
#     """Find all communication pairs.

#     Identify all unique communicaion pairs in dataframe and assign an id. Direction DOES matter.

#     Parameters
#     ----------
#     df : pd.DataFrame
#         Input dataframe.
#     fcn : FileColumnNames
#         Real names of predefined columns.

#     Returns
#     -------
#     bidict[int, CommunicationPair]
#         A dictionary containing every communication pair found in dataframe.
#         Key: new id of communication pair
#         Value: communication pair
#     """
#     # TODO recreate
#     assert all(col in df.columns for col in [fcn.src_ip, fcn.dst_ip, fcn.src_port, fcn.dst_port])

#     # get all combinations of ips occuring in the dataframe
#     list_of_tuples = df.loc[:, [fcn.src_ip, fcn.dst_ip, fcn.src_port, fcn.dst_port]].value_counts().index.values
#     list_of_pairs = list(map(lambda x: CommunicationPair(x[0], x[1], x[2], x[3]), list_of_tuples))
#     ids = np.arange(1, len(list_of_pairs) + 1, dtype=np.int64)

#     return bidict(zip(ids, list_of_pairs))


# endregion

# region Custom column creators


def add_station_id(df: pd.DataFrame, fcn: FileColumnNames, station_ids: bidict[int, Station], inplace: bool = False) -> pd.DataFrame:
    """Add src and dst station id columns to dataframe.

    Parameters
    ----------
    df : pd.DataFrame
        Input dataframe.
    fcn : FileColumnNames
        Real names of predefined columns.
    station_ids: bidict[int, Station]
        Key : ID of station.
        Value : Station.
    inplace : bool, optional
        Whether to perform the operation in place on the data.
        by default False.

    Returns
    -------
    pd.DataFrame
        Dataframe with new src and dst station id columns.
    """

    assert all(col in df.columns for col in [fcn.src_ip, fcn.dst_ip])

    if not inplace:
        df = df.copy()

    def get_station_id(ip, port=None):
        return station_ids.inv[Station(ip, port)]
    get_station_id_vectorized = np.vectorize(get_station_id)

    srcIPs = df[fcn.src_ip].values
    dstIPs = df[fcn.dst_ip].values

    if fcn.double_column_station:
        assert all(col in df.columns for col in [fcn.src_port, fcn.dst_port])

        srcPorts = df[fcn.src_port].values
        dstPorts = df[fcn.dst_port].values

        df[fcn.src_station_id] = get_station_id_vectorized(srcIPs, srcPorts)
        df[fcn.dst_station_id] = get_station_id_vectorized(dstIPs, dstPorts)
    else:
        df[fcn.src_station_id] = get_station_id_vectorized(srcIPs)
        df[fcn.dst_station_id] = get_station_id_vectorized(dstIPs)

    return df


def add_pair_id(df: pd.DataFrame, fcn: FileColumnNames, pair_ids: bidict[int, frozenset], inplace: bool = False) -> pd.DataFrame:
    """Add a pairId column determining the id of a communication pair. Direction does not matter.

    Parameters
    ----------
    df : pd.DataFrame
        Input dataframe.
    fcn : FileColumnNames
        Real names of predefined columns.
    pair_ids : bidict[int, frozenset]
        Key : ID of station.
        Value : Pair of stations.
    inplace : bool, optional
        Whether to perform the operation in place on the data.
        by default False.

    Returns
    -------
    pd.DataFrame
        Dataframe with new 'pairId' column.

    Notes
    -----
    Should be called after add_station_id().
    """
    assert all(col in df.columns for col in [fcn.src_station_id, fcn.dst_station_id])

    if not inplace:
        df = df.copy()

    def get_pair_id(id1, id2):
        return pair_ids.inv[frozenset({id1, id2})]
    get_pair_id_vectorized = np.vectorize(get_pair_id)

    srcIds = df[fcn.src_station_id].values
    dstIds = df[fcn.dst_station_id].values

    df[fcn.pair_id] = get_pair_id_vectorized(srcIds, dstIds)

    return df


def add_direction_id(df: pd.DataFrame, fcn: FileColumnNames, direction_ids: bidict[int, Direction], inplace: bool = False) -> pd.DataFrame:
    """Add a directionId column determining the id of a communication pair. Direction does matter.

    Parameters
    ----------
    df : pd.DataFrame
        Input dataframe.
    fcn : FileColumnNames
        Real names of predefined columns.
    direction_ids : bidict[int, Direction]
        Key : ID of station.
        Value : Source id and destination id.
    inplace : bool, optional
        Whether to perform the operation in place on the data.
        by default False.

    Returns
    -------
    pd.DataFrame
        Dataframe with new 'directionId' column.

    Notes
    -----
    Should be called after add_station_id().
    """
    assert all(col in df.columns for col in [fcn.src_station_id, fcn.dst_station_id])

    if not inplace:
        df = df.copy()

    def get_direction_id(src, dst):
        return direction_ids.inv[(src, dst)]
    get_direction_id_vectorized = np.vectorize(get_direction_id)

    srcIds = df[fcn.src_station_id].values
    dstIds = df[fcn.dst_station_id].values

    df[fcn.direction_id] = get_direction_id_vectorized(srcIds, dstIds)

    return df


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


def add_communication_id(df: pd.DataFrame, fcn: FileColumnNames, comm_pairs: bidict[int, CommunicationPair] = None, inplace: bool = False) -> pd.DataFrame:
    """Add communication id column to dataframe. Direction DOES matter.

    Parameters
    ----------
    df : pd.DataFrame
        Input dataframe.
    fcn : FileColumnNames
        Real names of predefined columns.
    comm_pairs : bidict[int, CommunicationPair]
        IDs of communication pairs.
    inplace : bool, optional
        Whether to perform the operation in place on the data.
        by default False

    Returns
    -------
    pd.DataFrame
        Dataframe with new communication ID column.
    """
    assert all(col in df.columns for col in [fcn.src_ip, fcn.dst_ip, fcn.src_port, fcn.dst_port])
    # TODO change

    if not inplace:
        df = df.copy()

    if not comm_pairs:
        comm_pairs = find_communication_pairs(df, fcn)

    srcIPs = df[fcn.src_ip].values
    dstIPs = df[fcn.dst_ip].values
    srcPorts = df[fcn.src_port].values
    dstPorts = df[fcn.dst_port].values

    def f(a, b, c, d):
        return comm_pairs.inv[CommunicationPair(a, b, c, d)]

    vf = np.vectorize(f)

    df[fcn.communication_id] = vf(srcIPs, dstIPs, srcPorts, dstPorts)

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


# def add_pair_id(df: pd.DataFrame, fcn: FileColumnNames, inplace: bool = False) -> pd.DataFrame:
#     """Add a pairId column determining the id of a communication pair. Direction does not matter.

#     Parameters
#     ----------
#     df : pd.DataFrame
#         Input dataframe.
#     fcn : FileColumnNames
#         Real names of predefined columns.
#     inplace : bool, optional
#         Whether to perform the operation in place on the data.
#         by default False

#     Returns
#     -------
#     pd.DataFrame
#         Dataframe with new 'pairId' column.

#     Notes
#     -----
#     Should be called after add_station_id()
#     """
#     assert all(col in df.columns for col in [fcn.src_station_id, fcn.dst_station_id])

#     def reversed_comm_pair(comm_pair: CommunicationPair) -> CommunicationPair:
#         return CommunicationPair(src_ip=comm_pair.dst_ip, dst_ip=comm_pair.src_ip, src_port=comm_pair.dst_port, dst_port=comm_pair.src_port)

#     if not inplace:
#         df = df.copy()

#     comm_pairs = find_communication_pairs(df, fcn)

#     x = {}

#     i = 0
#     for comm_pair in comm_pairs.values():
#         if comm_pair not in x.values():
#             x[comm_pair] = i
#             x[reversed_comm_pair(comm_pair)] = i
#             i += 1

#     srcIPs = df[fcn.src_ip].values
#     dstIPs = df[fcn.dst_ip].values
#     srcPorts = df[fcn.src_port].values
#     dstPorts = df[fcn.dst_port].values

#     def f(a, b, c, d):
#         return x[CommunicationPair(a, b, c, d)]

#     vf = np.vectorize(f)

#     df[fcn.pair_id] = vf(srcIPs, dstIPs, srcPorts, dstPorts)

#     return df


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
        df = df.drop(col_name, axis=1)

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
