import itertools
import json
import unittest
from simulador import Maquina, EJEMPLOS, leer_reglas, validar_configuracion


def ejecutar(entrada, reglas):
    m = Maquina(entrada, leer_reglas(reglas))
    for _ in range(2000):
        if m.terminada:
            return m
        m.paso()
    raise AssertionError("El ejemplo no terminó")


def salida(m):
    if not m.cinta:
        return ""
    return "".join(m.cinta.get(i, "_") for i in range(min(m.cinta), max(m.cinta) + 1))


class Pruebas(unittest.TestCase):
    def test_lenguaje_y_paridad(self):
        ejemplos = list(EJEMPLOS.values())
        for n in range(9):
            for caracteres in itertools.product("01", repeat=n):
                entrada = "".join(caracteres)
                esperado = n % 2 == 0 and entrada == "0" * (n // 2) + "1" * (n // 2)
                self.assertEqual(ejecutar(entrada, ejemplos[0][1]).resultado == "ACEPTADA", esperado)
                self.assertEqual(ejecutar(entrada, ejemplos[3][1]).resultado == "ACEPTADA",
                                 entrada.count("1") % 2 == 0)

    def test_operaciones_binarias(self):
        ejemplos = list(EJEMPLOS.values())
        for numero in range(128):
            entrada = bin(numero)[2:]
            self.assertEqual(salida(ejecutar(entrada, ejemplos[1][1])), bin(numero + 1)[2:])
            self.assertEqual(salida(ejecutar(entrada, ejemplos[2][1])),
                             "".join("1" if c == "0" else "0" for c in entrada))
        self.assertEqual(salida(ejecutar("", ejemplos[1][1])), "1")

    def test_retroceso_completo_y_reanudacion(self):
        m = Maquina("111", leer_reglas(list(EJEMPLOS.values())[1][1]))
        fotos = []
        while not m.terminada:
            fotos.append((dict(m.cinta), m.estado, m.cabezal, m.pasos, m.motivo))
            m.paso()
        for foto in reversed(fotos):
            self.assertTrue(m.retroceder())
            self.assertEqual((m.cinta, m.estado, m.cabezal, m.pasos, m.motivo), foto)
        self.assertFalse(m.retroceder())
        while not m.terminada:
            m.paso()
        self.assertEqual(salida(m), "1000")

    def test_deshacer_detencion_y_borrado(self):
        m = Maquina("1", leer_reglas("q0 1 _ L q1"))
        m.paso()
        self.assertEqual(m.cinta, {})
        m.paso()
        self.assertTrue(m.terminada)
        m.retroceder()
        self.assertFalse(m.terminada)
        m.retroceder()
        self.assertEqual(m.cinta, {0: "1"})
        self.assertEqual(m.cabezal, 0)

    def test_reglas_invalidas(self):
        for texto in ("", "q0 0 0 Z q0", "q0 00 1 R q0",
                      "q0 0 0 R q0\nq0 0 1 R q1"):
            with self.assertRaises(ValueError):
                leer_reglas(texto)

    def test_json(self):
        datos = dict(version=1, entrada="0011", reglas=list(EJEMPLOS.values())[0][1],
                     inicial="q0", acepta="aceptar", rechaza="rechazar")
        self.assertEqual(validar_configuracion(json.loads(json.dumps(datos))), datos)
        for malo in (None, {}, dict(datos, version=2), dict(datos, entrada=10),
                     dict(datos, rechaza="aceptar")):
            with self.assertRaises(ValueError):
                validar_configuracion(malo)


if __name__ == "__main__":
    unittest.main()
