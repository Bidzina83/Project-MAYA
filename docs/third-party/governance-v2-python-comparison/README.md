# Python Comparison - Third-Party Notices

Prepared on 2026-10-17 for the Python-only Gate A comparison, not the complete
Maya product or a new runtime release. Carry this folder alongside the reviewed
test kit as `notices/`. Do not insert it into the frozen reproduction or change
the reproduction manifest. The runtime, helper and reference executable bytes
are unchanged. Creating these notices authorizes no upload or VM execution.

## Original Notices

| File | Applies To | Origin |
| --- | --- | --- |
| PYTHON-WINDOWS-LICENSE.txt | CPython 3.13.14 Windows build, historical Python licences, Microsoft binary-build conditions, bzip2, libffi, OpenSSL Apache terms, Tcl/Tk | Original LICENSE.txt from the installed distribution matching all 796 frozen Python files |
| PYTHON-INCORPORATED-NOTICES.rst | Python's additional incorporated-code acknowledgements and licence texts, including mathematical, hashing, XML, compression and decimal components | CPython v3.13.14, Doc/license.rst; preserved as readable original reStructuredText |
| MICROSOFT-SANDBOX-SECURITY-TOOLS-LICENSE.txt | Unmodified Microsoft LaunchAppContainer reference launcher | Original MIT notice at pinned commit 8102bfc8dc3e244ec08e8204bd7d989e26a016e4 |
| OPENSSL-LICENSE.txt | OpenSSL 3.0.21, libssl-3.dll and libcrypto-3.dll | OpenSSL openssl-3.0.21, LICENSE.txt |
| EXPAT-COPYING.txt | Expat incorporated into pyexpat.pyd | CPython v3.13.14, Modules/expat/COPYING |
| ZLIB-LICENSE.txt | zlib 1.3.1, zlib1.dll | CPython source-deps zlib-1.3.1, LICENSE |
| LIBMPDEC-COPYRIGHT.txt | libmpdec 4.0.0 incorporated into _decimal.pyd | CPython source-deps mpdecimal-4.0.0, COPYRIGHT.txt |
| XZ-COPYING.txt | liblzma 5.2.5 incorporated into _lzma.pyd | CPython source-deps xz-5.2.5, COPYING; the XZ command-line programs are not included |
| TK-LICENSE.txt | Tk 8.6.15, tk86t.dll and _tkinter.pyd | Original installed tk8.6/license.terms; Python's Windows licence also contains Tcl/Tk notices |

Source URLs, SHA256 values, sizes, component versions and runtime bindings are
recorded in `notices-manifest.json`. Versions from Windows file metadata or
CPython's pinned build properties are distinguished from executed version probes;
no bundled Python was executed. All upstream notice bytes are preserved, including
line endings. These files are third-party terms, not a relicensing of Maya.

## Scope And Limits

The diagnostic kit is a selected copy of the existing Python distribution, not
a rebuilt or upgraded Python. No Python source, extension or runtime DLL has
been modified for this notice collection. The Maya diagnostic probe and launcher
are separate from Python; the Microsoft reference source is unmodified.

Python's Windows licence contains the conditions for its Microsoft Distributable
Code; retain them with the vcruntime140*.dll files. The Microsoft reference MIT
notice does not replace applicable Microsoft compiler/runtime redistribution
conditions for its statically linked CRT. This folder is a notice collection,
not certification that all packaging, toolchain, end-user terms or redistribution
obligations have been satisfied. Those remain part of transfer/release review.
It also does not grant or establish Windows client/Azure licensing rights.

SQLite 3.50.4 is present as sqlite3.dll. Its upstream public-domain explanation is
at https://www.sqlite.org/copyright.html; do not invent a new SQLite licence or
relabel the DLL as Maya-owned. Python's own incorporated-code document is retained
in full rather than claiming that its illustrative list is exhaustive. Embedded
source notices in copied standard-library modules remain in those original files.

The frozen Python distribution also contains the unopened bootstrap wheel
`Lib/ensurepip/_bundled/pip-26.1.2-py3-none-any.whl`. It retains 42 embedded
licence/copyright/authors files, including pip's licence and its vendored-library
notices. Its wheel hash and selected notice hashes are recorded separately under
`embedded_notices` in the manifest. The wheel is not an installed pip environment
or permission to bootstrap packages. Preserve it verbatim inside the frozen base;
do not remove it to make the inventory match an earlier description.

The .NET Framework and Windows system components used by the observer already
belong to the guest and are not redistributed in this sidecar. Hermes, installed
site-packages, LibreOffice, Metabase, embeddings and other Maya installer
dependencies are not part of this Python-only kit and are not covered here.

Keep the original binary/manifest fingerprints and the separate permission gates
in `docs/architecture/governance_v2_python_azure_procedure.md`. This directory is
not an execution manifest, approved transfer destination or product qualification.
