use std::time::Duration;
use bevy::prelude::*;
use bevy::prelude::shape::Cube;
use serde::Deserialize;
use bevy_blender_utils::{BBUManager, BBUPlugin, BBUSceneSpawnedEventWithId};

fn main() {
    App::new()
        .add_plugins(DefaultPlugins)
        // SceneId can be () unit-type if no identifier is needed.
        .add_plugin(BBUPlugin::<SceneId>::default())
        // Need to register type as scene requires it. I'm not sure if this has any implication
        // in this case.
        .register_type::<ShootingSquare>()
        .add_startup_system(build_camera_and_lights)
        .add_startup_system(load_assets)
        .add_system(spawn_bbu_assets)
        .add_system(periodic_spawn)
        .add_system(move_squares)
        .run();
}

// Parsed data, the format isn't opinionated; this is just how I prefer to use it.
// It is parsed from JSON like this:
// { "id": "shooting_square", "spawn_point": [0.0, 1.0, 0.0], "speed": 0.75 }
#[derive(Deserialize, Debug)]
#[serde(rename_all="snake_case", tag = "id")]
enum SceneObjects {
    ShootingSquare {
        spawn_point: Vec3,
        speed: f32,
    }
}

// Creating a scene id isn't required for this example. Still, it can categorize different scenes
// and have id-dependent logic on the same data.
#[derive(Copy, Clone)]
enum SceneId {
    MainScene
}

fn build_camera_and_lights(mut commands: Commands) {
    commands.spawn(Camera3dBundle {
        transform: Transform::from_translation(Vec3::new(0.0, 2.0, 4.0))
            .looking_at(Vec3::ZERO, Vec3::Y),
        ..default()
    });
    commands.spawn(SpotLightBundle {
        transform: Transform::from_translation(Vec3::new(0.0, 3.0, 5.0))
            .looking_at(Vec3::ZERO, Vec3::Y),
        spot_light: SpotLight {
            range: 20.0,
            ..default()
        },
        ..default()
    });
}

fn load_assets(
    mut bbu_manager: ResMut<BBUManager<SceneId>>,
    asset_server: Res<AssetServer>,
) {
    // Add a handle to our scene with the id we want to use. Id can be () unit-type.
    // .blend file and .gltf file can also be found on /assets.
    bbu_manager.manage(SceneId::MainScene, asset_server.load("shooting_squares.glb#Scene0"));
}

// The component that we are going to insert into the scene. It needs to derive reflect because of
// the Scene.
#[derive(Component, Reflect, Default)]
#[reflect(Component)]
struct ShootingSquare {
    spawn_point: Vec3,
    speed: f32,
}

#[derive(Component)]
struct ShootSpeed(f32);
#[derive(Component)]
struct SpawnedSquare;

// We get events for each scene that's loaded. We can do this from multiple systems because of how
// events work. But realistically speaking, it isn't good performance-wise, and it doesn't have any
// advantages that I know of.

fn spawn_bbu_assets(
    mut commands: Commands,
    mut reader: EventReader<BBUSceneSpawnedEventWithId<SceneId>>,
    mut scenes: ResMut<Assets<Scene>>,
) {
    for event in reader.iter() {
        // Parsing scenes and error handling. This skips error handling for the sake of the example.
        let Ok(mut scene) = event.parse(&mut scenes) else { continue; };
        let scene = &mut scene;

        match scene.id {
            SceneId::MainScene => scene.parse::<SceneObjects, _>(|commands, entity, _name, data| {
                // More error handling.
                let Ok(data) = data else { return; };
                // This isn't an error and can be used because not all scenes require extra data.
                // It can be used for handling other objects that have no data.
                let Some(data) = data else { return; };

                match data {
                    SceneObjects::ShootingSquare { spawn_point, speed } => {
                        commands
                            .entity(entity)
                            .insert(ShootingSquare {
                                spawn_point,
                                speed,
                            });
                    }
                }
            }),
        }

        // We updated our scene world; now time to spawn it. We could also save the handle of it and
        // spawn later, for stuff like loading screens.
        commands.spawn(SceneBundle {
            scene: scene.handle.clone(),
            ..default()
        });
    }
}

struct EachSecondTimer(Timer);

impl Default for EachSecondTimer {
    fn default() -> Self {
        Self(Timer::new(Duration::from_secs(1), TimerMode::Repeating))
    }
}

fn periodic_spawn(
    mut commands: Commands,
    query: Query<(&GlobalTransform, &ShootingSquare)>,
    time: Res<Time>,
    mut timer: Local<EachSecondTimer>,
    mut meshes: ResMut<Assets<Mesh>>,
    mut materials: ResMut<Assets<StandardMaterial>>,
) {
    if !timer.0.tick(time.delta()).just_finished() { return; }

    for (transform, shooting_square) in &query {
        let translation = transform.translation() + shooting_square.spawn_point;
        commands.spawn((
            PbrBundle {
                mesh: meshes.add(Cube::new(0.2).into()),
                transform: Transform::from_translation(translation),
                material: materials.add(Color::AZURE.into()),
                ..default()
            },
            SpawnedSquare,
            ShootSpeed(shooting_square.speed),
        ));
    }
}

fn move_squares(
    time: Res<Time>,
    mut query: Query<(&mut Transform, &ShootSpeed), With<SpawnedSquare>>,
) {
    for (mut transform, speed) in &mut query {
        transform.translation += Vec3::Y * time.delta_seconds() * speed.0;
    }
}