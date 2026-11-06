"""Planos, voz real y captions: límites que evitan desincronización y huecos."""
import importlib.util
from pathlib import Path
import unittest

PATH = Path(__file__).resolve().parents[2] / 'motion-studio/assets/plantilla/produccion.py'
SPEC = importlib.util.spec_from_file_location('produccion', PATH)
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)


class Produccion(unittest.TestCase):
    def setUp(self):
        self.cfg = {'video': {'fps': 24, 'duracion': 2}}
        self.plan = {'version': 1, 'planos': [
            {'id': 'P01', 'inicio': 0, 'fin': 24, 'impactos': [{'id': 'golpe', 'palabra': 0, 'efecto': 'tic'}]},
            {'id': 'P02', 'inicio': 24, 'fin': 48}]}
        self.words = M.leer_palabras({'segments': [{'words': [{'word': ' Hola', 'start': 0.8, 'end': 1.2}]}]})

    def test_fps_real_y_corte(self):
        r = M.preparar(self.plan, self.cfg, self.words)
        self.assertEqual(r['impactos'][0]['fotograma'], 19)
        self.assertEqual(r['subtitulos'][0]['fin'], 1)
        self.assertIn(19, r['muestras'])
        self.assertEqual(r['muestras'][-1], 47)

    def test_make_short_voice(self):
        w = M.leer_palabras({'lines': [{'words': [{'w': 'Hi', 'start': 0.1, 'end': 0.3}]}]})
        self.assertEqual(w[0]['word'], 'Hi')
        self.assertEqual(M.preparar(self.plan, self.cfg, w)['impactos'][0]['fotograma'], 2)

    def test_gap(self):
        self.plan['planos'][1]['inicio'] = 25
        with self.assertRaisesRegex(ValueError, 'hueco'):
            M.preparar(self.plan, self.cfg, self.words)

    def test_out_of_range(self):
        self.plan['planos'][0]['impactos'][0] = {'id': 'golpe', 'fotograma': 24}
        with self.assertRaisesRegex(ValueError, 'fuera'):
            M.preparar(self.plan, self.cfg)

    def test_invalid_voice(self):
        for d in ({}, {'words': [{'word': 'x', 'start': -1, 'end': 0}]}):
            with self.assertRaises(ValueError):
                M.leer_palabras(d)

    def test_voice_overrun(self):
        with self.assertRaisesRegex(ValueError, 'supera'):
            M.preparar(self.plan, self.cfg, [{'word': 'x', 'start': 1, 'end': 3}])


if __name__ == '__main__':
    unittest.main()
