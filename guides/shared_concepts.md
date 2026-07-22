# Shared Godot Authoring Concepts (Godot 4.7)

This guide contains rules shared by the `.tscn`, `.tres`, GDScript,
`.gdshader`, physics, and server authoring guides. Read it when a task crosses
formats or when a guide refers to shared ownership, timing, identifiers,
coordinate spaces, or validation rules.

It does not replace a format-specific guide. Use the specialized guide for
exact grammar, properties, method signatures, shader built-ins, body classes,
or server APIs.

## 1. Project and version authority

These guides target Godot 4.7, but a generated artifact still depends on the
target project. Always verify project-specific facts instead of guessing:

- the exact Godot version and feature tags;
- custom classes and `class_name` registrations;
- node names and scene paths;
- resource paths and resource types;
- input actions and project settings;
- collision-layer names and bit assignments;
- global shader parameters;
- renderer and physics backend;
- imported asset structure and generated resources.

Names are not evidence that an API exists. Do not infer a property, method,
signal, enum, callback signature, uniform, or node path from a naming pattern.
When `GODOT_DOCS_ROOT` points to a version-matched Godot documentation
checkout, check the relevant lowercase class file under
`$GODOT_DOCS_ROOT/classes`. Otherwise, check existing project code or generated
resource output and validate uncertain APIs with the target executable.

An artifact can be syntactically valid and still fail because it refers to a
class, path, property, signal, resource, or project setting that does not
exist.

### Evidence hierarchy

Use different authorities for different facts:

- For engine syntax and APIs covered by this guide set, prefer the target Godot
  executable and these versioned guides over project examples or model memory.
- For exact class members, signatures, inheritance, enums, and constants, use
  the version-matched class `.rst` files under
  `$GODOT_DOCS_ROOT/classes` when available.
- For project structure and conventions, prefer `project.godot`, project code,
  tests, and generated project artifacts over generic examples.
- For exhaustive class members outside this guide set, inspect target-project
  usage or verify a minimal candidate with Godot.
- Do not assume that a named API exists in every Godot 4 release.

Inspect `project.godot` feature tags, renderer and physics settings, CI,
export presets, and project documentation. `config_version` alone is not the
Godot engine version. If the target is not 4.7, re-check every version-sensitive
annotation, property, method, serialization field, shader built-in, and backend
default.

The guides remain usable without `GODOT_DOCS_ROOT`. Search this directory
before loading unrelated files, and combine only the format and subsystem
guides required by the task. When neither the external class reference,
guides, project, nor target engine establish a fact, preserve the uncertainty
instead of filling the gap from memory.

### Authoring surface and generated files

Prefer ordinary nodes and resources over low-level servers unless the
requirement needs direct RID control. Prefer simple hand-authored `.tscn` and
`.tres` structures over fabricated complex packed data. For meshes, imported
animations, tile data, and other generated structures, use the target Godot
version or `ResourceSaver` to produce a canonical example.

Do not treat `.godot/` cache and imported output as source files. Change the
source asset or import settings instead. Preserve engine-managed metadata in
existing files unless the target engine regenerates it.

Godot 4.4 and later generate `.uid` sidecars for scripts and shaders. Commit
these files, move them with the source file, and let Godot generate their
contents. Do not copy an example sidecar or create a UID by guessing.

When editing an existing project, make the smallest coherent change. Preserve
unrelated properties, resource IDs, node IDs, comments in source formats that
retain them, and project conventions. Do not rewrite an entire generated file
when a targeted edit is sufficient.

## 2. Types, values, and Variant boundaries

Godot systems exchange typed values even when the API surface uses `Variant`.
The consuming property or method determines the required type.

Keep these distinctions explicit:

- `String` is not `StringName`;
- `String` is not `NodePath`;
- `Vector2` is not `Vector3`;
- `Transform2D` is not `Transform3D`;
- a resource object is not its server `RID`;
- an object instance ID is not an object reference;
- a filesystem path is not a scene node path;
- a shader uniform type is not inferred safely from its name.

When serializing or passing a value:

