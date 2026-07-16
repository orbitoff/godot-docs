# Optional Godot 4.7 Class Reference Cache

This directory is intentionally small in Git. A project setup step may populate
it locally with the generated Godot 4.7 class reference after cloning.

The authoring guides do not require this cache. A developer may omit it
intentionally, or it may be missing because project setup was not run.

## Model behavior

1. Read [`VERSION`](VERSION).
2. Check whether `class_*.rst` files are present.
3. Use them only when the version is 4.7 and the requested file exists.
4. Read only the requested class and inherited parents.
5. If files are absent, partial, or wrong-version, fall back to the authoring
   guides, target project, and target Godot executable.
6. Never fill a missing class entry with a remembered or guessed API.

When populated, use filename search for classes and text search for members:

```text
class_<lowercase class name>.rst
```

Do not assume a method is declared directly on the leaf class, and do not load
the entire directory into one model context.

## Local generation

Populate this directory from the `classes` directory of a version-matched
Godot 4.7 documentation checkout. For example:

```powershell
Copy-Item "$env:GODOT_DOCS_ROOT\classes\*.rst" `
  ".\godot-authoring-guides\class_reference\"
```

```sh
cp "$GODOT_DOCS_ROOT"/classes/*.rst \
  ./godot-authoring-guides/class_reference/
```

Projects can automate this in their own bootstrap or agent setup. Do not copy
class files from `stable`, `latest`, or another version without confirming
that the snapshot is Godot 4.7.

The files retain Godot's generated reStructuredText markup. Links to narrative
tutorials may point outside this standalone bundle, but class declarations,
signatures, inheritance, descriptions, and version-specific notes are present
locally.

The class reference is derived from the Godot Engine source and distributed
under the MIT license in [`LICENSE.txt`](LICENSE.txt).

