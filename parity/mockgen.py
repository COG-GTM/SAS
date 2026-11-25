"""Deterministic mock-data generator for the SAS-vs-PySpark parity harness.

Every file mirrors the record layout of the matching file in ../Data (or of the
DATALINES block it replaces in the book programs) but is larger and seeded, and
deliberately includes the edge cases that separate a faithful port from a naive
one: missing values ('.'), names longer than the default $8 list-input length,
two-digit years around YEARCUTOFF, division by zero, short records, duplicate
BY values, negative numbers for SQRT/LOG, etc.

Output layout (under --out, default parity/build/mock):
  raw/<file>                 external files the programs INFILE (lower-case names)
  datalines/<key>__<k>.dat   replacement body for the k-th DATALINES block of a snippet
"""
from __future__ import annotations

import argparse
import datetime as dt
import random
from pathlib import Path

SEED = 20261125
EPOCH = dt.date(1960, 1, 1)
MON = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def rdate(r: random.Random, lo: dt.date, hi: dt.date) -> dt.date:
    return lo + dt.timedelta(days=r.randint(0, (hi - lo).days))


def mdy(d: dt.date, pad: bool = True) -> str:
    return f"{d.month:02d}/{d.day:02d}/{d.year}" if pad else f"{d.month}/{d.day}/{d.year}"


def maybe(r: random.Random, p: float, val: str, miss: str = ".") -> str:
    return miss if r.random() < p else val


