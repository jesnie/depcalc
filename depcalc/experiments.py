import depcalc.factory as f
import depcalc.operators as o
from depcalc.context import DefaultContext
from depcalc.root import DepCalc


def depcalc() -> None:
    ctx = DefaultContext(">=3.9.0")
    dc = DepCalc(ctx)
    print(dc.resolve_requirement("depcalc<1.0.0,>0.1.0"))
    for r in dc.resolve_release_set("tensorflow", f.releases()).releases:
        print(r)
    for r in dc.resolve_release_set("python", f.releases()).releases:
        print(r)
    print(
        dc.resolve_requirement(
            f.pkg("tensorflow")
            & f.version("<", o.ceil_ver(o.MAJOR, o.max_ver()))
            & f.version(">=", o.floor_ver(o.MINOR, o.min_ver(o.window(days=90))))
        )
    )


def main() -> None:
    depcalc()


if __name__ == "__main__":
    main()
