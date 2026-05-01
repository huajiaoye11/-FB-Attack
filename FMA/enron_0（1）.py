import os
import pickle
import time
import multiprocessing
from concurrent.futures import ProcessPoolExecutor
from collections import Counter

import numpy as np

from process_dict import get_size_frompkl, delete_get_size_frompkl

np.set_printoptions(suppress=True)


def _load_month_data(args):
    dataset_name, year, month, nkw, delete_rate = args
    return (year, month), {
        'all': get_size_frompkl(dataset_name, year, month, nkw),
        'delete': delete_get_size_frompkl(dataset_name, year, month, nkw, delete_rate)
    }


def _make_hashable_size(size_value):
    if isinstance(size_value, list):
        return tuple(size_value)
    return size_value


def _make_hashable_size_sequence(size_sequence):
    return tuple(_make_hashable_size(item) for item in size_sequence)


def load_sent_mail_contents(dataset_name, year=1999, month=1):
    pro_dataset_path = "../datasets/" + str(dataset_name) + str(year) + "_" + str(month) + ".pkl"
    if not os.path.exists(pro_dataset_path):
        raise ValueError("The file {} does not exist".format(pro_dataset_path))

    with open(pro_dataset_path, "rb") as f:
        dataset, res_dataset_length = pickle.load(f)

    return dataset, res_dataset_length


def load_stem_trends(dataset_name, nkw):
    pro_dataset_path = "datasets/trends/" + str(dataset_name) + "_trends_" + str(nkw) + ".pkl"
    if not os.path.exists(pro_dataset_path):
        raise ValueError("The file {} does not exist".format(pro_dataset_path))

    with open(pro_dataset_path, "rb") as f:
        stem, stem_trends = pickle.load(f)

    return stem, stem_trends


def run_single_experiment(exp_params):
    def _generate_train_test_data(dataset_name, n_keywords):
        chosen_keywords, trend_matrix = load_stem_trends(dataset_name, n_keywords)
        trend_matrix_norm = trend_matrix.copy()

        for i_col in range(trend_matrix_norm.shape[1]):
            if sum(trend_matrix_norm[:, i_col]) == 0:
                trend_matrix_norm[:, i_col] = 1 / n_keywords
            else:
                trend_matrix_norm[:, i_col] = (
                    trend_matrix_norm[:, i_col] / sum(trend_matrix_norm[:, i_col])
                )

        return trend_matrix_norm, chosen_keywords

    trend_real_norm, chosen_keywords = _generate_train_test_data(
        exp_params['dataset'],
        exp_params['nkw']
    )

    return trend_real_norm


