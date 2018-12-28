# @Time    : 2018/12/23 14:08
# @Author  : Xu Huipeng
# @Blog    : https://brycexxx.github.io/

import numpy as np
from typing import Tuple
from sklearn.preprocessing import LabelBinarizer
import matplotlib.pyplot as plt
from matplotlib.patches import Circle

class SupportVectorClassifier:
    """
    线性支持向量机
    """
    def __init__(self, tol: float=1e-4, C: float=1.0, max_iter: int=1000):
        self.tol = tol
        self.C = C
        self.max_iter = max_iter

    def _gx(self, x: np.ndarray) -> float:
        gx = np.dot(np.dot(x, self.X.T), self.y * self.alpha)[0] + self.b
        return gx

    def _Ei(self, i: int) -> float:
        return self._gx(self.X[i]) - self.y[i]

    def _stop_condition(self) -> bool:
        cond1 = np.dot(self.y.T, self.alpha) == 0
        if not cond1:
            return False
        cond2 = (self.alpha >= 0).all() and (self.alpha <= self.C).all()
        if not cond2:
            return False
        for i in range(self.n_samples):
            gx = self.Ei[i] + self.y[i]
            ygx = gx * self.y[i]
            if self.alpha[i] == 0:
                if ygx < 1:
                    return False
            elif 0 < self.alpha[i] < self.C:
                if ygx != 1:
                    return False
            else:
                if ygx > 1:
                    return False
        return True

    def _inner_loop(self, idx1: int):
        self.Ei[idx1] = self._Ei(idx1)
        if abs(self.Ei[idx1]) > self.tol:
            alpha1 = self.alpha[idx1].copy()
            E1 = self.Ei[idx1]
            idx2 = self.Ei.argmin() if E1 >= 0 else self.Ei.argmax()
            E2 = self.Ei[idx2]
            alpha2 = self.alpha[idx2].copy()
            K_11 = np.dot(self.X[idx1, np.newaxis], self.X[idx1][:, np.newaxis])
            K_22 = np.dot(self.X[idx2, np.newaxis], self.X[idx2][:, np.newaxis])
            K_12 = np.dot(self.X[idx1, np.newaxis], self.X[idx2][:, np.newaxis])
            eta = K_11 + K_22 - 2 * K_12
            if eta <= 0: print('eta < 0'); return 0
            alpha2_new_unc = alpha2 + self.y[idx2] * (E1 - E2) / eta
            if self.y[idx1] == self.y[idx2]:
                L = max(.0, alpha2 + alpha1 - self.C)
                H = min(self.C, alpha2 + alpha1)
            else:
                L = max(.0, alpha2 - alpha1)
                H = min(self.C, self.C + alpha2 - alpha1)
            if L == H: print('L == H'); return 0
            # 更新后的 alpha2
            if alpha2_new_unc > H: alpha2_new = H
            elif alpha2_new_unc < L: alpha2_new = L
            else: alpha2_new = alpha2_new_unc
            if abs(alpha2_new - alpha2) < 1e-5: print('alpha2 moving not enough'); return 0
            # 更新后的 alpha1
            alpha1_new = alpha1 + self.y[idx1] * self.y[idx2] * (alpha2 - alpha2_new)
            # 更新 alpha1 alpha2
            self.alpha[[idx1, idx2]] = np.array([[alpha1_new, alpha2_new]]).T
            b1_new = - E1 - self.y[idx1] * K_11 * (alpha1_new - alpha1) - self.y[idx2] * \
                     K_12 * (alpha2_new - alpha2) + self.b
            b2_new = - E2 - self.y[idx1] * K_12 * (alpha1_new - alpha1) - self.y[idx2] * \
                     K_22 * (alpha2_new - alpha2) + self.b
            # 更新 self.b
            if 0 < alpha1_new < self.C: self.b = b1_new
            elif 0 < alpha2_new < self.C: self.b = b2_new
            else: self.b = (b1_new + b2_new) / 2.0
            # 更新 Ei
            for i in range(self.n_samples): self.Ei[i] = self._Ei(i)
            return 1
        else: return 0

    def fit(self, X: np.ndarray, y: np.ndarray):
        self.X, self.y = X, y
        self.b = .0
        lb = LabelBinarizer(neg_label=-1)
        self.y = lb.fit_transform(self.y)
        self.n_samples, self.n_features = self.X.shape
        self.alpha = np.zeros((self.n_samples, 1))
        self.Ei = np.zeros((self.n_samples, 1))
        iter_ = 0; entire_set = True; alpha_pairs_changed = 0
        while (iter_ < self.max_iter) and (entire_set or alpha_pairs_changed):
            alpha_pairs_changed = 0
            if not entire_set:
                non_boundis = np.nonzero((self.alpha > 0) * (self.alpha < self.C))[0]
                for i in non_boundis:
                    alpha_pairs_changed += self._inner_loop(i)
                iter_ += 1
            else:
                for i in range(self.n_samples):
                    alpha_pairs_changed += self._inner_loop(i)
                iter_ += 1
            if entire_set: entire_set = False
            elif alpha_pairs_changed == 0: entire_set = True
        return self

    def predict(self, X: np.ndarray):
        gx = np.array([self._gx(x) for x in X])
        ret = np.where(gx>=0, 1, 0)
        return ret.squeeze()

    def plot_2d_SVM(self):
        pos_idx = (self.y == 1).squeeze()
        neg_idx = (self.y == -1).squeeze()
        sv_idx = (self.alpha != 0).squeeze()

        w = np.dot(self.X.T, np.multiply(self.alpha, self.y))

        plt.figure()
        plt.scatter(self.X[pos_idx][:, 0], self.X[pos_idx][:, 1], c='red', label='pos')
        plt.scatter(self.X[neg_idx][:, 0], self.X[neg_idx][:, 1], c='green', label='neg')
        ax = plt.gca()
        for sv_x, sv_y in self.X[sv_idx]:
            circle = Circle((sv_x, sv_y), radius=0.5, facecolor='none', edgecolor=(0,0.8,0.8), linewidth=3, alpha=0.5)
            ax.add_artist(circle)
        x = np.arange(self.X[:, 0].min(), self.X[:, 0].max(), 0.1)
        y = - (w[0] * x + self.b) / w[1]
        plt.plot(x, y.squeeze(), label='separate hyperplane')
        plt.xlim(-2, 12)
        plt.ylim(-8, 6)
        plt.legend(frameon=False)
        plt.show()

