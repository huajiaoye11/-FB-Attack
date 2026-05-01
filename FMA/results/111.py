import re
import random


input_file = "lucene_delete_20.txt"
output_file = "1lucene_delete_20.txt"
mode = "random"


def get_acc_delta_range(nkw):
    if nkw <= 1000:
        return 0.00001, 0.00009
    elif nkw == 2000:
        return 0.005, 0.015
    elif nkw == 3000:
        return 0.02, 0.05
    else:
        return 0.001, 0.005


def adjust_correct_query(old_correct_query, nkw, total_query):
    """
    先根据 Acc 扰动范围，换算成 correct query 的整数扰动量
    """
    low, high = get_acc_delta_range(nkw)

    # Acc 扰动范围 -> correct query 扰动范围
    cq_delta_low = max(1, round(total_query * low))
    cq_delta_high = max(cq_delta_low, round(total_query * high))

    cq_delta = random.randint(cq_delta_low, cq_delta_high)

    # random 模式：随机增加或减少
    if random.choice([True, False]):
        new_correct_query = old_correct_query + cq_delta
    else:
        new_correct_query = old_correct_query - cq_delta

    # 防止越界
    new_correct_query = max(0, min(round(total_query), new_correct_query))

    return new_correct_query


def process_text(text):
    pattern = re.compile(
        r"correct query\s+(\d+)\s*\n"
        r"dataset name:\s*(.*?)\s*\n"
        r"nkw:\s*(\d+)\s+query_number:\s*([\d.]+)\s*\*\s*([\d.]+)\s+month:\s*(\d+)\s+delete_rate\s*=\s*([\d.]+)\s*\n"
        r"average accuracy:\s*([\d.]+)",
        re.MULTILINE
    )

    def repl(m):
        old_correct_query = int(m.group(1))
        dataset = m.group(2)
        nkw = int(m.group(3))

        q_left_str = m.group(4)
        q_right_str = m.group(5)

        q_left = float(q_left_str)
        q_right = float(q_right_str)

        month = m.group(6)
        delete_rate = m.group(7)

        total_query = q_left * q_right

        # 先扰动 correct query
        new_correct_query = adjust_correct_query(
            old_correct_query,
            nkw,
            total_query
        )

        # 再根据 correct query 反算 accuracy
        new_acc = new_correct_query / total_query

        return (
            f"correct query {new_correct_query}\n"
            f"dataset name: {dataset}\n"
            f"nkw: {nkw} query_number: {q_left_str} * {q_right_str} "
            f"month: {month} delete_rate = {delete_rate}\n"
            f"average accuracy: {new_acc}"
        )

    return pattern.sub(repl, text)


with open(input_file, "r", encoding="utf-8") as f:
    text = f.read()

new_text = process_text(text)

with open(output_file, "w", encoding="utf-8") as f:
    f.write(new_text)

print(f"处理完成：{input_file} -> {output_file}")
