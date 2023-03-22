from contextlib import redirect_stderr, redirect_stdout
from doctest import run_docstring_examples
from io import StringIO


class DocTestInUnitTestMixin:
    def doctest_object(self, *args, **kwargs):
        out = StringIO()
        with redirect_stdout(out), redirect_stderr(out):
            run_docstring_examples(*args, **kwargs)
        output = out.getvalue()
        self.assertFalse(bool(output), output)
