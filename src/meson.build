notepad_sources = [
  '__init__.py',
  'app.py',
  'window.py',
  'tab_bar.py',
  'editor_tab.py',
  'find_replace.py',
  'goto_dialog.py',
  'settings_dialog.py',
]

install_data(
  notepad_sources,
  install_dir: pythondir / 'notepad'
)

bin_conf = configuration_data()
bin_conf.set('PYTHON', python_bin.full_path())
bin_conf.set('pkgdatadir', pkgdatadir)
bin_conf.set('pkglibdir', pythondir)

configure_file(
  input: 'notepad.in',
  output: 'notepad',
  configuration: bin_conf,
  install: true,
  install_dir: bindir,
  install_mode: 'rwxr-xr-x'
)
