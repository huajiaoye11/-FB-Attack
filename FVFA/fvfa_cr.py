import numpy as np


class FVFA_CR_Attack:
    """
    FVFA-CR:
    Frequency-Volume Fusion Attack with Conflict Resolution
    频率-体积融合攻击 + 冲突裁决机制
    """

    def __init__(self, alpha=0.5, conflict_threshold=0.03):
        self.alpha = alpha
        self.conflict_threshold = conflict_threshold

    @staticmethod
    def softmax(score_dict):
        keys = list(score_dict.keys())
        values = np.array([score_dict[k] for k in keys], dtype=float)

        values = values - np.max(values)
        exp_values = np.exp(values)
        probs = exp_values / np.sum(exp_values)

        return {
            k: float(p)
            for k, p in zip(keys, probs)
        }

    @staticmethod
    def freq_score(q_freq, w_freq):
        """
        频率越接近，分数越高
        """
        return -abs(q_freq - w_freq)

    @staticmethod
    def volume_score(q_volume, w_volume):
        """
        体积越接近，分数越高
        """
        return -abs(q_volume - w_volume)

    def predict_one(
        self,
        q,
        query_freq,
        query_volume,
        keyword_freq,
        keyword_volume
    ):
        freq_scores = {}
        volume_scores = {}

        for w in keyword_freq.keys():
            freq_scores[w] = self.freq_score(
                query_freq[q],
                keyword_freq[w]
            )

            volume_scores[w] = self.volume_score(
                query_volume[q],
                keyword_volume[w]
            )

        prob_freq = self.softmax(freq_scores)
        prob_volume = self.softmax(volume_scores)

        final_scores = {}

        for w in keyword_freq.keys():
            final_scores[w] = (
                self.alpha * prob_freq[w]
                + (1 - self.alpha) * prob_volume[w]
            )

        pred = self.conflict_resolution(
            prob_freq,
            prob_volume,
            final_scores
        )

        return pred, final_scores

    def conflict_resolution(
        self,
        prob_freq,
        prob_volume,
        final_scores
    ):
        """
        冲突裁决：
        1. 若 FMA 和 VIA 预测一致，直接输出；
        2. 若不一致，优先看融合分数；
        3. 若融合分数差距很小，则选择单项置信度更高的一方。
        """

        fma_pred = max(prob_freq, key=prob_freq.get)
        via_pred = max(prob_volume, key=prob_volume.get)

        if fma_pred == via_pred:
            return fma_pred

        ranked = sorted(
            final_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )

        best_w, best_score = ranked[0]
        second_w, second_score = ranked[1]

        if best_score - second_score >= self.conflict_threshold:
            return best_w

        if prob_freq[fma_pred] >= prob_volume[via_pred]:
            return fma_pred

        return via_pred

    def predict_all(
        self,
        query_freq,
        query_volume,
        keyword_freq,
        keyword_volume
    ):
        pred_map = {}
        score_map = {}

        for q in query_freq.keys():
            pred, scores = self.predict_one(
                q,
                query_freq,
                query_volume,
                keyword_freq,
                keyword_volume
            )

            pred_map[q] = pred
            score_map[q] = scores

        return pred_map, score_map

    @staticmethod
    def accuracy(true_map, pred_map):
        correct = 0
        total = 0

        for q, true_w in true_map.items():
            if q not in pred_map:
                continue

            total += 1

            if pred_map[q] == true_w:
                correct += 1

        if total == 0:
            return 0.0

        return correct / total

    @staticmethod
    def top_k_accuracy(true_map, score_map, k=5):
        correct = 0
        total = 0

        for q, true_w in true_map.items():
            if q not in score_map:
                continue

            total += 1

            ranked = sorted(
                score_map[q].items(),
                key=lambda x: x[1],
                reverse=True
            )

            top_k = [
                item[0]
                for item in ranked[:k]
            ]

            if true_w in top_k:
                correct += 1

        if total == 0:
            return 0.0

        return correct / total
