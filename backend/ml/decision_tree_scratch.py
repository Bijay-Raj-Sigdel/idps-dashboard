import numpy as np


class Node:
    """Represents a single node in the binary decision tree."""

    def __init__(
        self,
        feature_index=None,
        threshold=None,
        left=None,
        right=None,
        value=None,
    ):
        self.feature_index = feature_index  # Index of feature to split on
        self.threshold = threshold  # Threshold value for split
        self.left = left  # Left child subtree (feature <= threshold)
        self.right = right  # Right child subtree (feature > threshold)
        self.value = value  # Majority class label (populated on leaf nodes)


def calculate_gini(y: np.ndarray) -> float:
    """Computes Gini Impurity for a label array y."""
    if len(y) == 0:
        return 0.0
    _, counts = np.unique(y, return_counts=True)
    probabilities = counts / len(y)
    return float(1.0 - np.sum(probabilities**2))


def find_best_split(
    X: np.ndarray, y: np.ndarray, num_percentiles: int = 10
) -> tuple:
    """Finds the best feature and threshold split using weighted Gini impurity with percentile binning."""
    best_gini = float("inf")
    best_feature, best_threshold = None, None
    num_features = X.shape[1]

    for feature_idx in range(num_features):
        feature_values = X[:, feature_idx]

        # Use percentiles to prevent performance degradation on continuous features
        thresholds = np.percentile(
            feature_values, np.linspace(5, 95, num_percentiles)
        )
        thresholds = np.unique(thresholds)

        for threshold in thresholds:
            left_mask = feature_values <= threshold
            right_mask = ~left_mask

            if not np.any(left_mask) or not np.any(right_mask):
                continue

            left_gini = calculate_gini(y[left_mask])
            right_gini = calculate_gini(y[right_mask])

            weighted_gini = (
                left_mask.sum() * left_gini + right_mask.sum() * right_gini
            ) / len(y)

            if weighted_gini < best_gini:
                best_gini = weighted_gini
                best_feature = feature_idx
                best_threshold = threshold

    return best_feature, best_threshold, best_gini


def build_tree(
    X: np.ndarray,
    y: np.ndarray,
    depth: int = 0,
    max_depth: int = 8,
    min_samples_split: int = 10,
) -> Node:
    """Recursively builds the decision tree using greedy splits."""
    labels, counts = np.unique(y, return_counts=True)

    # Base Cases: Pure node, reached max depth, or insufficient samples
    if (
        depth >= max_depth
        or len(y) < min_samples_split
        or len(labels) == 1
    ):
        majority_class = labels[counts.argmax()]
        return Node(value=majority_class)

    feature_idx, threshold, split_gini = find_best_split(X, y)

    # Return leaf if no valid split reduces impurity
    if feature_idx is None:
        majority_class = labels[counts.argmax()]
        return Node(value=majority_class)

    left_mask = X[:, feature_idx] <= threshold
    right_mask = ~left_mask

    left_child = build_tree(
        X[left_mask], y[left_mask], depth + 1, max_depth, min_samples_split
    )
    right_child = build_tree(
        X[right_mask], y[right_mask], depth + 1, max_depth, min_samples_split
    )

    return Node(
        feature_index=feature_idx,
        threshold=threshold,
        left=left_child,
        right=right_child,
    )


class DecisionTreeScratch:
    """Custom Scikit-Learn compatible Decision Tree Classifier."""

    def __init__(self, max_depth: int = 8, min_samples_split: int = 10):
        self.max_depth = max_depth
        self.min_samples_split = min_samples_split
        self.root = None

    def fit(self, X: np.ndarray, y: np.ndarray):
        """Fits the decision tree to training data."""
        self.root = build_tree(
            X,
            y,
            max_depth=self.max_depth,
            min_samples_split=self.min_samples_split,
        )
        return self

    def _predict_single(self, node: Node, x: np.ndarray):
        if node.value is not None:
            return node.value
        if x[node.feature_index] <= node.threshold:
            return self._predict_single(node.left, x)
        return self._predict_single(node.right, x)

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predicts class labels for samples in X."""
        return np.array([self._predict_single(self.root, row) for row in X])