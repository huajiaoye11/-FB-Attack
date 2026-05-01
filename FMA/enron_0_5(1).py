import os
import pickle
import numpy as np

from process_dict import get_size_frompkl, delete_get_size_frompkl

np.set_printoptions(suppress=True)


def load_sent_mail_contents(dataset_name, year=1999, month=1):
    pro_dataset_path = "./datasets/" + str(dataset_name) + str(year) + "_" + str(month) + ".pkl"
    if not os.path.exists(pro_dataset_path):
        raise ValueError("The file {} does not exist".format(pro_dataset_path))

    with open(pro_dataset_path, "rb") as f:
        dataset, res_dataset_length = pickle.load(f)

    return dataset, res_dataset_length


def load_stem_trends(dataset_name, nkw):
    pro_dataset_path = "./datasets/trends/" + str(dataset_name) + "_trends_" + str(nkw) + ".pkl"
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
            col_sum = np.sum(trend_matrix_norm[:, i_col])

            if col_sum == 0:
                print("The {}th column of the trend matrix adds up to zero, making it uniform!".format(i_col))
                trend_matrix_norm[:, i_col] = 1 / n_keywords
            else:
                trend_matrix_norm[:, i_col] = trend_matrix_norm[:, i_col] / col_sum

        return trend_matrix_norm, chosen_keywords

    trend_real_norm, chosen_keywords = _generate_train_test_data(
        exp_params["dataset"],
        exp_params["nkw"]
    )

    return trend_real_norm