def static_enron_data_info(dataset_name, nkw, trend_norm, n_month, query_number, delete_rate):
    chosen_keywords, _ = load_stem_trends(dataset_name, nkw)
    statistic_trend_number = query_number * trend_norm

    candidate_class = []
    candidate = []
    candidate_class_count = []

    month_args = []
    year = 2000
    month = 1

    for i in range(n_month):
        if i == 12:
            month = 1
            year += 1

        month_args.append((dataset_name, year, month, nkw, delete_rate))
        month += 1

    if n_month > 1 and multiprocessing.cpu_count() > 1:
        max_workers = min(multiprocessing.cpu_count(), n_month)
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            preloaded_data = dict(executor.map(_load_month_data, month_args))
    else:
        preloaded_data = {}
        for args in month_args:
            key, value = _load_month_data(args)
            preloaded_data[key] = value

    keyword_history = {keyword: [] for keyword in chosen_keywords}

    for i in range(n_month):
        prev_year = 2000 + (i // 12)
        prev_month = 1 + (i % 12)
        delete_data = preloaded_data[(prev_year, prev_month)]['delete']

        for keyword in chosen_keywords:
            keyword_history[keyword].append(delete_data.get(keyword, []))

    word_to_id = {}
    id_to_word = {}

    for index, keyword in enumerate(chosen_keywords):
        word_to_id[keyword] = index
        id_to_word[index] = keyword

    for month_count in range(n_month):
        temp_class = {}
        temp_class_count = {}
        temp_candidate = {}

        current_year = 2000 + (month_count // 12)
        current_month = 1 + (month_count % 12)
        current_data = preloaded_data[(current_year, current_month)]['all']

        query_keyword = np.floor(query_number * trend_norm[:, month_count]).astype(int)
        query_keyword_list = np.repeat(np.arange(nkw), query_keyword).tolist()
        trend_target = statistic_trend_number[:, month_count].astype(int)

        if month_count == 0:
            size_to_class = {}

            for q_id in query_keyword_list:
                keyword_value = current_data[id_to_word[q_id]]
                size_key = _make_hashable_size(keyword_value)

                if size_key in size_to_class:
                    temp_class_count[size_to_class[size_key]] += 1
                else:
                    temp_class[q_id] = [keyword_value]
                    temp_class_count[q_id] = 1
                    size_to_class[size_key] = q_id

            for k2, v2 in temp_class.items():
                cand_np = np.abs(temp_class_count[k2] - trend_target)
                cand_index = np.where(cand_np == cand_np.min())
                temp_candidate[k2] = set(cand_index[0].tolist())

            candidate_class.append(temp_class)
            candidate.append(temp_candidate)
            candidate_class_count.append(temp_class_count)

        else:
            now_month_size = current_data
            size_to_class = {}

            for q_id in query_keyword_list:
                keyword = id_to_word[q_id]
                keyword_sizes = keyword_history[keyword][:month_count]

                if keyword in now_month_size:
                    keyword_sizes = keyword_sizes + [now_month_size[keyword]]
                else:
                    keyword_sizes = keyword_sizes + [[]]

                size_key = _make_hashable_size_sequence(keyword_sizes)

                if size_key in size_to_class:
                    temp_class_count[size_to_class[size_key]] += 1
                else:
                    temp_class[q_id] = keyword_sizes
                    temp_class_count[q_id] = 1
                    size_to_class[size_key] = q_id

            for k2, v2 in temp_class.items():
                cand_np = np.abs(temp_class_count[k2] - trend_target)
                cand_index = np.where(cand_np == cand_np.min())
                temp_candidate[k2] = set(cand_index[0].tolist())

            candidate_class.append(temp_class)
            candidate.append(temp_candidate)
            candidate_class_count.append(temp_class_count)

    counter_size = []

    for i in range(n_month):
        temp_size = {}

        for k1, v1 in candidate_class[i].items():
            temp_size[k1] = []

            for v2 in v1:
                temp_size[k1].append(Counter(v2))

        counter_size.append(temp_size)

    new_candidate_size = {}
    new_candidate = {}
    new_candidate_count = {}
    ttc = {}

    for k1, v1 in counter_size[0].items():
        new_candidate_size[k1] = v1
        new_candidate[k1] = set(candidate[0][k1])
        new_candidate_count[k1] = candidate_class_count[0][k1]
        ttc[k1] = []
        ttc[k1].append((k1, candidate_class_count[0][k1]))

    for i in range(1, n_month):
        current_candidate = candidate[i]
        current_count = candidate_class_count[i]

        for k1, v1 in counter_size[i].items():
            if len(v1) == 0:
                continue

            delete_size = v1[-1]
            in_flag = 0
            max_key = 0
            max_sim_value = 0

            for k2, v2 in new_candidate_size.items():
                if len(v2) == 0:
                    continue

                all_size = v2[-1]
                inter_size = len(all_size & delete_size)
                union_size = len(all_size | delete_size)

                if union_size == 0 or inter_size / union_size > 0.6:
                    in_flag = 1
                    max_sim = 0 if union_size == 0 else inter_size / union_size

                    if max_sim > max_sim_value:
                        max_sim_value = max_sim
                        max_key = k2

            if in_flag == 1:
                new_candidate[max_key] = current_candidate[k1].intersection(
                    new_candidate[max_key]
                )
                new_candidate_size[max_key] = v1
                new_candidate_count[max_key] += current_count[k1]
                ttc[max_key].append((k1, current_count[k1]))

            else:
                if k1 not in new_candidate_size:
                    new_candidate_size[k1] = v1
                    new_candidate[k1] = current_candidate[k1]
                    new_candidate_count[k1] = current_count[k1]
                    ttc[k1] = []
                else:
                    new_key = k1 + 3000
                    new_candidate_size[new_key] = v1
                    new_candidate[new_key] = current_candidate[k1]
                    new_candidate_count[new_key] = current_count[k1]
                    ttc[new_key] = []

    ex_value = 0

    for k3, v3 in new_candidate.items():
        if len(v3) == 1 and list(v3)[0] == k3:
            for kv4 in ttc[k3]:
                if kv4[0] == k3:
                    ex_value += kv4[1]

    return ex_value


if __name__ == "__main__":
    multiprocessing.freeze_support()

    total_start = time.time()

    nkw_list = [500, 1000, 2000, 3000]
    query_list = [5000, 10000, 15000, 20000]
    query_month = [6, 12, 18, 24]
    delete_rate = 0.00

    for nkw in nkw_list:
        for query_number in query_list:
            for n_month in query_month:
                iter_start = time.time()

                parameter_dict = {
                    'dataset': 'enron-full',
                    'nkw': nkw,
                    'query_number_dist': 'poiss',
                    'query_params': 24 * query_number / n_month,
                    'n_month': n_month
                }

                trend_norm = run_single_experiment(parameter_dict)

                ans = static_enron_data_info(
                    'enron-full',
                    nkw,
                    trend_norm,
                    n_month,
                    query_number,
                    delete_rate=delete_rate
                )

                iter_time = time.time() - iter_start

                print("correct query", ans)
                print("dataset name: enron")
                print(
                    "nkw:", nkw,
                    "query_number:", n_month, "*", 24 * query_number / n_month,
                    "month:", n_month,
                    "delete_rate = 0.00"
                )
                print("average accuracy: ", ans * 1.0 / (24 * query_number))
                print(f"running time: {iter_time:.2f} s")

    total_time = time.time() - total_start
    print(f"total running time: {total_time:.2f} s")