class Gen:
    def __init__(self, out: Path):
        self.out = out
        self.r = random.Random(SEED)
        (out / "raw").mkdir(parents=True, exist_ok=True)
        (out / "datalines").mkdir(parents=True, exist_ok=True)

    def raw(self, name: str, lines: list[str]):
        (self.out / "raw" / name).write_text("\n".join(lines) + "\n")

    def dl(self, key: str, k: int, lines: list[str]):
        for ln in lines:
            assert ";" not in ln, ln
        (self.out / "datalines" / f"{key}__{k}.dat").write_text("\n".join(lines) + "\n")

    # ------------------------------------------------------------------ external files
    def veggies(self):
        r = self.r
        names = ["Cucumber", "Carrot", "Corn", "Eggplant", "Tomato", "Watermelon", "Zucchini",
                 "Pumpkin", "Broccoli", "Cauliflower", "Pea", "Bean"]
        rows = []
        for _ in range(400):
            n = r.choice(names)
            code = f"{r.randint(50000, 59999)}-{r.choice('ABC')}"
            days = maybe(r, .03, str(r.randint(40, 120)))
            number = r.choice(["0", "30", "50", "100", "200", "1500", str(r.randint(1, 3000))]) \
                if r.random() > .02 else "."
            price = maybe(r, .03, f"{r.randint(99, 995)}" if r.random() < .7 else f"{r.uniform(1, 9):.2f}")
            rows.append(f"{n} {code} {days} {number} {price}")
        self.raw("veggies.txt", rows)

    def mydata(self):
        r = self.r
        rows, csv = [], []
        for _ in range(500):
            g = r.choice("MF")
            age = maybe(r, .04, str(r.randint(12, 90)))
            h = maybe(r, .04, str(r.randint(55, 78)) if r.random() < .8 else f"{r.uniform(55, 78):.1f}")
            w = maybe(r, .04, str(r.randint(85, 300)))
            rows.append(f"{g} {age} {h} {w}")
            csv.append(",".join([f'"{g}"', age.replace(".", "") if age == "." else age,
                                 "" if h == "." else h, "" if w == "." else w]))
        self.raw("mydata.txt", rows)
        self.raw("mydata.csv", csv)

    def bank(self):
        r = self.r
        rows = []
        for i in range(1, 601):
            dob = mdy(rdate(r, dt.date(1925, 1, 1), dt.date(2005, 12, 31)))
            if r.random() < .03:
                dob = " " * 10
            g = r.choice("MF") if r.random() > .02 else " "
            kind = r.random()
            if kind < .5:
                bal = str(r.randint(0, 999999))
            elif kind < .85:
                bal = f"{r.uniform(-9999, 99999):.2f}"
            elif kind < .95:
                bal = str(-r.randint(1, 99999))
            else:
                bal = ""
            rows.append(f"{i:03d}"[-3:] + dob + g + f"{bal:>7}"[:7])
        self.raw("bank.txt", rows)

    def _people(self):
        first = ["Christopher", "Michelle", "Roger", "Ann", "Bo", "Jose", "Mary Ellen", "Li",
                 "Alexandria", "Fitzgerald", "Kim", "Pat"]
        last = ["Mullens", "Kwo", "McDonald", "Smith", "Ng", "Ramirez", "Van der Berg-Hollingsworth",
                "O'Neil", "Chen", "Abernathy", "Wu"]
        return first, last

    def lists(self):
        r = self.r
        first, last = self._people()
        csv, txt = [], []
        for i in range(1, 401):
            name = f"{r.choice(first)} {r.choice(['', 'W. ', 'J. '])}{r.choice(last)}".replace("  ", " ")
            d = rdate(r, dt.date(1930, 1, 1), dt.date(2000, 12, 31))
            sal = r.randint(15000, 199999)
            sal_s = f"${sal:,}"
            if len(sal_s) > 8:          # keep inside the dollar8. informat width
                sal_s = f"{sal // 10:,}"
            csv.append(f'"{i:03d}","{name}",{mdy(d, pad=False)},"{sal_s}"')
            txt.append(f"{i:03d} {name}  {mdy(d, pad=False)} {sal_s}")
        self.raw("list.csv", csv)
        self.raw("list.txt", txt)

    def survey(self):
        r = self.r
        rows = []
        for i in range(1, 501):
            qs = " ".join(r.choice("12345") for _ in range(5))
            rows.append(f"{i:03d} {r.choice('MF')} {maybe(r, .03, str(r.randint(18, 85)))} "
                        f"{maybe(r, .03, str(r.randint(12000, 250000)))} {qs}")
        self.raw("survey.txt", rows)

    def grades(self):
        r = self.r
        rows = []
        for _ in range(500):
            f = [maybe(r, .06, str(r.randint(14, 80))), r.choice("MF"),
                 maybe(r, .05, str(r.randint(40, 100))),
                 maybe(r, .08, r.choice(["A+", "A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D", "F"])),
                 maybe(r, .05, str(r.randint(40, 100)))]
            if r.random() < .06:          # short record -> MISSOVER sets trailing vars missing
                f = f[:r.randint(2, 4)]
            rows.append(" ".join(f))
        self.raw("grades.txt", rows)

    def dates(self):
        r = self.r
        rows = []
        for i in range(1, 401):
            dob = rdate(r, dt.date(1920, 1, 1), dt.date(2010, 12, 31))
            visit = rdate(r, max(dob, dt.date(1990, 1, 1)), dt.date(2025, 12, 31))
            two = rdate(r, dt.date(1926, 1, 1), dt.date(2025, 12, 31))
            last = rdate(r, dt.date(1950, 1, 1), dt.date(2030, 12, 31))
            if i % 37 == 0:   # leap-day birthdays exercise YRDIF/AGE
                dob = dt.date(r.choice([1952, 1960, 1984, 2000]), 2, 29)
            mon = MON[last.month - 1]
            mon = mon.upper() if r.random() < .2 else mon
            line = (f"{i:03d} {mdy(dob)} {visit.month:02d}{visit.day:02d}{visit.year} "
                    f"{two.month:02d}/{two.day:02d}/{two.year % 100:02d} {last.day:02d}{mon}{last.year}")
            if r.random() < .05:
                line = line[:33]          # TRUNCOVER: LastDate missing
            rows.append(line)
        self.raw("dates.txt", rows)

    def blood(self):
        r = self.r
        rows = []
        for i in range(1, 1501):
            g = r.choices(["Female", "Male", "."], [48, 48, 4])[0]
            bt = r.choices(["A", "B", "AB", "O"], [40, 11, 4, 45])[0]
            ag = r.choice(["Young", "Old"])
            wbc = maybe(r, .05, str(r.randint(4000, 11000)))
            rbc = maybe(r, .05, f"{r.uniform(3.5, 8.5):.2f}".rstrip("0").rstrip("."))
            chol = maybe(r, .1, str(r.randint(120, 330)))
            rows.append(f"{i:<4d} {g:<6} {bt:<2} {ag:<5} {wbc:<6} {rbc:<4} {chol}")
        self.raw("blood.txt", rows)

    # ------------------------------------------------------------------ datalines mocks
    def conditional(self):
        r = self.r
        rows = []
        for _ in range(300):
            rows.append(" ".join([maybe(r, .08, str(r.randint(10, 85))), r.choice("MF"),
                                  maybe(r, .05, str(r.randint(40, 100))),
                                  maybe(r, .08, r.choice(["A+", "A", "B+", "B-", "C", "C-", "F"])),
                                  maybe(r, .05, str(r.randint(40, 100)))]))
        for key in ("book_7-3", "book_7-5"):
            self.dl(key, 1, rows)

    def revenue(self):
        r = self.r
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        rows = [f"{days[i % 7]} {maybe(r, .1, '$' + format(r.randint(0, 99) * 100 + r.choice([0, 50]), ','))}"
                for i in range(250)]
        self.dl("book_8-5", 1, rows)

    def ch10(self):
        r = self.r
        surn = ["Adams", "Smith", "Schneider", "Gregory", "Shea", "O'Brien", "Bessler", "Horvath",
                "Stevens", "Brown", "Washington", "Featherstonehaugh", "Li", "Okafor", "Nguyen"]
        ids = r.sample(range(1, 400), 120)
        one = ids[:50]
        two = ids[40:90]                     # overlapping IDs -> interleave ties
        three = ids[90:120]
        self.dl("section_ch10-setup", 1, [f"{i} {r.choice(surn)} {r.randint(80, 260)}" for i in one])
        self.dl("section_ch10-setup", 2, [f"{i} {r.choice(surn)} {r.randint(80, 260)}" for i in two])
        self.dl("section_ch10-setup", 3, [f"{i} {r.choice('MF')} {r.choice(surn)}" for i in three])
        emp = r.sample(range(1, 300), 80)
        self.dl("section_ch10-setup", 4, [f"{i} {r.choice(surn)}" for i in emp])
        hrs = r.sample(emp, 50) + r.sample(range(300, 400), 15)
        hrs += r.sample(hrs, 10)             # one-to-many: duplicate IDs in HOURS
        r.shuffle(hrs)
        self.dl("section_ch10-setup", 5, [f"{i} {r.choice('ABC')} {maybe(r, .05, str(r.randint(10, 60)))}"
                                          for i in hrs])
        bert = sorted(r.sample(range(100, 999), 60))
        ernie = sorted(r.sample(bert, 40) + r.sample(range(100, 999), 15))
        ernie = sorted(set(ernie))
        self.dl("section_ch10-setup", 6, [f"{i} {r.randint(50, 150)}" for i in bert])
        self.dl("section_ch10-setup", 7, [f"{i} {r.randint(150, 400)}" for i in ernie])
        ss = sorted(r.sample(range(100000000, 999999999), 60))
        d1 = [f"{s} {mdy(rdate(r, dt.date(1940, 1, 1), dt.date(1999, 12, 31)), pad=False)} {r.choice('MF')}"
              for s in ss[:50]]
        d2 = []
        for s in sorted(ss[10:]):
            t = f"{s:09d}"
            d2.append(f"{t[:3]}-{t[3:5]}-{t[5:]} {r.choice(['A10', 'B5', 'A20', 'C7'])} ${r.randint(20000, 99999):,}")
        self.dl("section_ch10-setup", 8, d1)
        self.dl("section_ch10-setup", 9, d2)
        self.dl("section_ch10-setup", 10, [f"{r.choice([123, 222, 333, 444])}  {r.randint(100, 600)}"
                                           for _ in range(12)])
        words = ["foot hose", "greeting card", "lb. grass seed", "lb. fertilizer", "garden rake",
                 "bird feeder", "watering can", "hand trowel"]
        codes = sorted(r.sample(range(100, 999), 40))
        prices = []
        for c in codes:
            desc = f"{r.randint(5, 80)} {r.choice(words)}" if r.random() < .6 else r.choice(words)
            prices.append(f"{c} {desc[:17].rstrip()}  {r.uniform(0.5, 99):.2f}")
        self.dl("section_ch10-setup", 11, prices)
        upd = r.sample(codes, 15) + r.sample(range(100, 999), 5)
        self.dl("section_ch10-setup", 12, [f"{c} {maybe(r, .25, f'{r.uniform(0.5, 99):.2f}')}" for c in upd])

    def ch11(self):
        r = self.r
        self.dl("book_11-1", 1, [f"{r.uniform(1, 90):.2f} {r.uniform(40, 300):.2f} "
                                 f"{r.choice(['.0001', '5.99', '0', '-2.5', f'{r.uniform(0, 500):.3f}'])}"
                                 for _ in range(200)])
        self.dl("book_11-4", 1, [f"{i:03d} " + " ".join(maybe(r, .25, str(r.randint(1, 9))) for _ in range(10))
                                 for i in range(1, 201)])
        vals = [r.choice(["2", "-2", "0", "10", "100", "0.5", "-0.25", "3.75", "-7", "1"]) for _ in range(120)]
        self.dl("book_11-7", 1, [" ".join(vals[i:i + 7]) for i in range(0, len(vals), 7)])
        temps = [f"{t} {maybe(r, .08, str(r.randint(30, 99)))}" for t in range(1, 201)]
        self.dl("book_11-15", 1, temps)
        xs = [str(r.randint(0, 15)) for _ in range(150)]
        self.dl("book_11-16", 1, [" ".join(xs[i:i + 6]) for i in range(0, len(xs), 6)])
        self.dl("book_11-18", 1, temps)
        q = [f"{i:03d} " + " ".join(maybe(r, .12, str(r.randint(40, 100))) for _ in range(8)) for i in range(1, 201)]
        self.dl("book_11-19", 1, q)
        self.dl("book_11-20", 1, q)

    def ch12(self):
        r = self.r
        firsts = ["ron", "JASON", "mary  ann", "o'neil", "peter", "LAURA", "al"]
        lasts = ["coDY", "Tran", "SMITH", "van  dyke", "mcdonald", "o'brien-jones"]
        streets = ["1178  HIGHWAY 480", "123 lake  view drive", "80 LAZY brook road", "9 elm st."]
        cities = ["camp   verde", "East  Rockaway", "flemington", "LONG beach", "new  york"]
        addr = []
        for _ in range(60):
            addr += [f"{r.choice(firsts)}   {r.choice(lasts)}", r.choice(streets),
                     f"{r.choice(cities):<20}{r.choice(['tx', 'NY', 'nj', 'Ca'])} {r.randint(10000, 99999)}"]
        self.dl("cd_ADDRESS", 1, addr)
        ids = []
        for _ in range(150):
            st = r.choice(["NJ", "NY", "TX", "CA", "PA"])
            ids.append(f"{st}{r.randint(10, 99)}{r.choice('MF')}{r.randint(0, 99999)}"[:10])
        self.dl("book_12-12", 1, [" ".join(ids[i:i + 4]) for i in range(0, len(ids), 4)])
        names = ["Jeffrey Smith", "Ron Cody", "Alan Wilson", "Alfred E. Newman", "Mary Ellen Van Dyke",
                 "Cher", "Robert  Merrill", "Ann Marie O'Neil", "Li Wu", "Zelda A. B. Fitzgerald"]
        self.dl("book_12-13", 1, [r.choice(names) for _ in range(120)])
        self.dl("book_12-16", 1, ["".join(r.choice("12345ABCDE9") for _ in range(r.randint(3, 6)))
                                  for _ in range(100)])
        pre = ["Dr.", "Mr.", "Mrs.", "Ms.", ""]
        st = ["Road", "Avenue", "Street", "Lane"]
        a2 = []
        for _ in range(60):
            a2 += [f"{r.choice(pre)} {r.choice(['Peter', 'Robert', 'Laura', 'Ann'])} "
                   f"{r.choice(['Benchley', 'Merrill', 'Smith', 'Mr.Mister'])}".strip(),
                   f"{r.randint(1, 999)} {r.choice(['River', 'Ocean', 'Lazy Brook', 'Main'])} {r.choice(st)}",
                   f"{r.choice(['Oceanside', 'Long Beach', 'Flemington', 'Salt Lake City'])}, "
                   f"{r.choice(['NY', 'CA', 'NJ', 'UT'])} {r.randint(1000, 99999):05d}"]
        self.dl("book_12-17", 1, a2)

    def ch13(self):
        r = self.r
        temps = [str(r.randint(20, 100)) for _ in range(24 * 30)]
        self.dl("book_13-5", 1, [" ".join(temps[i:i + 17]) for i in range(0, len(temps), 17)])
        self.dl("book_13-6", 1, [f"{i:03d} " + " ".join(maybe(r, .05, str(r.randint(20000, 150000))) for _ in range(8))
                                 for i in range(1, 151)])
        self.dl("book_13-7", 1, [f"{r.randint(100, 999)} " + "".join(r.choice("ABCDE ") for _ in range(10)).rstrip()
                                 for _ in range(200)])

    def clinic(self):
        r = self.r
        rows = []
        for pid in r.sample(range(100, 999), 120):
            d = rdate(r, dt.date(2004, 1, 1), dt.date(2007, 12, 31))
            for _ in range(r.choice([1, 1, 2, 3, 4, 5, 6])):
                rows.append(f"{pid} {mdy(d, pad=False)} {r.randint(1, 7)} {r.randint(50, 110)} "
                            f"{r.randint(100, 220)} {r.randint(60, 120)}")
                d += dt.timedelta(days=r.randint(1, 200))
        r.shuffle(rows)
        self.dl("cd_CLINIC", 1, rows)

    def health_demog(self):
        r = self.r
        h = r.sample(range(1, 300), 150)
        d = r.sample(range(1, 300), 150)
        self.dl("cd_HEALTH", 1, [f"{s:03d} {r.randint(56, 78)} {maybe(r, .05, str(r.randint(90, 280)))}" for s in h])
        names = ["Friedman", "Stern", "McGoldrick", "Chien", "Abernathy", "Okafor", "Nguyen", "Rossi"]
        self.dl("cd_DEMOGRAPHIC", 1, [f"{s:03d} {mdy(rdate(r, dt.date(1930, 1, 1), dt.date(2000, 12, 31)), pad=False)} "
                                      f"{r.choice('MF')} {r.choice(names)}" for s in d])

    def oneper(self):
        r = self.r
        rows = []
        for s in range(1, 301):
            dx = [str(r.choice([240, 250, 410, 430, 450, 500])) for _ in range(3)]
            for k in range(3):
                if r.random() < .2:
                    dx[k] = "."
            rows.append(f"{s:03d} " + " ".join(f"{x:>6}" for x in dx))
        self.dl("cd_ONEPER", 1, rows)

    def all(self):
        for f in (self.veggies, self.mydata, self.bank, self.lists, self.survey, self.grades, self.dates,
                  self.blood, self.conditional, self.revenue, self.ch10, self.ch11, self.ch12, self.ch13,
                  self.clinic, self.health_demog, self.oneper):
            f()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(Path(__file__).parent / "build" / "mock"))
    out = Path(ap.parse_args().out)
    Gen(out).all()
    n = sum(1 for _ in out.rglob("*") if _.is_file())
    print(f"mock data: {n} files written to {out} (seed {SEED})")


if __name__ == "__main__":
    main()