def static_enron_data_info(dataset_name, nkw, trend_norm, n_month, query_number, delete_rate):
    chosen_keywords, _ = load_stem_trends(dataset_name, nkw)

    statistic_trend_number = query_number * trend_norm

    year = 2000
    month = 1

    candidate_class = []
    candidate = []
    candidate_class_count = []

    all_keyword_size = []
    delete_keyword_size = []

    for i in range(n_month):
        if i == 12:
            month = 1
            year += 1

        temp_all_size = get_size_frompkl(dataset_name, year, month, nkw)
        temp_del_size = delete_get_size_frompkl(dataset_name, year, month, nkw, delete_rate)

        for key in chosen_keywords:
            if key not in temp_all_size:
                temp_all_size[key] = []
            if key not in temp_del_size:
                temp_del_size[key] = []

        all_keyword_size.append(temp_all_size)
        delete_keyword_size.append(temp_del_size)

        month += 1

    word_to_id = {}
    id_to_word = {}

    for index, keyword in enumerate(chosen_keywords):
        word_to_id[keyword] = index
        id_to_word[index] = keyword

    for month_count in range(n_month):
        temp_class = {}
        temp_class_count = {}
        temp_candidate = {}

        query_keyword = np.floor(query_number * trend_norm[:, month_count]).astype(int)

        query_keyword_list = []
        for i in range(nkw):
            query_keyword_list.extend([i for _ in range(query_keyword[i])])

        if month_count == 0:
            for q_id in query_keyword_list:
                in_flag = 0
                current_size = all_keyword_size[month_count][id_to_word[q_id]]

                for k1, size1 in temp_class.items():
                    if current_size == size1[0]:
                        in_flag = 1
                        temp_class_count[k1] += 1
                        break

                if in_flag == 0:
                    temp_class[q_id] = [current_size]
                    temp_class_count[q_id] = 1

            for k2 in temp_class.keys():
                cand_np = np.abs(
                    temp_class_count[k2] -
                    statistic_trend_number[:, month_count].astype(int)
                )
                cand_index = np.where(cand_np == cand_np.min())
                temp_candidate[k2] = set(cand_index[0].tolist())

        else:
            now_month_size = delete_keyword_size[month_count]

            keyword_size = {}
            for keyword in chosen_keywords:
                keyword_size[keyword] = []

                for i_m in range(month_count):
                    if keyword in delete_keyword_size[i_m]:
                        keyword_size[keyword].append(delete_keyword_size[i_m][keyword])
                    else:
                        keyword_size[keyword].append([])

                if keyword in now_month_size:
                    keyword_size[keyword].append(now_month_size[keyword])
                else:
                    keyword_size[keyword].append([])

            for q_id in query_keyword_list:
                in_flag = 0
                current_size = keyword_size[id_to_word[q_id]]

                for k1, size1 in temp_class.items():
                    if current_size == size1:
                        in_flag = 1
                        temp_class_count[k1] += 1
                        break

                if in_flag == 0:
                    temp_class[q_id] = current_size
                    temp_class_count[q_id] = 1

            for k2 in temp_class.keys():
                cand_np = np.abs(
                    temp_class_count[k2] -
                    statistic_trend_number[:, month_count].astype(int)
                )
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
                temp_size[k1].append(set(v2))

        counter_size.append(temp_size)

    unique_keyword = set()

    for i in range(n_month):
        for k1, v1 in candidate[i].items():
            if len(v1) == 1:
                unique_keyword.add(k1)

    new_candidate_size = {}
    new_candidate = {}
    new_candidate_count = {}
    ttc = {}

    for k1, v1 in counter_size[0].items():
        new_candidate_size[k1] = v1
        new_candidate[k1] = set(candidate[0][k1])
        new_candidate_count[k1] = candidate_class_count[0][k1]
        ttc[k1] = [(k1, candidate_class_count[0][k1])]

    for i in range(1, n_month):
        for k1, v1 in counter_size[i].items():
            in_flag = 0
            max_key = 0
            max_sim_value = 0

            for k2, v2 in new_candidate_size.items():
                v2_len = len(v2)

                if v2_len == 0:
                    continue

                delete_size = v1[v2_len - 1]
                all_size = v2[v2_len - 1]

                inter_size = len(all_size & delete_size)
                union_size = len(all_size) + len(delete_size) - inter_size

                if union_size == 0:
                    sim = 0
                else:
                    sim = inter_size / union_size

                if union_size == 0 or sim > 0.5:
                    in_flag = 1

                    if max_sim_value <= sim:
                        max_sim_value = sim
                        max_key = k2

            if in_flag == 1:
                new_candidate[max_key] = candidate[i][k1].intersection(new_candidate[max_key])
                new_candidate_size[max_key] = v1
                new_candidate_count[max_key] += candidate_class_count[i][k1]
                ttc[max_key].append((k1, candidate_class_count[i][k1]))

            else:
                if k1 not in new_candidate_size:
                    new_candidate_size[k1] = v1
                    new_candidate[k1] = candidate[i][k1]
                    new_candidate_count[k1] = candidate_class_count[i][k1]
                    ttc[k1] = []
                else:
                    print("k1", i, k1, max_sim_value, in_flag)

                    new_key = k1 + 3000
                    new_candidate_size[new_key] = v1
                    new_candidate[new_key] = candidate[i][k1]
                    new_candidate_count[new_key] = candidate_class_count[i][k1]
                    ttc[new_key] = []

    ex_value = 0

    for k3, v3 in new_candidate.items():
        if len(v3) == 1 and list(v3)[0] == k3:
            for kv4 in ttc[k3]:
                if kv4[0] == k3:
                    ex_value += kv4[1]

    print("correct query", ex_value)

    return ex_value


if __name__ == "__main__":
    repeat_cnt = 1

    nkw_list = [500, 1000, 2000, 3000]
    query_list = [5000, 10000, 15000, 20000]
    query_month = [6, 12, 18, 24]
    delete_list = [0, 0.05, 0.1, 0.15, 0.2]

    for nkw in nkw_list:
        for query_number in query_list:
            for n_month in query_month:
                parameter_dict = {
                    "dataset": "enron-full",
                    "nkw": nkw,
                    "query_number_dist": "poiss",
                    "query_params": 24 * query_number / n_month,
                    "n_month": n_month
                }

                trend_norm = run_single_experiment(parameter_dict)

                ans = static_enron_data_info(
                    "enron-full",
                    nkw,
                    trend_norm,
                    n_month,
                    query_number,
                    delete_rate=0.05
                )

                print("dataset name: enron")
                print(
                    "nkw:", nkw,
                    "query_number:", n_month, "*", 24 * query_number / n_month,
                    "month:", n_month,
                    "delete_rate = 0.05"
                )
                print("average accuracy: ", ans * 1.0 / (24 * query_number))
