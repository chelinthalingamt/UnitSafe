"""Review demos: python demo.py review2   or   python demo.py review3"""
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
    'review3': [
        ('1. Conversions: km and hours in, km / h out', ['run', 'demo/review3/01_conversions.us']),
        ('2. Angles: sin(90) is refused before running (sin(90 deg) on line 2 is fine)', ['run', 'demo/review3/02_angles.us']),
        ('3. Quantity kinds: torque + energy is refused', ['run', 'demo/review3/03_kinds.us']),
        ('4. Temperatures: readings, changes, Celsius and Fahrenheit', ['run', 'demo/review3/04_temperatures.us']),
        ('5. Empirical functions: fractional powers, checked edges', ['run', 'demo/review3/05_empirical.us']),
    ],
}


def main(name):
    for title, args in STEPS[name]:
        print('=' * 70, flush=True)
        print(title, flush=True)
        print('$ python -m unitsafe ' + ' '.join(args), flush=True)
        print('-' * 70, flush=True)
        subprocess.run([sys.executable, '-m', 'unitsafe', *args], cwd=ROOT)
        if args[0] == 'build':
            print((ROOT / args[-1]).read_text(encoding='utf-8').split('def fall_time')[1].join(['def fall_time', '']), flush=True)
        print(flush=True)


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'review2')
