import shelve
import json
import pandas as pd

from rafcon.utils import log
logger = log.get_logger(__name__)


def log_to_raw_structure(execution_history_items):
    """
    :param dict executiion_history_items: history items, in the simplest case
           directly the opened shelve log file
    :return: start_item, the StateMachineStartItem of the log file
             previous, a dict mapping history_item_id --> history_item_id of previous history item
             next_, a dict mapping history_item_id --> history_item_id of the next history item (except if
                    next item is a concurrent execution branch)
             concurrent, a dict mapping history_item_id --> []list of concurrent next history_item_ids
                         (if present)
             grouped, a dict mapping run_id --> []list of history items with this run_id
    :rtype: tuple
    """
    previous = {}
    next_ = {}
    concurrent = {}
    grouped_by_run_id = {}
    start_item = None

    # if a shelve was not closed properly not all data can be caught, thus try + catch
    try:
        for k,v in execution_history_items.items():
            if v['item_type'] == 'StateMachineStartItem':
                start_item = v
            else:

                # connect the item to its predecessor
                prev_item_id = v['prev_history_item_id']
                previous[k] = prev_item_id

                if execution_history_items[prev_item_id]['item_type'] == 'ConcurrencyItem' and \
                   execution_history_items[k]['item_type'] != 'ReturnItem':
                    # this is not a return  item, thus this 'previous' relationship of this
                    # item must be a call item of one of the concurrent branches of
                    # the concurrency state
                    if prev_item_id in concurrent:
                        concurrent[prev_item_id].append(k)
                    else:
                        concurrent[prev_item_id] = [k]
                else:
                    # this is a logical 'next' relationship
                    next_[prev_item_id] = k

            rid = v['run_id']
            if rid in grouped_by_run_id:
                grouped_by_run_id[rid].append(v)
            else:
                grouped_by_run_id[rid] = [v]
    except Exception:
        logger.error("Shelve was not properly closed!")
        pass

    return start_item, previous, next_, concurrent, grouped_by_run_id


def log_to_collapsed_structure(execution_history_items, full_next=False):
    """
    Collapsed structure means that all history items belonging the same state execution are
    merged together into one object (e.g. CallItem and ReturnItem of an ExecutionState). This
    is based on the log structure in which all Items which belong together have the same run_id.
    The collapsed items hold input as well as output data (direct and scoped), and the outcome
    the state execution.
    :param dict executiion_history_items: history items, in the simplest case
           directly the opened shelve log file
    :return: start_item, the StateMachineStartItem of the log file
             next_, a dict mapping run_id --> run_id of the next executed state on the same
                    hierarchy level
             concurrent, a dict mapping run_id --> []list of run_ids of the concurrent next
                         executed states (if present)
             hierarchy, a dict mapping run_id --> run_id of the next executed state on the
                        deeper hierarchy level (the start state within that HierarchyState)
             items, a dict mapping run_id --> collapsed representation of the execution of
                    the state with that run_id
    :rtype: tuple
    """

    start_item, previous, next_, concurrent, grouped = log_to_raw_structure(execution_history_items)

    start_item = None
    collapsed_next = {}
    collapsed_concurrent ={}
    collapsed_hierarchy = {}
    collapsed_items = {}

    # single state executions are not supported
    if len(next_) == 0 or len(next_) == 1:
        for rid, gitems in grouped.items():
            if gitems[0]['item_type'] == 'StateMachineStartItem':
                item = gitems[0]
                execution_item = {}
                for l in ['description', 'path_by_name', 'state_name', 'run_id', 'state_type',
                          'path', 'timestamp', 'root_state_storage_id', 'state_machine_version',
                          'used_rafcon_version', 'creation_time', 'last_update']:
                    execution_item[l] = item[l]
                start_item = execution_item
        return start_item, collapsed_next, collapsed_concurrent, collapsed_hierarchy, collapsed_items

    # build collapsed items
    for rid, gitems in grouped.items():
        if gitems[0]['item_type'] == 'StateMachineStartItem':
            item = gitems[0]
            execution_item = {}
            for l in ['description', 'path_by_name', 'state_name', 'run_id', 'state_type', \
                      'path', 'timestamp', 'root_state_storage_id', 'state_machine_version', \
                      'used_rafcon_version', 'creation_time', 'last_update']:
                execution_item[l] = item[l]

            start_item = execution_item

            collapsed_next[rid] = execution_history_items[next_[gitems[0]['history_item_id']]]['run_id']
            collapsed_items[rid] = execution_item
        elif gitems[0]['state_type'] == 'ExecutionState' or \
             gitems[0]['state_type'] == 'HierarchyState' or \
             gitems[0]['state_type'] == 'LibraryState' or \
             'Concurrency' in gitems[0]['state_type']:

            # for item in gitems:
            #     if item["description"] is not None:
            #         print item["item_type"], item["call_type"], item["state_type"], item["state_name"]
            #     print item["description"]

            # select call and return items for this state
            try:
                call_item = gitems[[gitems[i]['item_type'] == 'CallItem' and \
                                    gitems[i]['call_type'] == 'EXECUTE' \
                                    for i in range(len(gitems))].index(True)]
            except ValueError:
                # fall back to container call, should only happen for root state
                call_item = gitems[[gitems[i]['item_type'] == 'CallItem' and \
                                    gitems[i]['call_type'] == 'CONTAINER' \
                                    for i in range(len(gitems))].index(True)]


            try:
                return_item = gitems[[gitems[i]['item_type'] == 'ReturnItem' and \
                                      gitems[i]['call_type'] == 'EXECUTE' \
                                      for i in range(len(gitems))].index(True)]
            except ValueError:
                # fall back to container call, should only happen for root state
                return_item = gitems[[gitems[i]['item_type'] == 'ReturnItem' and \
                                      gitems[i]['call_type'] == 'CONTAINER' \
                                      for i in range(len(gitems))].index(True)]

            # next item (on same hierarchy level) is always after return item
            if return_item['history_item_id'] in next_:
                # no next relationship at the end of containers
                if execution_history_items[next_[return_item['history_item_id']]]['state_type'] == 'HierarchyState' and execution_history_items[next_[return_item['history_item_id']]]['item_type'] == 'ReturnItem' and execution_history_items[next_[return_item['history_item_id']]]['call_type'] == 'CONTAINER':
                    if full_next:
                        collapsed_next[rid] = execution_history_items[next_[return_item['history_item_id']]]['run_id']
                    else:
                        pass
                else:
                    collapsed_next[rid] = execution_history_items[next_[return_item['history_item_id']]]['run_id']

            # treat hierarchy level 
            if execution_history_items[previous[call_item['history_item_id']]]['state_type'] == 'HierarchyState' and execution_history_items[previous[call_item['history_item_id']]]['item_type'] == 'CallItem':
                prev_rid = execution_history_items[previous[call_item['history_item_id']]]['run_id']
                collapsed_hierarchy[prev_rid] = rid

            # treat concurrency level
            if execution_history_items[previous[call_item['history_item_id']]]['item_type'] == 'ConcurrencyItem':
                prev_rid = execution_history_items[previous[call_item['history_item_id']]]['run_id']
                if prev_rid in collapsed_concurrent:
                    collapsed_concurrent[prev_rid].append(rid)
                else:
                    collapsed_concurrent[prev_rid] = [rid]

            # assemble grouped item
            execution_item = {}
            for l in ['description', 'path_by_name', 'state_name', 'run_id', 'state_type', 'path']:
                execution_item[l] = call_item[l]
            for l in ['outcome_name', 'outcome_id']:
                execution_item[l] = return_item[l]
            for l in ['timestamp']:
                execution_item[l+'_call'] = call_item[l]
                execution_item[l+'_return'] = return_item[l]


            execution_item['data_ins'] = json.loads(call_item['input_output_data'])
            execution_item['data_outs'] = json.loads(return_item['input_output_data'])

            execution_item['scoped_data_ins'] = {}
            for k, v in json.loads(call_item['scoped_data']).items():
                if k.startswith('error'):
                    pass
                execution_item['scoped_data_ins'][v['name']] = v['value']
            execution_item['scoped_data_outs'] = {}
            for k, v in json.loads(return_item['scoped_data']).items():
                if k.startswith('error'):
                    pass
                execution_item['scoped_data_outs'][v['name']] = v['value']

            collapsed_items[rid] = execution_item

    return start_item, collapsed_next, collapsed_concurrent, collapsed_hierarchy, collapsed_items


