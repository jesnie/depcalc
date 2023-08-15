import compreq.factory as f
import compreq.operators as o
from compreq.context import DefaultContext
from compreq.root import CompReq


def compreq() -> None:
    ctx = DefaultContext(">=3.9.0")
    dc = CompReq(ctx)
    print(dc.resolve_requirement("compreq<1.0.0,>0.1.0"))
    for r in dc.resolve_release_set("tensorflow", f.releases()).releases:
        print(r)
    for r in dc.resolve_release_set("python", f.releases()).releases:
        print(r)
    print(
        dc.resolve_requirement(
            f.pkg("tensorflow")
            & f.version("<", o.ceil_ver(o.MAJOR, o.max_ver()))
            & f.version(">=", o.floor_ver(o.MINOR, o.max_ver(o.min_age(days=90))))
        )
    )


def main() -> None:
    compreq()


if __name__ == "__main__":
    main()
