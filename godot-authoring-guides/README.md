# Godot 4.7 Standalone Authoring Bundle

Copy this entire directory into a Godot project. It contains:

- the Godot 4.7 authoring guides;
- an optional location for a locally generated Godot 4.7 class reference;
- fallback rules for projects where the class reference is not generated.

The class reference payload is intentionally excluded from Git to keep project
repositories small. The authoring guides remain usable on their own.

## AI reading order

1. Read [`index.md`](index.md).
2. Read [`shared_concepts.md`](shared_concepts.md) when the task crosses
   formats or subsystems.
3. Read only the specialized authoring guides required by the task.
4. Check whether [`class_reference/`](class_reference/README.md) contains a
   generated Godot 4.7 reference.
5. When it is present, open only the relevant class files and inherited
   parents.
6. When it is absent, incomplete, or for another version, ignore it and use
   the authoring guides, target project, and target Godot executable.
7. Verify project-specific paths, classes, settings, actions, and node names
   from the target project.

The optional class cache is an enhancement, not a prerequisite. Its absence
must not cause the model to ignore these guides or substitute guessed APIs.

## Class file routing

When generated, class filenames are lowercase:

```text
Node                       -> class_reference/class_node.rst
CharacterBody2D            -> class_reference/class_characterbody2d.rst
PhysicsDirectSpaceState3D  -> class_reference/class_physicsdirectspacestate3d.rst
@GDScript                  -> class_reference/class_@gdscript.rst
@GlobalScope               -> class_reference/class_@globalscope.rst
```

Use the class reference for exact methods, properties, signals, enums,
constants, parameter types, return types, inheritance, and version-specific
notes. Use the authoring guides for workflow, ownership, serialization,
timing, integration, and failure-prevention rules.

If no matching class file exists, search the guides and existing project code,
then validate the smallest candidate with Godot. If the fact still cannot be
established, state the uncertainty rather than inventing a member.

## Version rule

This bundle targets Godot 4.7. Do not silently use it for another engine
version or mix it with class files from another snapshot. Replace the complete
bundle when the target project's Godot version changes.
