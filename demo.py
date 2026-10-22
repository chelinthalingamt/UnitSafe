"""Review demos: python demo.py showcase | review2 | review3"""
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent
STEPS = {
    'review2': [
        ('1. A valid program runs', ['run', 'demo/review2/01_valid.us']),
        ('2. kg + s is rejected, with its rule ID', ['run', 'demo/review2/02_mixup.us']),
        ('3. The generated Python has no unit code at run time', ['build', 'demo/review2/01_valid.us', '-o', 'demo/review2/01_valid.py']),
        ('4. Several mistakes, all reported at once', ['check', 'demo/review2/03_several_mistakes.us']),
    ],
    'showcase': [
        ('1. A car trip: units, functions, if / else if, pi', ['run', 'demo/showcase/01_motion.us']),
        ('2. Conversions and nicknames: km, h, min, N, J, W, kW', ['run', 'demo/showcase/02_conversions.us']),
        ('3. Angles: ramps, slopes and rolling wheels', ['run', 'demo/showcase/03_angles.us']),
        ('4. Quantity kinds and temperatures', ['run', 'demo/showcase/04_kinds_temperatures.us']),
        ('5. Empirical formulas: speed of sound, metabolic rate', ['run', 'demo/showcase/05_empirical.us']),
        ('6. Money in two currencies', ['run', 'demo/showcase/06_money.us']),
        ('7. Units checked at the input: pound-force seconds are converted', ['run', 'demo/showcase/07_input_check.us'], '1100 lbf * s'),
        ('8. Ready-made SI units (use si), results printed as J and W', ['run', 'demo/showcase/08_use_si.us']),
    ],
    'review3': [
        ('1. Conversions: km and hours in, km / h out', ['run', 'demo/review3/01_conversions.us']),
        ('2. Angles: sin(90) is refused before running (sin(90 deg) on line 2 is fine)', ['run', 'demo/review3/02_angles.us']),
        ('3. Quantity kinds: torque + energy is refused', ['run', 'demo/review3/03_kinds.us']),
        ('4. Temperatures: readings, changes, Celsius and Fahrenheit', ['run', 'demo/review3/04_temperatures.us']),
        ('5. Empirical functions: fractional powers, checked edges', ['run', 'demo/review3/05_empirical.us']),
        ('6. Input with the wrong unit is refused while running', ['run', 'demo/showcase/07_input_check.us'], '1100 kg'),
        ('7. Several syntax mistakes, all reported in one run', ['check', 'demo/review3/07_syntax_errors.us']),
    ],
}


def main(name):
    for title, args, *typed in STEPS[name]:
        print('=' * 70, flush=True)
        print(title, flush=True)
        print('$ python -m unitsafe ' + ' '.join(args), flush=True)
        print('-' * 70, flush=True)
        if typed:
            print(f'(typed in: {typed[0]})', flush=True)
        subprocess.run([sys.executable, '-m', 'unitsafe', *args], cwd=ROOT,
                       input=(typed[0] + '\n') if typed else None, text=True)
        if typed:
            print(flush=True)
        if args[0] == 'build':
            print((ROOT / args[-1]).read_text(encoding='utf-8').split('def fall_time')[1].join(['def fall_time', '']), flush=True)
        print(flush=True)


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'review2')
