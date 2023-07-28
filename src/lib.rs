use std::marker::PhantomData;
use bevy::ecs::system::CommandQueue;
use bevy::gltf::GltfExtras;
use bevy::prelude::*;
use serde::de::DeserializeOwned;
use serde::Deserialize;

mod bbu_manager;

pub use bbu_manager::{BBUManager, BBUSceneSpawnedEvent, BBUSceneSpawnedEventWithId};

pub trait SceneId: Copy + Clone + Send + Sync + 'static {}

/// Id allows for different parsing logic to work on scenes if needed.
pub struct BBUPlugin<Id> {
    _phantom: PhantomData<Id>,
}

impl<Id> Default for BBUPlugin<Id> {
    fn default() -> Self {
        Self {
            _phantom: default(),
        }
    }
}

impl<Id: SceneId> Plugin for BBUPlugin<Id> {
    fn build(&self, app: &mut App) {
        app
            .add_event::<BBUSceneSpawnedEventWithId<Id>>()
            .init_resource::<BBUManager<Id>>()
            .add_systems(Update, inform_if_loaded_system::<Id>);
    }
}

fn inform_if_loaded_system<Id: SceneId>(
    mut bbu_manager: ResMut<BBUManager<Id>>,
    asset_server: Res<AssetServer>,
    writer: EventWriter<BBUSceneSpawnedEventWithId<Id>>,
) {
    bbu_manager.inform_if_loaded(&asset_server, writer);
}

#[derive(Deserialize, Clone, Copy, PartialEq, Default, Debug)]
struct BBUObjectData<Data> {
    bbu_object_data: Option<Data>,
}

#[derive(Deserialize, Clone, Copy, PartialEq, Default, Debug)]
pub struct CuboidData {
    pub cuboid: Vec3,
    pub offset: Vec3,
}

#[derive(Deserialize, Clone, Copy, PartialEq, Default, Debug)]
pub struct SphereData {
    radius: f32,
    offset: Vec3,
}

#[derive(Deserialize, Clone, Copy, PartialEq, Default, Debug)]
pub struct CapsuleData {
    radius: f32,
    height: f32,
    offset: Vec3,
    up_vector: Vec3,
}

/// All the required info for parsing scene extras and spawning scenes.
pub struct BBUScene<'a, Id> {
    pub id: Id,
    pub handle: &'a Handle<Scene>,
    scene: &'a mut Scene,
}

impl<'a, Id> BBUScene<'a, Id> {
    /// Parses scene extras using ``parser`` and applies changes to the scene world.
    pub fn parse<Data: DeserializeOwned, F>(
        &mut self,
        mut parser: F,
    ) where
        F: FnMut(&mut Commands, Entity, &Name, Result<Option<Data>, serde_json::Error>),
    {
        let mut command_queue = CommandQueue::default();

        let query = self.scene.world
            .query::<(Entity, &Name, &GltfExtras)>()
            .iter(&self.scene.world)
            .collect::<Vec<(Entity, &Name, &GltfExtras)>>();

        let mut commands = Commands::new(&mut command_queue, &self.scene.world);

        for (entity, name, extras) in query {
            let value = serde_json::from_str::<BBUObjectData<Data>>(extras.value.as_ref())
                .map(|data| data.bbu_object_data);
            parser(&mut commands, entity, name, value);
        }

        command_queue.apply(&mut self.scene.world)
    }
}
