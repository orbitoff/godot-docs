# Godot 4.7 General Physics Authoring Guide

This guide defines physics concepts shared by Godot 4.7 2D and 3D projects.
Use it together with `physics_2d.md` or
`physics_3d.md`. Dimension-specific node names, vectors,
shapes, and APIs are intentionally kept in those guides so the three guides
do not duplicate one another.

Read [`shared_concepts.md`](shared_concepts.md) for
cross-format rules about project assumptions, resource ownership, identifiers,
timing, coordinate spaces, and general validation.

## 1. Physics model

Godot physics separates:

- **collision detection**: determining whether shapes intersect or contact;
- **collision response**: deciding how bodies move or react after contact;
- **overlap detection**: observing objects inside a region without making them
  physically push one another;
- **physics queries**: asking the physics space what a ray, shape, or point
  would intersect.

Physics bodies are nodes backed by a physics server. The scene tree is the
high-level representation; the server owns the low-level collision state.
Physics state should be read and changed at physics timing, not arbitrarily
during rendering callbacks.

Godot physics is not guaranteed to be deterministic across runs, machines,
physics backends, frame schedules, or floating-point environments. Do not
assume identical inputs produce bit-for-bit identical simulation results.

## 2. Physics timing

`_physics_process(delta)` runs before a physics step at the configured fixed
physics rate. For the general timing and synchronization rules, read the
shared concepts guide. Physics-specific use is:

- body movement;
- forces and impulses that are part of gameplay;
- direct-space queries;
- reading collision results;
- updating physics-dependent state.

`delta` is elapsed physics time in seconds. Always use it for time-based
movement or acceleration instead of assuming a fixed numeric value.

`_process(delta)` is render-frame timing and is not the correct place for
physics movement or direct-space queries. Visual interpolation can make
physics-driven motion appear smooth, but it does not turn render-frame code
into deterministic physics.

The default physics tick rate is commonly 60 ticks per second, but it is a
project setting. Increasing `physics/common/physics_ticks_per_second` can
improve fast-object and stack stability at higher CPU cost. Excessive physics
work can cause a physics spiral of death; do not raise the rate without
profiling.

## 3. Collision object families

The same conceptual families exist in 2D and 3D:

| Family | Purpose |
| --- | --- |
| `Area` | Detects overlaps and can override local gravity/damping and audio behavior. It does not provide solid body response by itself. |
| `StaticBody` | Immovable environment or obstacle. It participates in collision but is not moved by simulation. |
| `AnimatableBody` | A body moved by animation or script that conveys its motion to colliding bodies. Prefer it for moving platforms that do not need character-body logic. |
| `RigidBody` | Fully simulated body. The physics engine computes movement, rotation, contacts, and response from forces, impulses, mass, damping, and constraints. |
| `CharacterBody` | Script-controlled body. The engine detects collisions and supplies movement helpers, but gameplay code computes gravity, velocity, and desired motion. |
| `RayCast` | Persistent first-hit ray query updated each physics frame. |
| `ShapeCast` | Persistent swept-shape query for detecting objects along a motion path. |

The exact class names and APIs for each family are dimension-specific and are
defined only in the 2D and 3D guides.

Choose the smallest family matching the behavior. Do not use a `RigidBody` for
an object that must be positioned directly every frame, and do not use a
`CharacterBody` when the engine should simulate the object's response.

## 4. Collision shapes

Every collision body or area needs one or more collision shapes to participate
in shape-based collision detection. A typical scene uses one or more direct
`CollisionShape` children whose `shape` property references a `Shape` resource.

Important rules:

- A `CollisionShape` must have a non-null shape resource.
- Collision shape nodes must be direct children of the collision object.
- Indirect descendants are not automatically used as that object's shapes.
- Multiple shapes on one object do not collide with one another.
- Primitive shapes are generally the best choice for dynamic bodies.
- Concave/trimesh shapes are intended for static geometry and are not suitable
  for ordinary dynamic bodies.
- Keep collision geometry simpler than visual geometry when small details do
  not affect gameplay.

Collision shape resources follow the shared-resource ownership rules in
[`shared_concepts.md`](shared_concepts.md). Make a shape
unique or duplicate it before per-object mutation.

Avoid scaling physics bodies or collision shapes. Use the shape resource's
dimensions and keep the collision object's scale uniform. Non-uniform scaling
can produce incorrect or unstable collision behavior.

## 5. Collision layers and masks

Each collision object has a 32-bit `collision_layer` and 32-bit
`collision_mask`.

