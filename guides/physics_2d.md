# Godot 4.7 2D Physics Authoring Guide

This guide contains only 2D-specific physics information. Read
`physics.md` first for shared physics concepts such as timing,
body-family selection, collision layers/masks, areas, rigid-body semantics,
queries, physics materials, and performance.

Cross-format ownership, identifier, coordinate-space, and validation rules are
in [`shared_concepts.md`](shared_concepts.md).

## 1. 2D coordinate and class model

2D physics uses `Vector2`, `Transform2D`, and `Node2D`/`CanvasItem` coordinates.
The default 2D gravity direction is downward in screen coordinates:

```gdscript
var gravity := Vector2(0, 980)
```

The 2D collision class hierarchy is:

```text
CollisionObject2D
├── Area2D
└── PhysicsBody2D
    ├── StaticBody2D
    ├── AnimatableBody2D
    ├── CharacterBody2D
    └── RigidBody2D
```

`RayCast2D` and `ShapeCast2D` are query nodes, not collision bodies.

2D collision objects only collide inside the same `Viewport` canvas or
`CanvasLayer`. Behavior across different canvases is undefined; do not use
separate canvases as if they were one shared physics world.

## 2. 2D collision shape resources

Use these `Shape2D` resources:

| Shape | Use and constraints |
| --- | --- |
| `RectangleShape2D` | Axis-aligned in its local shape coordinates; useful for boxes, platforms, and UI-like rectangular bodies. |
| `CircleShape2D` | Uniform-radius shape; efficient for balls, radial triggers, and round projectiles. |
| `CapsuleShape2D` | Rounded elongated shape; useful for characters and moving bodies that should slide smoothly around corners. |
| `SegmentShape2D` | A line segment with no area; useful for edges, rays represented as shapes, and thin static geometry. |
| `SeparationRayShape2D` | Character-oriented ray shape that helps maintain separation from surfaces; it is not a general solid volume. |
| `WorldBoundaryShape2D` | Infinite half-plane boundary; use for world limits rather than finite geometry. |
| `ConvexPolygonShape2D` | Convex polygon; can represent custom convex geometry and is suitable for dynamic objects when kept reasonably simple. |
| `ConcavePolygonShape2D` | Arbitrary polygon/trimesh-like geometry; intended for `StaticBody2D`, not ordinary dynamic bodies. |

Primitive shapes are preferred for `RigidBody2D` and `CharacterBody2D`.
Concave shapes are the most flexible but slowest and should normally describe
static level geometry. A concave shape has no filled volume in the same sense
as a convex solid; do not use it as a dynamic character collider.

## 3. CollisionShape2D and CollisionPolygon2D

`CollisionShape2D` references one `Shape2D` resource:

```text
[node name="CollisionShape2D" type="CollisionShape2D" parent="Player"]
shape = SubResource("CapsuleShape2D_player")
```

`CollisionPolygon2D` creates collision from polygon points. Its build mode is:

- **Solids**: the polygon interior and contained area participate;
- **Segments**: only polygon edges participate.

Collision shapes must be direct children of the `CollisionObject2D`; a shape
under a visual child or another intermediate node is ignored for that object.
Do not scale a `CollisionShape2D` node to resize it. Change the shape resource's
size/radius/extents instead.

When using several shapes on one body, they form one compound collider and do
not collide with each other.

## 4. CharacterBody2D

`CharacterBody2D` is script-controlled. It detects collisions and affects
other bodies, but the physics engine does not apply gravity or friction to it.
Gameplay code must compute those effects.

Minimal platformer pattern:

```gdscript
extends CharacterBody2D

@export var speed := 250.0
@export var gravity := 980.0
@export var jump_velocity := -380.0

func _physics_process(delta: float) -> void:
	if not is_on_floor():
		velocity.y += gravity * delta

	if Input.is_action_just_pressed("jump") and is_on_floor():
		velocity.y = jump_velocity

	var direction := Input.get_axis("move_left", "move_right")
	if direction != 0.0:
		velocity.x = direction * speed
	else:
		velocity.x = move_toward(velocity.x, 0.0, speed)

	move_and_slide()
```

