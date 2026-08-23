# Dev plugins folder

Local checkouts of `mongo-x-ray-*` plugins can live here during development.
`discover_plugins()` prefers a plugin found in this folder over the same
plugin installed as an entry point, so all components can be developed and
tested from the core checkout alone (e.g. symlink each plugin repository in):

```sh
# from the core repository root, with the plugin repos as siblings
ln -s ../../mongo-x-ray-ftdc plugins/mongo-x-ray-ftdc
ln -s ../../mongo-x-ray-hc  plugins/mongo-x-ray-hc
ln -s ../../mongo-x-ray-log plugins/mongo-x-ray-log
ln -s ../../mongo-x-ray-gmd plugins/mongo-x-ray-gmd
```

Each entry must be a directory (or symlink to one) that contains a `src/`
folder with a `mongo_x_ray_*` import package exposing a `plugin.py` that
defines the `Plugin` subclass. Plugins not present here fall back to the
installed `mongo_x_ray.plugins` entry points.