1. identify the exact consuming property, method, or uniform;
2. use the documented type and value shape;
3. preserve the dimension, coordinate space, and units;
4. do not substitute JSON, arbitrary dictionaries, or stringly typed values
   for Godot's documented Variant representation.

Arrays, packed arrays, dictionaries, mesh channels, shader uniforms, and
server payloads have specific element types and length rules. A container that
looks structurally plausible can still be rejected or interpreted incorrectly.

## 3. Shared resources and mutation

Godot resources are commonly reference-counted and shared. Multiple nodes,
scenes, materials, shapes, meshes, or server users can refer to the same
resource.

Assume a resource is shared unless the relevant guide explicitly says
otherwise. Mutating it can change every user:

```gdscript
var shared_material: Material = load("res://materials/shared.tres")
var local_material := shared_material.duplicate()
```

Use duplication, a unique resource, or `resource_local_to_scene` when each
scene instance needs independent mutable state. The `.tres` guide defines the
serialization and local-to-scene rules; physics and rendering guides define
their subsystem-specific consequences.

A server `RID` does not necessarily keep a reference-counted source resource
alive. Keep a strong reference to resources whose RIDs are in use. This
applies to shape, mesh, texture, material, and other server-backed resources.

Do not free or mutate a resource that another node, scene, or server object
still expects to remain valid.

## 4. Identifiers and ownership

Godot uses several unrelated identifier kinds:

| Identifier | Meaning |
|---|---|
| Filesystem path | Project file location, usually beginning with `res://`. |
| Resource UID | Stable identity used by resource loading and serialization. |
| UID sidecar | Engine-generated `file.ext.uid` identity for scripts and shaders. |
| `.tscn`/`.tres` local ID | File-local reference such as `ExtResource("x")` or `SubResource("x")`. |
| Scene `NodePath` | Path from one scene node to another. |
| `RID` | Runtime handle owned by a low-level server. |
| Object/instance ID | Numeric identity associated with an engine object. |

Never substitute one identifier kind for another. In particular:

- a `.tscn` local resource ID is not a UID or filesystem path;
- a `.uid` sidecar is not an import cache and must travel with its source;
- a server RID is not a serializable asset identity;
- an object ID does not keep the object alive;
- a `NodePath` is not a filesystem path;
- a resource path does not identify a child node.

### Server RID ownership

Server-created objects must have an explicit owner and cleanup path. Store
every RID that the system creates, keep required source resources alive, and
free dependent objects before their dependencies:

```text
instance/body/area/joint
        |
        v
material/shape/mesh/texture/shader
        |
        v
server-created canvas/scenario/space when applicable
```

Use the matching server's `free_rid()` method. Never free a world-, viewport-,
node-, or resource-owned RID unless the owning API explicitly transfers
ownership to your system.

The PhysicsServer and RenderingServer guides add their dimension- or
renderer-specific ownership rules, callback cleanup requirements, and
world-owned RID details.

## 5. Timing and synchronization

Timing is part of correctness, not merely performance:

- use `_physics_process()` for physics-dependent movement, forces, and direct
  physics-space queries;
- use `_process()` for render-frame logic that does not modify physics state;
- use documented physics integration/state callbacks for direct server state;
- use render-thread callbacks only when the rendering API requires them;
- do not retain direct state objects beyond their documented callback lifetime.

Physics state can be locked while the server simulates. Direct-space queries
must run at safe physics timing.

RenderingServer commands may be queued for the rendering thread. A setter
returning does not mean that the GPU has completed the work. A getter may force
synchronization and stall the rendering or physics server. Maintain
authoritative values in your own data when possible instead of polling server
getters every frame.

Physics and rendering interpolation are synchronization systems, not physics
or transform replacements. When creating a visual object at runtime from
physics-driven code, initialize the appropriate interpolation state so the
first rendered frame does not appear to teleport.

## 6. Coordinate spaces, transforms, and units

Before constructing a vector, transform, query, property, or shader value,
identify:

1. the dimension: 2D or 3D;
2. the coordinate space: local, parent, canvas, viewport, world, camera, mesh,
   bone, particle, or shader-stage space;
