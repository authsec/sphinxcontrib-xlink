# sphinxcontrib-xlink (DEPRECATED)

> **This project has been renamed to [`doxtr-xlink`](https://pypi.org/project/doxtr-xlink/).**
>
> `sphinxcontrib-xlink` is no longer maintained. The final release (`1.3.2`) is a
> tombstone that contains no functionality. Importing it or enabling it as a
> Sphinx extension raises an error with migration instructions.

## Migrate

```bash
pip uninstall sphinxcontrib-xlink
pip install doxtr-xlink
```

Then update your `conf.py`:

```python
extensions = [
    'doxtr_xlink',   # was: 'sphinxcontrib.xlink'
]
```

Everything else (`.xlink` files, directives, roles, config options) works the
same under the new package. See the
[doxtr-xlink documentation](https://github.com/doxtr/doxtr-xlink#readme) for details.
