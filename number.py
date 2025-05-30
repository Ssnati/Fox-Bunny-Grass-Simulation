class LCG:
    """
    Generador Congruencial Lineal (LCG) para generar números pseudoaleatorios.
    """

    def __init__(self, a, x0, m, c, min_val, max_val):
        """
        Inicializa el generador con los parámetros dados.
        :param a: Multiplicador
        :param x0: Semilla inicial
        :param m: Módulo
        :param c: Constante aditiva
        :param min_val: Valor mínimo del rango de salida
        :param max_val: Valor máximo del rango de salida
        """
        self.a = a
        self.x0 = x0
        self.m = m
        self.c = c
        self.min = min_val
        self.max = max_val
        self.xi_list = []
        self.ri_list = []
        self.ni_list = []

    def calculate_seed(self, i):
        """
        Genera una secuencia de valores pseudoaleatorios.
        :param i: Cantidad de valores a generar
        """
        for _ in range(i):
            xi = ((self.a * (self.xi_list[-1] if self.xi_list else self.x0)) + self.c) % self.m
            self.xi_list.append(xi)
            self.calculate_ri(xi)

    def calculate_ri(self, xi):
        """
        Calcula el valor normalizado ri.
        :param xi: Valor generado en la secuencia
        """
        ri = xi / self.m
        self.calculate_ni(ri)
        self.ri_list.append(ri)

    def calculate_ni(self, ri):
        """
        Calcula el valor escalado ni dentro del rango especificado.
        :param ri: Valor normalizado
        """
        ni = self.min + ((self.max - self.min) * ri)
        self.ni_list.append(ni)


class MiddleSquare:
    """
    Generador de números pseudoaleatorios basado en el método del cuadrado medio.
    """

    def __init__(self, number, digits, count):
        self.list = []
        self.normalized_list = []
        self.number = number
        self.digits = digits
        self.calculate(count)

    def calculate(self, count):
        """
        Genera una secuencia de números utilizando el método del cuadrado medio.
        :param count: Cantidad de números a generar
        """
        for _ in range(count):
            self.list.append(self.take_central_digits(self.list[-1] if self.list else self.number))

    def take_central_digits(self, number):
        """
        Extrae los dígitos centrales del número al cuadrado.
        :param number: Número de entrada
        :return: Dígitos centrales
        """
        str_n = str(number * number).zfill(self.digits * 2)
        mid_start = (len(str_n) - self.digits) // 2
        num = int(str_n[mid_start:mid_start + self.digits])
        self.normalize_list(num)
        return num

    def normalize_list(self, number):
        """
        Normaliza el número para que esté en el rango [0,1].
        """
        self.normalized_list.append(number / 10 ** len(str(number)))


lgc = LCG(a=1664525, x0=1, m=2**32, c=1013904223, min_val=0, max_val=1)
lgc.calculate_seed(1000)
ms = MiddleSquare(number=1234, digits=4, count=1000)
# Ejemplo de uso de LCG y MiddleSquare
print("LCG Normalized Values:", lgc.ni_list[:10])  # Muestra los primeros 10 valores normalizados
print("Middle Square Normalized Values:", ms.normalized_list[:10])  # Muestra los primeros 10 valores normalizados