if __name__ == "__main__":
    from sklearn.datasets import load_breast_cancer
    from sklearn.svm import LinearSVC
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import accuracy_score
    from sklearn.dummy import DummyClassifier

    bc = load_breast_cancer()
    X = bc.data
    y = bc.target
    train_X, test_X, train_y, test_y = train_test_split(X, y, random_state=0)
    svc = SupportVectorClassifier(max_iter=1000, tol=1e-5)
    svc.fit(train_X, train_y)
    y_pred = svc.predict(test_X)
    print(y_pred.sum())
    print(accuracy_score(test_y, y_pred))
    print('-'*20)
    sk_svc = LinearSVC(max_iter=2000, random_state=42).fit(train_X, train_y)
    print(sk_svc.score(test_X, test_y))
    # def loadDataSet(fileName):
    #     """
    #     加载数据集
    #     :param fileName:
    #     :return:
    #     """
    #     dataMat = []
    #     labelMat = []
    #     fr = open(fileName)
    #     for line in fr.readlines():
    #         lineArr = line.strip().split('\t')
    #         dataMat.append([float(lineArr[0]), float(lineArr[1])])
    #         labelMat.append(float(lineArr[2]))
    #     return dataMat, labelMat
    # x, y = loadDataSet(r'..\ttest\svc_data.txt')
    # svc = SupportVectorClassifier()
    # svc.fit(np.array(x), np.array(y))
    # print(svc.alpha)
    # svc.plot_2d_SVM()
    