3. the direction convention and handedness;
4. the units and scale;
5. whether the value is a point, direction, normal, velocity, or transform.

Common mistakes include:

- applying a local transform where a world transform is required;
- using a node-space query with world-space coordinates;
- treating a normal like a position;
- mixing `Transform2D` and `Transform3D`;
- assuming screen, canvas, world, and clip coordinates are interchangeable;
- applying `delta` twice to a velocity or motion value;
- using a shader built-in without checking its stage-specific coordinate space.

The shader guide documents built-in coordinate spaces. The 2D/3D physics and
RenderingServer guides document their transform and query spaces. This guide
defines the shared discipline; those guides define the exact APIs.

## 7. Cross-artifact dependency order

When a feature spans multiple files, generate and validate dependencies in this
direction:

```text
project settings and imported assets
            |
            v
GDScript / gdshader declarations
            |
            v
.tres resources and sub-resources
            |
            v
.tscn nodes, properties, instances, and connections
            |
            v
runtime physics/rendering server objects
```

The order means:

- a declared shader uniform must exist before a material sets it;
- a resource must exist before a scene property references it;
- a script must parse and inherit the intended class before a scene attaches it;
- a node path must match the final serialized tree;
- a runtime RID must be created only after its source data and dependencies are
  available.

Server-created runtime state should normally be recreated from serialized
resources or configuration. Do not persist opaque RIDs as stable asset IDs.

## 8. Validation ladder

Validation has distinct levels. Passing an earlier level does not imply that a
later level passes:

1. **Text structure:** delimiters, sections, indentation, IDs, and references
   are internally consistent.
2. **Engine parse/import:** the target Godot version parses scripts and shaders,
   imports assets, and recognizes serialized classes and properties.
3. **Load/instantiate:** scenes and resources load, scripts attach to compatible
   objects, and node/resource paths resolve.
4. **Runtime behavior:** lifecycle timing, signals, physics, rendering,
   ownership, and cleanup behave as intended.
5. **Project behavior:** existing tests, scenes, exports, and performance
   expectations still pass.

Use the target project's existing validation commands. A headless editor launch
can expose many parse, import, and shader errors, but it may also execute editor
plugins and `@tool` scripts. Run it in a controlled worktree and inspect any
generated changes.

If a validation level cannot be run, state that limitation. Do not present text
inspection as proof that the target engine loaded or executed the artifact.

## 9. Shared validation checklist

Use this checklist before relying on a generated artifact:

### Project and identity

- The target Godot version and renderer/backend are known.
- Project-specific classes, paths, settings, actions, and layers were verified.
- Filesystem paths, UIDs, local IDs, node paths, RIDs, and object IDs are not
  being confused.
- Script and shader `.uid` sidecars are preserved and version-controlled.
- Generated import/cache output is not being edited as project source.
- No API was invented from a name pattern.

### Values and types

- Every property, method argument, uniform, array slot, and resource value has
  the documented type.
- 2D/3D values, transforms, coordinate spaces, and units are intentional.
- Packed arrays and dictionaries have the required element types and lengths.
- Godot Variant syntax is used at serialization boundaries.

### Ownership and lifetime

- Shared resources are not mutated unintentionally.
- Resources remain referenced while server RIDs use them.
- Runtime server objects have explicit owners and cleanup paths.
- Dependent objects are freed before their dependencies.
- World-, node-, viewport-, and resource-owned objects are not freed by code
  that does not own them.

### Timing and synchronization

- Physics changes and direct physics queries run at physics-safe timing.
- Rendering-thread work is isolated to documented render-thread APIs.
- Expensive server getters are not used as ordinary per-frame polling.
- Direct state objects are not retained beyond their valid callback.
- Runtime-created physics-driven visuals initialize interpolation correctly.

### Final integration

- Each specialized guide's format-, dimension-, shader-, or server-specific
  checklist also passes.
- Validation claims identify the highest level that actually ran.
- The final files are reviewed together as one dependency graph.
- The smallest valid artifact works before optional complexity is added.
