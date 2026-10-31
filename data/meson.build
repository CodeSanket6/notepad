# Desktop file
configure_file(
  input: 'io.github.CodeSanket6.notepad.desktop.in',
  output: 'io.github.CodeSanket6.notepad.desktop',
  copy: true,
  install: true,
  install_dir: datadir / 'applications'
)

# Appstream metainfo
configure_file(
  input: 'io.github.CodeSanket6.notepad.metainfo.xml.in',
  output: 'io.github.CodeSanket6.notepad.metainfo.xml',
  copy: true,
  install: true,
  install_dir: datadir / 'metainfo'
)

# Icons
foreach size : ['16x16', '24x24', '32x32', '48x48', '64x64', '128x128', '256x256', '512x512']
  install_data(
    'icons' / 'hicolor' / size / 'apps' / 'io.github.CodeSanket6.notepad.png',
    install_dir: datadir / 'icons' / 'hicolor' / size / 'apps'
  )
endforeach

# Styles
install_data(
  'styles' / 'fluent.css',
  install_dir: pkgdatadir / 'styles'
)
