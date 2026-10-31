project('notepad',
  version: '11.2607.14.0',
  meson_version: '>= 0.59.0',
  default_options: ['warning_level=2'],
)

python = import('python')
python_bin = python.find_installation('python3')

prefix = get_option('prefix')
bindir = prefix / get_option('bindir')
datadir = prefix / get_option('datadir')
pkgdatadir = datadir / meson.project_name()
pythondir = python_bin.get_install_dir()

app_id = 'io.ninja.notepad'

subdir('data')
subdir('src')

gnome = import('gnome')
gnome.post_install(
  glib_compile_schemas: false,
  gtk_update_icon_cache: true,
  update_desktop_database: true,
)
