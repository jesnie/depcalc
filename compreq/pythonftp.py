"""
Code for crawling https://www.python.org/ftp/
"""
from __future__ import annotations

import datetime as dt
import re
from abc import ABC, abstractmethod
from typing import Mapping, NewType

import requests
from bs4 import BeautifulSoup, NavigableString, Tag

from compreq.time import UtcDatetime, is_utc_datetime, utc_now

Url = NewType("Url", str)

LS_LINE_RE = re.compile(r"\s*(\d\d-\w\w\w-\d\d\d\d\s\d\d:\d\d)\s*((-)|(\d+))\s*")
LS_TIMESTAMP_FORMAT = "%d-%b-%Y %H:%M"


class FtpPath(ABC):
    def __init__(self, path_str: str, modified: UtcDatetime) -> None:
        assert path_str.startswith("/"), path_str
        self.path_str = path_str
        self.modified = modified

    @property
    def url(self) -> Url:
        return Url("https://www.python.org/ftp" + self.path_str)

    @abstractmethod
    def as_dir(self) -> FtpDir:
        ...

    @abstractmethod
    def as_file(self) -> FtpFile:
        ...


class FtpDir(FtpPath):
    def __init__(self, path_str: str, modified: UtcDatetime) -> None:
        super().__init__(path_str, modified)
        assert path_str.endswith("/"), path_str

    def ls(self) -> Mapping[str, FtpPath]:
        html = requests.get(self.url, timeout=600.0).text
        soup = BeautifulSoup(html, "html.parser")
        body = soup.body
        assert body is not None
        pre = body.pre
        assert pre is not None

        result: dict[str, FtpPath] = {}
        children = iter(pre.children)
        try:
            while True:
                a = next(children)
                assert isinstance(a, Tag) and (a.name == "a"), a
                href = a.attrs["href"]
                assert href
                text = next(children)
                assert isinstance(text, NavigableString)

                if href == "../":
                    continue

                match = LS_LINE_RE.fullmatch(text)
                assert match
                modified_str = match[1]
                size_str = match[4]

                path_str = self.path_str + href
                modified = dt.datetime.strptime(modified_str, LS_TIMESTAMP_FORMAT)
                modified = modified.replace(tzinfo=dt.timezone.utc)
                assert is_utc_datetime(modified), modified

                if size_str is None:
                    result[href] = FtpDir(path_str, modified)
                else:
                    size = int(size_str)
                    result[href] = FtpFile(path_str, modified, size)
        except StopIteration:
            pass

        return result

    def as_dir(self) -> FtpDir:
        return self

    def as_file(self) -> FtpFile:
        raise AssertionError(f"{self!r} is not a file.")

    def __repr__(self) -> str:
        return f"compreq.pythonftp.FtpDir({self.path_str!r}, {self.modified!r})"


class FtpFile(FtpPath):
    def __init__(self, path_str: str, modified: UtcDatetime, size: int) -> None:
        super().__init__(path_str, modified)
        assert not path_str.endswith("/"), path_str

        self.size = size

    def read_text(self) -> str:
        return requests.get(self.url, timeout=600.0).text

    def read_bytes(self) -> bytes:
        return requests.get(self.url, timeout=600.0).content

    def as_dir(self) -> FtpDir:
        raise AssertionError(f"{self!r} is not a directory.")

    def as_file(self) -> FtpFile:
        return self

    def __repr__(self) -> str:
        return f"compreq.pythonftp.FtpFile({self.path_str!r}, {self.modified!r}, {self.size!r})"


ROOT = FtpDir("/", utc_now())