`move_and_slide()` uses the body's `velocity`, moves it, performs slide
collisions, and modifies `velocity` to reflect the resulting motion. Do not
multiply `velocity` by `delta` when calling `move_and_slide()`.

Important properties:

| Property | Meaning |
| --- | --- |
| `velocity` | Desired/current linear velocity in pixels per second. |
| `motion_mode` | `MOTION_MODE_GROUNDED` recognizes floor, wall, and ceiling; `MOTION_MODE_FLOATING` treats all contacts as walls and is suitable for top-down movement. |
| `up_direction` | Defines which direction is away from the floor. Default is `Vector2(0, -1)`. |
| `floor_max_angle` | Maximum contact angle classified as a floor, in radians. |
| `floor_stop_on_slope` | Prevents sliding down a slope while standing still when enabled. |
| `floor_snap_length` | Distance used to keep the body attached to sloped floors. |
| `wall_min_slide_angle` | Minimum angle for sliding along a wall/slope. |
| `max_slides` | Maximum slide-collision iterations per movement call. |
| `safe_margin` | Collision recovery margin used to detect near contacts. |
| `floor_constant_speed` | Keeps speed constant on slopes when enabled. |
| `slide_on_ceiling` | Controls whether upward motion slides along ceilings. |
| `platform_floor_layers` | Layers of moving platforms that can transfer floor motion. |
| `platform_wall_layers` | Layers of moving platforms that can transfer wall motion. |
| `platform_on_leave` | Controls how platform velocity is handled when leaving a platform. |

Use `is_on_floor()`, `is_on_wall()`, and `is_on_ceiling()` after movement.
`*_only()` variants report whether the last motion contacted only that category.
`get_floor_normal()` and `get_wall_normal()` provide contact normals after a
movement result exists.

For custom responses, use:

```gdscript
var collision := move_and_collide(velocity * delta)
if collision:
	velocity = velocity.bounce(collision.get_normal())
```

`move_and_collide()` receives a relative motion vector, stops at the first
collision, and returns `KinematicCollision2D` or `null`. It does not provide
the automatic slide response of `move_and_slide()`.

## 5. RigidBody2D

`RigidBody2D` is fully simulated. Apply forces, impulses, torques, or set
integration state rather than setting its transform every physics frame.

2D force and motion values use `Vector2`; torque and angular velocity are
scalar radians-based values:

```gdscript
extends RigidBody2D

func launch(direction: Vector2, impulse_strength: float) -> void:
	apply_central_impulse(direction.normalized() * impulse_strength)
```

Use:

- `apply_central_force()` for a force through the center;
- `apply_force(force, position)` for force at a position;
- `apply_central_impulse()` for an immediate linear impulse;
- `apply_impulse(impulse, position)` for an impulse that can add rotation;
- `apply_torque()` and `apply_torque_impulse()` for angular changes;
- `add_constant_*()` for forces/torques that persist until removed.

Important 2D properties include `mass`, `linear_velocity`,
`angular_velocity`, `gravity_scale`, `linear_damp`, `angular_damp`,
`lock_rotation`, `freeze`, `freeze_mode`, `can_sleep`, `sleeping`,
`continuous_cd`, `contact_monitor`, `max_contacts_reported`, and
`physics_material_override`.

`_integrate_forces(state: PhysicsDirectBodyState2D)` is the preferred callback
for direct control of the simulated state. `custom_integrator` changes whether
the default force integration is bypassed; enable it only intentionally.

Contact signals such as `body_entered` require `contact_monitor = true` and a
sufficient `max_contacts_reported`.

## 6. Area2D

`Area2D` detects `CollisionObject2D` overlaps and can override local 2D
gravity/damping or route audio. It does not provide solid collision response.

Common signals:

- `body_entered(body)`;
- `body_exited(body)`;
- `area_entered(area)`;
- `area_exited(area)`;
- `body_shape_entered(body_rid, body, body_shape_index, local_shape_index)`;
- `body_shape_exited(...)`;
- `area_shape_entered(...)`;
- `area_shape_exited(...)`.

Use `get_overlapping_bodies()` and `get_overlapping_areas()` only when
monitoring is enabled and remember that overlap lists describe the physics
state at the update boundary, not an arbitrary immediate geometric query.

Area override modes are:

