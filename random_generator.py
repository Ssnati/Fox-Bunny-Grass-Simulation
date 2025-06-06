class LCG:
    """
    Generador Congruencial Lineal (LCG) para generar números pseudoaleatorios.
    """
    def __init__(self, a, x0, m, c, min_val, max_val):
        self.a = a
        self.x0 = x0
        self.m = m
        self.c = c
        self.min = min_val
        self.max = max_val
        self.xi_list = []
        self.ri_list = []
        self.ni_list = []
        self.calculate_seed(10000)

    def calculate_seed(self, i):
        for _ in range(i):
            xi = ((self.a * (self.xi_list[-1] if self.xi_list else self.x0)) + self.c) % self.m
            self.xi_list.append(xi)
            self.calculate_ri(xi)

    def calculate_ri(self, xi):
        ri = xi / self.m
        self.calculate_ni(ri)
        self.ri_list.append(ri)

    def calculate_ni(self, ri):
        ni = self.min + ((self.max - self.min) * ri)
        self.ni_list.append(ni)

    def pop_last(self):
        """
        Elimina y retorna el último número generado (ni), junto con ri y xi.
        :return: Tupla (ni, ri, xi) o None si las listas están vacías
        """
        if not self.ni_list:
            return None
        ni = self.ni_list.pop()
        ri = self.ri_list.pop()
        xi = self.xi_list.pop()
        return ni, ri, xi
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
        for _ in range(count):
            self.list.append(self.take_central_digits(self.list[-1] if self.list else self.number))

    def take_central_digits(self, number):
        str_n = str(number * number).zfill(self.digits * 2)
        mid_start = (len(str_n) - self.digits) // 2
        num = int(str_n[mid_start:mid_start + self.digits])
        self.normalize_list(num)
        return num

    def normalize_list(self, number):
        self.normalized_list.append(number / 10**len(str(number)))

    def pop_last(self):
        """
        Elimina y retorna el último número generado (original y normalizado).
        :return: Tupla (número original, número normalizado) o None si está vacío
        """
        if not self.list:
            return None
        original = self.list.pop()
        normalized = self.normalized_list.pop()
        return original, normalized
