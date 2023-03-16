use std::path::Path;
use bevy::asset::{AssetPath, LoadState};
use bevy::prelude::*;
use thiserror::Error;
use crate::BBUScene;

/// Tracks assets that are loading and sends an event when loaded.
#[derive(Resource)]
pub struct BBUManager<Id> {
    loading_assets: Vec<SceneWithId<Id>>,
}

impl<Id> Default for BBUManager<Id> {
    fn default() -> Self {
        Self {
            loading_assets: Vec::new(),
        }
    }
}

impl<Id: Copy + Clone + Event> BBUManager<Id> {
    /// Add scene handle to track.
    pub fn manage(&mut self, id: Id, handle: Handle<Scene>) -> Handle<Scene> {
        self.loading_assets.push(SceneWithId {
            id,
            handle: handle.clone(),
        });

        handle
    }

    /// See if the queue is loaded, useful with a state-based asset loading approach.
    pub fn is_loaded(&self) -> bool {
        self.loading_assets.is_empty()
    }

    pub(crate) fn inform_if_loaded(
        &mut self,
        asset_server: &AssetServer,
        mut writer: EventWriter<BBUSceneSpawnedEventWithId<Id>>,
    ) {

        let get_path = |handle: &Handle<Scene>| asset_server
            .get_handle_path(handle)
            .as_ref()
            .map(AssetPath::path)
            .and_then(Path::to_str)
            .map(ToString::to_string);

        self.loading_assets.retain(|SceneWithId { id, handle, .. }| {
            match asset_server.get_load_state(handle) {
                LoadState::Loading => true,
                LoadState::NotLoaded => true,
                LoadState::Unloaded => false,
                LoadState::Loaded => {
                    writer.send(BBUSceneSpawnedEventWithId::Loaded {
                        id: *id,
                        handle: handle.clone(),
                        path: get_path(handle),
                    });

                    false
                },
                LoadState::Failed => {
                    writer.send(BBUSceneSpawnedEventWithId::Failed {
                        path: get_path(handle),
                    });

                    false
                },
            }
        });

    }
}

struct SceneWithId<Id> {
    id: Id,
    handle: Handle<Scene>,
}

/// Event of a loaded scene asset can also be used with custom logic.
pub enum BBUSceneSpawnedEventWithId<Id> {
    Loaded {
        id: Id,
        handle: Handle<Scene>,
        path: Option<String>,
    },
    Failed {
        path: Option<String>,
    },
}

impl<Id: Copy + Clone + Event> BBUSceneSpawnedEventWithId<Id> {
    /// Convenience method for parsing events and getting scenes from them.
    pub fn parse<'a>(
        &'a self,
        scenes: &'a mut Assets<Scene>,
    ) -> Result<BBUScene<'a, Id>, BBUEventParseError> {
        let (id, handle, path) = match self {
            BBUSceneSpawnedEventWithId::Loaded { id, handle, path } => Ok((id, handle, path)),
            BBUSceneSpawnedEventWithId::Failed { path } => Err(
                path
                    .as_ref()
                    .map(ToOwned::to_owned)
                    .map(BBUEventParseError::AssetLoadFailed)
                    .unwrap_or(BBUEventParseError::AssetLoadFailedUnknownPath)
            ),
        }?;

        let scene = scenes.get_mut(handle)
            .ok_or_else(|| path
                .as_ref()
                .map(ToOwned::to_owned)
                .map(BBUEventParseError::NoSceneExist)
                .unwrap_or(BBUEventParseError::NoSceneExistUnknownPath)
            )?;

        Ok(BBUScene {
            id: *id,
            handle,
            scene,
        })
    }
}

#[derive(Error, Debug)]
pub enum BBUEventParseError {
    #[error("asset failed to load: path unknown")]
    AssetLoadFailedUnknownPath,
    #[error("asset failed to load: path `{0}`")]
    AssetLoadFailed(String),
    #[error("scene doesn't exist: path unknown")]
    NoSceneExistUnknownPath,
    #[error("scene doesn't exist: path `{0}`")]
    NoSceneExist(String),
}

/// Idless event alias for convenience.
pub type BBUSceneSpawnedEvent = BBUSceneSpawnedEventWithId<()>;
