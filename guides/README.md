# Godot 4.7 Standalone Authoring Bundle

Copy this entire directory into a Godot project. It contains:

- the Godot 4.7 authoring guides;
- rules for reading the Godot 4.7 class reference from a documentation
  checkout configured by `GODOT_DOCS_ROOT`;
- fallback rules for projects where that checkout is unavailable.

The authoring guides remain usable on their own when `GODOT_DOCS_ROOT` is not set.

## AI reading order

1. Read [`index.md`](index.md).
2. Read [`shared_concepts.md`](shared_concepts.md) when the task crosses
   formats or subsystems.
3. Read only the specialized authoring guides required by the task.
4. Resolve the documentation from `GODOT_DOCS_ROOT/classes/`.
5. When it contains a version-matched reference, open only the relevant class
   files and inherited parents.
6. When the variable is unset or the checkout is absent, or incomplete, use the authoring guides, target project, and target Godot
   executable.
7. Verify project-specific paths, classes, settings, actions, and node names
   from the target project.

The external class reference is an enhancement, not a prerequisite. Its
absence must not cause the model to ignore these guides.

## Class file routing

Class filenames are lowercase. Resolve them relative to
`GODOT_DOCS_ROOT/classes`:

```text
Node                       -> $GODOT_DOCS_ROOT/classes/class_node.rst
CharacterBody2D            -> $GODOT_DOCS_ROOT/classes/class_characterbody2d.rst
PhysicsDirectSpaceState3D  -> $GODOT_DOCS_ROOT/classes/class_physicsdirectspacestate3d.rst
@GDScript                  -> $GODOT_DOCS_ROOT/classes/class_@gdscript.rst
@GlobalScope               -> $GODOT_DOCS_ROOT/classes/class_@globalscope.rst
```

Use the class reference for exact methods, properties, signals, enums,
constants, parameter types, return types, inheritance, and version-specific
notes. Use the authoring guides for workflow, ownership, serialization,
timing, integration, and failure-prevention rules.

If no matching class file exists, search the guides and existing project code,
then validate the smallest candidate with Godot. If the fact still cannot be
established, state the uncertainty rather than inventing a member.

## Version rule

This bundle targets Godot 4.7. Do not silently use it for another engine version or combine it with a `GODOT_DOCS_ROOT` checkout for another snapshot.
