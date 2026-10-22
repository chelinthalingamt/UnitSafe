"""Phase 8: quantity kinds (build guide Part 7, K1-K6, K4b)."""
import unittest

from tests.helpers import TableMixin, current_phase
from tests.test_checker import messages

H = ('unit kg\nunit m\nunit s\nunit N = kg * m / s^2\nkind torque\nkind energy\n'
     'unit J = N * m of energy\nlet tau: N * m of torque = 40 N * m\nlet work = 40 J\n')
P = 'fn p(t: N * m of torque) -> N * m of torque\n  return t\nend\n'


@unittest.skipIf(current_phase() < 8, 'phase 8')
class Kinds(TableMixin, unittest.TestCase):
    def test_rows(self):
        self.run_table([
            (H + 'print(tau + work)', '!K3'),
            (H + 'print(tau + 5 N * m)', '!K3'),
            (H + 'print(tau + 2 * tau)', '120 kg * m^2 / s^2'),
            (H + 'print(tau / 2 + tau)', '60 kg * m^2 / s^2'),
            (H + 'let F = 10 N\nlet d = 3 m\nlet e: J = F * d\nprint(e)', '30 J'),
            (H + 'let e: J = tau', '!K5'),
            (H + 'let x: N * m = tau', '!K5'),
            (H + 'print(tau > work)', '!K3'),
            (H + 'kind torque', '!K6'),
            (H + 'kind m', '!K6'),
            (H + 'let torque = 1', '!K6'),
            (H + 'let x: N * m of mass = 1 N * m', '!K1'),
            (H + 'let x: J of torque = 1 J', '!K2'),
            (H + 'unit E2 = N * m of mass', '!K1'),
            (H + 'print(abs(tau))', '40 kg * m^2 / s^2'),
            (H + P + 'print(p(work))', '!K5'),
            (H + P + 'print(p(tau))', '40 N * m'),
            (H + 'print(tau in J)', '!K3'),
            (H + 'unit kJ = 1000 J\nprint(2 kJ + work in J)', '2040 J'),
            (H + 'let y = tau\ny = 5 N * m\nprint(y)', '5 kg * m^2 / s^2'),
            (H + 'let y = tau\ny = work', '!K5'),
            (H + 'print(torque)', '!S12'),
            (H + 'print(sqrt(tau * tau))', '40 kg * m^2 / s^2'),
            (H + 'print(work * 2 + work)', '120 kg * m^2 / s^2'),
            (H + 'print(-tau + tau)', '0 kg * m^2 / s^2'),
        ])

    def test_messages(self):
        self.assertEqual(messages(H + 'print(tau + work)'), ['cannot add torque and energy'])
        self.assertEqual(messages(H + 'print(tau + 5 N * m)'),
                         ['cannot add torque and a plain value; write of torque to label it'])
        self.assertEqual(messages(H + 'let e: J = tau'), ["'e' holds energy, not torque"])


if __name__ == '__main__':
    unittest.main()
