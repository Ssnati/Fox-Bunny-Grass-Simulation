import math
import statistics as st
from scipy.stats import chi2

class ChiSquare:
    """
    Clase para realizar la prueba de Chi-Cuadrado sobre una lista de números.
    """
    def __init__(self, number_list):
        self.number_list = number_list
        self.intervals_number = int(math.sqrt(len(number_list)))
        self.min_value = min(number_list)
        self.max_value = max(number_list)
        self.range_value = (self.max_value - self.min_value) / \
                           self.intervals_number
        self.intervals = {}
        self.squ_chi = 0
        self.squ_chi_critic = chi2.ppf(0.95, self.intervals_number - 1)

    def create_intervals(self):
        """Crea los intervalos de frecuencia esperada para la prueba."""
        expected_freq = len(self.number_list) / self.intervals_number
        for i in range(self.intervals_number):
            min_value = self.min_value + i * self.range_value if i > 0 else self.min_value
            max_value = min_value + self.range_value
            self.intervals[(min_value, max_value)] = {
                "freq_o": 0, "freq_e": expected_freq, "square_chi": 0}

    def calculate_frequence(self):
        """Calcula la frecuencia observada en cada intervalo."""
        for number in self.number_list:
            for (min_val, max_val) in self.intervals:
                if min_val <= number < max_val or (max_val == self.max_value and number == max_val):
                    self.intervals[(min_val, max_val)]["freq_o"] += 1
                    break

    def calculate_squ_chi(self):
        """Calcula el estadístico Chi-Cuadrado."""
        for freqs in self.intervals.values():
            freqs["square_chi"] = pow(
                freqs["freq_o"] - freqs["freq_e"], 2) / freqs["freq_e"]
            self.squ_chi += freqs["square_chi"]

class KS:
    """
    Clase para realizar la prueba de Kolmogorov-Smirnov sobre una lista de números.
    """
    def __init__(self, number_list):
        self.number_list = number_list
        self.intervals_number = int(math.sqrt(len(number_list)))
        self.min_value = min(number_list)
        self.max_value = max(number_list)
        self.range_value = (self.max_value - self.min_value) / \
                           self.intervals_number
        self.intervals = {}
        self.dm_calculated = 0
        self.dm_critic = 1.36 / (math.sqrt(len(self.number_list)))

    def create_intervals(self):
        """Crea los intervalos para la prueba KS."""
        expected_freq = len(self.number_list) / self.intervals_number
        for i in range(self.intervals_number):
            min_value = self.min_value + i * self.range_value if i > 0 else self.min_value
            max_value = min_value + self.range_value
            self.intervals[(min_value, max_value)] = {
                "freq_o": 0,
                                                      "freq_o_a": 0,
                                                      "prob_o_a": 0,
                "freq_e_a": expected_freq * (i + 1),
                "prob_e_a": (expected_freq * (i + 1)) / len(self.number_list),
                "abs_diff": 0
            }

    def calculate_frequence_obtained(self):
        """Calcula la frecuencia observada en cada intervalo."""
        for number in self.number_list:
            for (min_val, max_val) in self.intervals:
                if min_val <= number < max_val or (max_val == self.max_value and number == max_val):
                    self.intervals[(min_val, max_val)]["freq_o"] += 1
                    break

    def calculate_frequence_obtained_acumulated(self):
        """Calcula la frecuencia acumulada observada y su probabilidad."""
        size_list = len(self.number_list)
        temp = 0
        for frequency in self.intervals.values():
            frequency["freq_o_a"] += frequency["freq_o"] + temp
            temp += frequency["freq_o"]
            frequency["prob_o_a"] = frequency["freq_o_a"] / size_list

    def calculate_dm(self):
        """Calcula el valor de DM para la prueba KS."""
        for frequency in self.intervals.values():
            frequency["abs_diff"] = abs(
                frequency["prob_o_a"] - frequency["prob_e_a"])
            if frequency["abs_diff"] >= self.dm_calculated:
                self.dm_calculated = frequency["abs_diff"]
        self.calculate_proof()

    def calculate_proof(self):
        if self.dm_calculated < self.dm_critic:
            """
            print(
                f"La lista de números aleatorios sigue una distribución uniforme (DM = {self.dm_calculated:.6f}, DM crítico = {self.dm_critic:.6f})")
        else:
            print(
                f"La lista de números aleatorios NO sigue una distribución uniforme (DM = {self.dm_calculated:.6f}, DM crítico = {self.dm_critic:.6f})")
        """

    def show_intervals(self):
        for interval, frequency in self.intervals.items():
            print(f"Intervalo {interval}: {frequency}")


"""
if __name__ == "__main__":
    alg = random_number.LCG(5, 7, 991, 3, 4, 19)
    alg.calculate_seed(60)
    alg.print_xi()
    pm = KS(alg.ri_list)
    pm.create_intervals()
    pm.calculate_frequence_obtained()
    pm.calculate_frequence_obtained_acumulated()
    pm.calculate_dm()
    pm.show_intervals()

"""