- **Combine**: add this area's values to the current result;
- **Replace**: replace the result and stop considering lower-priority areas;
- **Combine-Replace**: combine, then stop lower-priority processing;
- **Replace-Combine**: replace the current result, then continue processing.

Higher-priority areas are processed first. Override-able properties include
gravity strength/direction and linear/angular damping. Point gravity uses the
area's point center and unit distance.

## 7. AnimatableBody2D

`AnimatableBody2D` inherits static-body behavior but is intended to be moved
manually by code or animation. The engine estimates its linear and angular
velocity and uses that motion to affect other bodies in its path.

Use it for moving platforms, doors, elevators, and similar objects that should
not be pushed by external forces. When animation drives the movement, process
the animation during physics when physics-frame synchronization is required.
Do not combine `sync_to_physics` animation movement with
`PhysicsBody2D.move_and_collide()` on the same body.

## 8. RayCast2D and ShapeCast2D

`RayCast2D` casts from its origin to local `target_position` and reports the
closest hit. It updates every physics frame and retains its result until the
next update.

Key properties:

- `enabled`;
- `target_position: Vector2`;
- `collision_mask`;
- `collide_with_bodies`;
- `collide_with_areas`;
- `exclude_parent`;
- `hit_from_inside`.

Useful methods:

- `is_colliding()`;
- `get_collider()`;
- `get_collider_rid()`;
- `get_collider_shape()`;
- `get_collision_point()`;
- `get_collision_normal()`;
- `force_raycast_update()`;
- `add_exception()`/`remove_exception()`.

`ShapeCast2D` sweeps a `Shape2D` through 2D space and is appropriate for
character clearance, melee volumes, and thick movement tests where one ray is
not sufficient. Use its collision-count and collision-result methods rather
than treating it as a solid body.

## 9. 2D direct-space queries

Inside `_physics_process()`:

```gdscript
func _physics_process(_delta: float) -> void:
	var space_state := get_world_2d().direct_space_state
	var query := PhysicsRayQueryParameters2D.create(
		global_position,
		global_position + Vector2.RIGHT * 500.0,
	)
	query.collision_mask = 1 << 0
	query.exclude = [self]
	var result := space_state.intersect_ray(query)
	if not result.is_empty():
		print(result.position, result.normal, result.collider)
```

2D query positions are in world coordinates. A ray result dictionary can
contain `position`, `normal`, `collider`, `collider_id`, `rid`, `shape`, and
`metadata`. Check for an empty dictionary before reading values.

Set `collide_with_areas = true` when a query should detect areas; body
collisions and area collisions are separately configurable.

## 10. 2D-only collision features

2D collision objects support one-way collision configuration on shape owners:

- one-way enabled/disabled;
- one-way direction;
- one-way collision margin.

Use one-way collision for platforms that should be passable from one side.
The direction is a `Vector2` and must agree with the platform's orientation.

2D `CollisionObject2D` also supports canvas-local mouse picking through
`input_pickable`, `_input_event`, `_mouse_enter`, `_mouse_exit`,
`_mouse_shape_enter`, and `_mouse_shape_exit`. This is input picking, not
physics contact detection.

## 11. 2D shapes and performance

For characters, prefer capsule, circle, or a small compound of primitives.
For static level geometry, use simplified concave polygons or tile-generated
collision. Avoid hundreds of tiny convex shapes for one moving object.

When tile edges cause bumps, use composite collision geometry. In Godot 4.5+
`TileMapLayer` can automatically create composite collision chunks; tune
Physics Quadrant Size for the tradeoff between update cost and smoothness.

## 12. 2D validation checklist

- The body has direct `CollisionShape2D`/`CollisionPolygon2D` children.
- Each shape uses an appropriate `Shape2D` resource.
- Character movement occurs in `_physics_process()`.
- `move_and_slide()` receives velocity in pixels per second and no `delta`.
- `move_and_collide()` receives motion multiplied by `delta`.
- `up_direction` and floor-angle settings match the game's orientation.
- Areas have monitoring enabled for required overlap signals.
- Rigid-body contact monitoring is enabled when contact signals are used.
- Query coordinates are global `Vector2` values.
- One-way direction and margin are configured intentionally.
- Objects are in the same canvas when they must collide.
