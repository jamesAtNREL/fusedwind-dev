from numpy.core.umath import sin, pi
import numpy as np
from fusedwind.core.openmdao_interface import fused_func, Inputs, Outputs
from fusedwind.variables import wind_speed, wind_direction, power
from openmdao.components.execcomp import ExecComp
from openmdao.components.paramcomp import ParamComp
from openmdao.core.group import Group
from openmdao.core.problem import Problem

__author__ = 'pire'

import unittest


class TestFused_func(unittest.TestCase):

    def test_one_output(self):

        @fused_func(
            Inputs(
                ws = wind_speed(4.0),
                wd = wind_direction(270.0)),
            Outputs(
                p = power))
        def my_silly_func(u, d):
            return u**3.0 * sin(d * pi/180.)

        a = my_silly_func(3.0, 0.0)
        self.assertAlmostEqual(a(5.0, 90.0), 5.0**3.0)

    def test_several_outputs(self):

        @fused_func(
            Inputs(
                ws = wind_speed(4.0),
                wd = wind_direction(270.0)),
            Outputs(
                p1 = power,
                p2 = power,
                p3 = power))
        def my_silly_func(u, d):
            return [i * u**3.0 * sin(d * pi/180.) for i in range(3)]

        a = my_silly_func(3.0, 0.0)
        for i in range(3):
            self.assertAlmostEqual(a(5.0, 90.0)[i], i*5.0**3.0)

    def test_call_error(self):
        @fused_func(
            Inputs(
                ws = wind_speed(4.0),
                wd = wind_direction(270.0)),
            Outputs(
                p = power))
        def my_silly_func(u, d):
            return u**3.0 * sin(d * pi/180.)

        a = my_silly_func(3.0, 0.0)
        with self.assertRaises(NotImplementedError,
                               msg='Only use args or kwargs independently, not both at the same time.'):
            a(3.0, wd=90.0)



class TestOpenMDAOInterface(unittest.TestCase):

    def setUp(self):
        @fused_func(
            Inputs(
                ws = wind_speed(4.0),
                wd = wind_direction(270.0)),
            Outputs(
                p = power))
        def my_silly_func(u, d):
            return u**3.0 * sin(d * pi/180.0)

        self.func = my_silly_func()

    def test_add(self):
        pb = Problem(root=Group())
        pb.root.add('a', self.func)
        pb.setup()
        self.assertTrue(hasattr(pb.root,'a'))
        self.assertTrue('ws' in pb.root.a.params)

    def test_promotes(self):
        pb = Problem(root=Group())
        pb.root.add('a', self.func, promotes=['*'])
        pb.setup()
        self.assertTrue('p' in pb.root.unknowns)

    def test_connection(self):
        pb = Problem(root=Group())
        pb.root.add('a', self.func, promotes=['*'])
        pb.root.add('eq', ExecComp('y = p*2.0'), promotes=['*'])
        pb.setup()
        self.assertEqual(pb.root.connections, {'eq.p':'a.p'})

    def test_run(self):
        pb = Problem(root=Group())
        pb.root.add('iws', ParamComp('ws', 5.0), promotes=['*'])
        pb.root.add('iwd', ParamComp('wd', 90.0), promotes=['*'])
        pb.root.add('a', self.func, promotes=['*'])
        pb.root.add('eq', ExecComp('y = p*2.0'), promotes=['*'])
        pb.setup()
        pb.run()
        result = 5.0**3.0 * sin(90.0 * pi / 180.0)  * 2.0
        self.assertAlmostEqual(pb.root.unknowns['y'], result)