- `collision_layer` says which layers the object belongs to.
- `collision_mask` says which layers the object scans for interaction.

Layers are not object categories stored by name; they are bits in an integer.
Layer 1 corresponds to bit 0, layer 2 to bit 1, and so on:

```gdscript
var layer_1 := 1 << 0
var layer_3 := 1 << 2
var layers_1_and_3 := layer_1 | layer_3
```

An object can only detect or collide with another object when the relevant
layer/mask relationship allows it. Do not assume that two objects interact
merely because their visual nodes overlap.

Use Project Settings layer names to document the project-wide meaning of bits.
Keep a stable layer plan, for example:

| Layer | Meaning |
| --- | --- |
| 1 | World |
| 2 | Player |
| 3 | Enemies |
| 4 | Projectiles |
| 5 | Triggers |

The actual names and assignments are project decisions. Generated code must
match the target project's layer plan rather than inventing action or layer
names.

Ray and shape queries also use collision masks. A query can additionally
exclude specific objects/RIDs, and persistent ray/shape nodes can choose
whether to detect areas and/or bodies.

## 6. Areas and overlap monitoring

An area defines a region for detecting other collision objects. It can:

- emit entered/exited signals;
- report currently overlapping bodies or areas;
- override gravity and damping in its region;
- route audio through a configured bus in supported dimensions.

`monitoring` controls whether the area tracks overlaps and emits monitoring
signals. `monitorable` controls whether other areas can detect this area.
Overlap methods and signals require the corresponding monitoring behavior to be
enabled.

Do not treat an area overlap as a physical collision. An area does not stop a
body, push it, or provide a solid surface merely because it overlaps.

Area signal timing is physics-related. Connect handlers with the exact signal
signature and avoid assuming that an object remains valid after it exits or is
freed.

## 7. Physics materials

A physics material controls contact response properties such as:

- friction;
- bounce;
- roughness/absorption behavior where supported.

A material affects the bodies/shapes using it according to the dimension's
physics backend and material-combine rules. It does not change collision
layers, shape geometry, or overlap monitoring.

Use a dedicated material when behavior must differ per object. Remember that
resource sharing and duplication follow the rules in
[`shared_concepts.md`](shared_concepts.md).

## 8. Movement semantics

There are three fundamentally different movement strategies:

1. **Script-controlled movement**: compute desired velocity and call the
   dimension-specific character movement API during `_physics_process()`.
2. **Physics simulation**: apply forces/impulses or modify the rigid body's
   physics state through its integration callback.
3. **Kinematic collision response**: move by a requested motion and inspect a
   returned collision, implementing custom response such as reflection.

Do not mix direct transform assignment with active rigid-body simulation every
physics tick. Teleporting or repeatedly setting a rigid body's transform or
velocity can fight the solver and produce unpredictable behavior.

For teleporting a simulated body intentionally, pause/freeze or otherwise
follow the dimension-specific API and then restore simulation state as needed.

## 9. Queries and physics space

The active world exposes a direct physics space state. Direct-space queries
are safe during `_physics_process()` when the physics space is available and
unlocked. Querying it from arbitrary callbacks can fail because the physics
space may be locked while the server is simulating.

Common query types:

- ray intersection;
- point intersection;
- shape intersection;
- motion/sweep testing;
- collision-point and normal queries.

Query coordinates are world coordinates unless the API explicitly says
otherwise. Convert local positions using the node's global transform before
building a query.

Typical ray result data includes:

- hit position;
- surface normal;
- collider object;
- collider object ID;
- collider RID;
- hit shape index;
- collider metadata.

An empty result means no hit. Always check the result before reading fields.
Use an exclusion list to avoid self-hits and a collision mask to filter broad
categories. Exclusions can generally contain collision objects or RIDs.

## 10. Persistent ray and shape casts

Persistent cast nodes cache their result for the current physics frame:

- configure their target/motion, mask, and area/body filters;
- read their result during or after the physics update;
- call `force_raycast_update()` when an immediate recalculation is required.

A ray returns the closest object along its path. A shape cast sweeps a shape
and can detect multiple objects or collisions depending on its API and
configuration. Use a direct-space query when a one-off query needs custom
parameters or must run several times in one physics frame.

## 11. Rigid-body force semantics

For simulated bodies:

- a **force** acts over time and should normally be applied each physics step;
- an **impulse** changes momentum immediately and is normally applied once;
- a **central** force/impulse does not add torque;
- an off-center force/impulse can change angular motion;
- mass, inertia, damping, gravity scale, and sleeping affect the result.

