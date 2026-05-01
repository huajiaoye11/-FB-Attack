import os
import glob
import email
import json
import math
from collections import Counter, defaultdict

import pandas as pd
import tqdm


def split_df(dframe, frac=0.5):
    first_split = dframe.sample(frac=frac)
    second_split = dframe.drop(first_split.index)
    return first_split, second_split


def get_body_from_enron_email(mail):
    msg = email.message_from_string(mail)
    parts = []

    for part in msg.walk():
        if part.get_content_type() == "text/plain":
            payload = part.get_payload(decode=True)

            if payload is None:
                payload = part.get_payload()
                if isinstance(payload, str):
                    parts.append(payload)
            else:
                charset = part.get_content_charset() or "utf-8"
                parts.append(payload.decode(charset, errors="ignore"))

    return "".join(parts)


def extract_sent_mail_contents(maildir_directory="../maildir/") -> pd.DataFrame:
    import utils

    path = os.path.expanduser(maildir_directory)
    mails = glob.glob(f"{path}/*/_sent_mail/*")

    mail_contents = []
    mail_lengths = []

    for mailfile_path in tqdm.tqdm(mails, desc="Reading the emails"):
        with open(mailfile_path, "r", encoding="utf-8", errors="ignore") as mailfile:
            raw_mail = mailfile.read()
            mail_contents.append(get_body_from_enron_email(raw_mail))

        mail_lengths.append(utils.getFileSize(mailfile_path))

    return pd.DataFrame(
        {
            "filename": mails,
            "mail_body": mail_contents,
            "mail_length": mail_lengths,
        }
    )


class KeywordExtractor:
    def __init__(self, corpus_df, file_name, min_freq=1):
        _, glob_freq_dict = KeywordExtractor.extract_email_voc(corpus_df)

        with open(file_name, "w", encoding="utf-8") as f:
            json.dump(glob_freq_dict, f, ensure_ascii=False)

    @staticmethod
    def get_voc_from_one_email(email_text, freq=False):
        import nltk
        from nltk.corpus import stopwords
        from nltk.stem.porter import PorterStemmer
        from nltk.tokenize import sent_tokenize, word_tokenize

        stopwords_list = stopwords.words("english")
        stopwords_list.extend(["subject", "cc", "from", "to", "forward"])

        stemmer = PorterStemmer()

        stemmed_word_list = [
            stemmer.stem(word.lower())
            for sentence in sent_tokenize(email_text)
            for word in word_tokenize(sentence)
            if word.lower() not in stopwords_list and word.isalnum()
        ]

        if freq:
            return nltk.FreqDist(stemmed_word_list)

        return stemmed_word_list

    @staticmethod
    def extract_email_voc(dframe, one_occ_per_doc=True):
        freq_dict = {}
        glob_freq_list = {}

        for row_tuple in tqdm.tqdm(dframe.itertuples(), total=len(dframe)):
            temp_freq_dist = KeywordExtractor.get_voc_from_one_email(
                row_tuple.mail_body,
                freq=True,
            )

            freq_dict[row_tuple.filename] = []

            for word, freq in temp_freq_dist.items():
                freq_to_add = 1 if one_occ_per_doc else freq
                freq_dict[row_tuple.filename].append(word)

                if word not in glob_freq_list:
                    glob_freq_list[word] = {
                        "size": 0,
                        "length": [],
                    }

                glob_freq_list[word]["size"] += freq_to_add
                glob_freq_list[word]["length"].append(row_tuple.mail_length)

        return freq_dict, glob_freq_list

    @staticmethod
    def consist(a, b):
        a = dict(Counter(a))
        b = dict(Counter(b))

        for key1, val1 in a.items():
            if key1 in b and val1 <= b[key1]:
                continue
            return False

        return True


def load_top_keywords(filename, word_size):
    with open(filename, "r", encoding="utf-8") as f:
        data = json.load(f)

    sorted_data = sorted(
        data.items(),
        key=lambda x: x[1]["size"],
        reverse=True,
    )

    keywords = []

    for word, value in sorted_data[:word_size]:
        length_list = value["length"]
        length_counter = Counter(length_list)

        keywords.append(
            {
                "word": word,
                "size": value["size"],
                "length_count": len(length_list),
                "length_counter": length_counter,
            }
        )

    return keywords


def build_partial_index(partial_keywords):
    inverted_index = defaultdict(list)

    for idx, item in enumerate(partial_keywords):
        for length_value, count in item["length_counter"].items():
            inverted_index[length_value].append((idx, count))

    return inverted_index


def count_unique_matches(ed_keyword, partial_keywords, partial_index, frac1, frac2):
    ed_length = ed_keyword["length_count"]

    if ed_length == 0:
        return 0

    threshold = frac1 + frac2 - 1
    overlaps = defaultdict(int)

    for length_value, ed_count in ed_keyword["length_counter"].items():
        if length_value not in partial_index:
            continue

        for partial_idx, partial_count in partial_index[length_value]:
            overlaps[partial_idx] += min(ed_count, partial_count)

    count_in = 0

    for partial_idx, overlap in overlaps.items():
        partial_length = partial_keywords[partial_idx]["length_count"]

        if partial_length == 0:
            continue

        max_possible = min(ed_length, partial_length)
        if max_possible / math.sqrt(ed_length * partial_length) < threshold:
            continue

        res_percent = overlap / math.sqrt(ed_length * partial_length)

        if res_percent >= threshold:
            count_in += 1

            if count_in > 1:
                return 0

    return 1 if count_in == 1 else 0


def test_data_top(edb_filename, partial_filename, frac1, frac2, word_size=500):
    edb_keywords = load_top_keywords(edb_filename, word_size)
    partial_keywords = load_top_keywords(partial_filename, word_size)
    partial_index = build_partial_index(partial_keywords)

    count_uni = 0

    for ed_keyword in tqdm.tqdm(edb_keywords, total=len(edb_keywords)):
        count_uni += count_unique_matches(
            ed_keyword=ed_keyword,
            partial_keywords=partial_keywords,
            partial_index=partial_index,
            frac1=frac1,
            frac2=frac2,
        )

    print(frac1, frac2, "containing unique result", count_uni)


def main():
    frac1_list = [0.9, 0.8, 0.7, 0.6, 0.5]
    frac2_list = [0.9, 0.8, 0.7]

    for i in frac1_list:
        for j in frac2_list:
            filename1 = "./PVIA_Enron/edb/" + str(i) + ".json"
            filename2 = "./PVIA_Enron/partial/" + str(j) + ".json"

            test_data_top(filename1, filename2, i, j, word_size=5000)


if __name__ == "__main__":
    main()