def log_to_DataFrame(execution_history_items):
    """
    Returns all collapsed items in a table-like structure (pandas.DataFrame). The data flow is
    omitted from this table as the different states have different ports defined. The available
    data per execution item (row in the table) can be printed using pandas.DataFrame.columns.
    """
    start, next_, concurrenty, hierarchy, gitems = log_to_collapsed_structure(execution_history_items)
    gitems.pop(start['run_id'])
    if len(gitems) == 0:
        return pd.DataFrame()

    # remove columns which are not generic over all states (basically the
    # data flow stuff)
    df_keys = gitems.values()[0].keys()
    df_keys.remove('data_ins')
    df_keys.remove('data_outs')
    df_keys.remove('scoped_data_ins')
    df_keys.remove('scoped_data_outs')
    df_keys.sort()

    df_items = []
    for rid, item in gitems.items():
        df_items.append([item[k] for k in df_keys])

    df = pd.DataFrame(df_items, columns=df_keys)
    # convert epoch to datetime
    df.timestamp_call = pd.to_datetime(df.timestamp_call, unit='s')
    df.timestamp_return = pd.to_datetime(df.timestamp_return, unit='s')

    # use call timestamp as index
    df_timed = df.set_index(df.timestamp_call)
    df_timed.sort_index(inplace=True)

    return df_timed


def log_to_ganttplot(execution_history_items):
    """
    Example how to use the DataFrame representation
    """
    import matplotlib.pyplot as plt
    import matplotlib.dates as dates
    import numpy as np

    d = log_to_DataFrame(execution_history_items)

    # de-duplicate states and make mapping from state to idx
    unique_states, idx = np.unique(d.path_by_name, return_index=True)
    ordered_unique_states = np.array(d.path_by_name)[np.sort(idx)]
    name2idx = {k: i for i, k in enumerate(ordered_unique_states)}

    calldate = dates.date2num(d.timestamp_call.dt.to_pydatetime())
    returndate = dates.date2num(d.timestamp_return.dt.to_pydatetime())

    state2color = {'HierarchyState': 'k',
                   'ExecutionState': 'g',
                   'BarrierConcurrencyState': 'y',
                   'PreemptiveConcurrencyState': 'y'}

    fig, ax = plt.subplots(1,1)
    ax.barh(bottom=[name2idx[k] for k in d.path_by_name], width=returndate-calldate, left=calldate, align='center', color=[state2color[s] for s in d.state_type], lw=0.0)
    plt.yticks(range(len(ordered_unique_states)), ordered_unique_states)