Use `_integrate_forces(state)` when direct access to the physics state is
required. Enable a custom integrator only when intentionally replacing or
augmenting the default integration behavior.

Do not call a transform-facing `look_at()` or set the transform every frame on
an active rigid body. Convert the desired behavior into forces, impulses,
angular velocity, or integration-state changes.

Contact monitoring on rigid bodies is not automatic for all contact signals.
Enable contact monitoring and set a sufficient maximum contact count when the
project needs body-entered/exited reporting.

## 12. Constraints and joints

Joints constrain two bodies or a body and a fixed point. They are not a
replacement for collision layers or collision shapes.

General joint rules:

- both connected bodies must exist at the expected paths or RIDs;
- anchors and axes use the dimension's coordinate system;
- joint limits and softness are solver parameters, not visual transforms;
- joint collision exceptions should be configured when connected bodies must
  not collide with each other;
- unstable joint stacks often require better mass ratios, damping, solver
  settings, or simpler geometry.

Use the dimension-specific joint classes and serialized properties from the
target class reference.

## 13. Physics servers

The scene nodes are high-level wrappers around `PhysicsServer2D` or
`PhysicsServer3D`. Server-level APIs use RIDs and require explicit ownership,
shape creation, space assignment, and synchronization.

Use server APIs only when the node-level APIs cannot express the required
behavior. They are lower-level, easier to misuse, and may not interact with
scene-node monitoring signals exactly like ordinary nodes.

For complete low-level authoring details, use:

- [PhysicsServer2D authoring guide](servers/physics_server_2d.md)
- [PhysicsServer3D authoring guide](servers/physics_server_3d.md)

The dedicated guides document RID lifetime, spaces, server-created shapes,
bodies, areas, callbacks, direct queries, joints, cleanup, and
dimension-specific server methods. The 3D guide additionally covers axis
locks, soft bodies, rendering synchronization, and physics-backend caveats.

## 14. Performance and stability

Prefer:

- primitive shapes for moving bodies;
- simplified static level collision;
- fewer shapes per dynamic object;
- composite colliders for tiled surfaces where appropriate;
- collision masks that exclude irrelevant categories;
- direct queries instead of large numbers of permanent cast nodes when queries
  are sparse.

Common causes of instability:

- thin collision geometry;
- excessive shape complexity;
- non-uniform scaling;
- very large world coordinates;
- high-speed tunneling;
- unstable mass ratios or stacked bodies;
- physics work exceeding the available tick budget.

Continuous collision detection can reduce tunneling for fast rigid bodies.
Thicker static colliders, simpler geometry, and a higher physics tick rate can
also help, at increased CPU cost.

Physics is less reliable far from the world origin because floating-point
precision decreases. Large-world projects need an origin/world-coordinate
strategy rather than merely moving every node to huge coordinates.

## 15. Authoring workflow

1. Identify whether the object is detection-only, static, animated, simulated,
   or script-controlled.
2. Choose a collision layer/mask contract before adding nodes.
3. Choose simple collision shapes appropriate to the object's role.
4. Keep visual and collision nodes separate where scaling differs.
5. Implement physics changes in `_physics_process()` or the rigid integration
   callback.
6. Use signals for event-style overlap/contact notifications.
7. Use direct-space queries for one-off or highly customized tests.
8. Validate high-speed, stacked, sloped, thin, and edge-contact cases.
9. Profile shape count, query count, and physics tick cost.

## 16. Shared validation checklist

- The selected body family matches the intended control model.
- At least one valid collision shape exists where collision is required.
- Collision shape nodes are direct children of the collision object.
- Shape resources are compatible with the dimension and body role.
- Collision layers and masks match the project layer plan.
- Area monitoring/monitorable settings match the intended signals.
- Physics code runs in the correct callback.
- Rigid bodies are not transformed directly every frame.
- Direct-space queries run while the physics space is safe to access.
- Query coordinates and collision normals use the intended coordinate space.
- Self-exclusions and area/body filters are configured.
- Shared-resource ownership and duplication rules from
  `shared_concepts.md` are satisfied.
- Complex geometry is simplified where possible.
- Fast objects use an appropriate tunneling strategy.
- No assumption of deterministic simulation is made.

## 17. Source authority

This guide covers shared physics semantics. For exact properties, enum values,
signal signatures, and method names, use the Godot 4.7 class reference for the
target dimension-specific class and the matching dimension guide.
