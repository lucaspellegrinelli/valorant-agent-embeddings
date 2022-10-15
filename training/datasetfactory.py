import json
import numpy as np
import tensorflow as tf

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from utils.consts import ALL_AGENTS, ALL_MAPS, ALL_STATS

class DatasetFactory:
    """Class to load and generate the dataset"""

    def __init__(self, scrapped_comps_file: str):
        self.scrapped_comps_file = scrapped_comps_file

        self.agent_encoder = OneHotEncoder()
        self.agent_encoder.fit(np.array(ALL_AGENTS).reshape(-1, 1))

        self.map_encoder = OneHotEncoder()
        self.map_encoder.fit(np.array(ALL_MAPS).reshape(-1, 1))

        self.std_scaler = StandardScaler()

    def generate_dataset(self, test_size: float = 0.2, as_tf_dataset: bool = True):
        """Generates the dataset"""

        # Loads and preprocesses the data
        agents, maps, stats, meta = self._load_data()
        agents, maps, stats = self._preprocess_data(agents, maps, stats)

        # Splits the data into train and test
        agents_train, agents_test, maps_train, maps_test, stats_train, stats_test, meta_train, meta_test = train_test_split(agents, maps, stats, meta, test_size=test_size, random_state=42)

        # Finds data shapes
        n_train = agents_train.shape[0] * agents_train.shape[1]
        n_test = agents_test.shape[0] * agents_test.shape[1]
        n_agents = agents_train.shape[-1]
        n_maps = maps_train.shape[-1]
        n_stats = stats_train.shape[-1]

        # Initializes all the arrays
        x_agents_train = np.zeros((n_train, 4, n_agents))
        x_maps_train = np.zeros((n_train, n_maps))
        x_stats_train = np.zeros((n_train, 4, n_stats))

        x_agents_test = np.zeros((n_test, 4, n_agents))
        x_maps_test = np.zeros((n_test, n_maps))
        x_stats_test = np.zeros((n_test, 4, n_stats))

        y_agents_train = np.zeros((n_train, n_agents))
        y_stats_train = np.zeros((n_train, n_stats))

        y_agents_test = np.zeros((n_test, n_agents))
        y_stats_test = np.zeros((n_test, n_stats))
        
        # Repeat meta data for each player
        flat_meta_train = []
        flat_meta_test = []

        # Fills the arrays
        for y_i in range(agents_train.shape[1]):
            train_idx_start = y_i * agents_train.shape[0]
            train_idx_end = (y_i + 1) * agents_train.shape[0]

            test_idx_start = y_i * agents_test.shape[0]
            test_idx_end = (y_i + 1) * agents_test.shape[0]

            all_xi = [j for j in range(agents_train.shape[1]) if j != y_i]

            x_agents_train[train_idx_start : train_idx_end, :, :] = agents_train[:, all_xi, :]
            x_maps_train[train_idx_start : train_idx_end, :] = maps_train[:, 0, :]
            x_stats_train[train_idx_start : train_idx_end, :, :] = stats_train[:, all_xi, :]
            x_agents_test[test_idx_start : test_idx_end, :, :] = agents_test[:, all_xi, :]
            x_maps_test[test_idx_start : test_idx_end, :] = maps_test[:, 0, :]
            x_stats_test[test_idx_start : test_idx_end, :, :] = stats_test[:, all_xi, :]

            y_agents_train[train_idx_start : train_idx_end, :] = agents_train[:, y_i, :]
            y_stats_train[train_idx_start : train_idx_end, :] = stats_train[:, y_i, :]
            y_agents_test[test_idx_start : test_idx_end, :] = agents_test[:, y_i, :]
            y_stats_test[test_idx_start : test_idx_end, :] = stats_test[:, y_i, :]

            flat_meta_train.extend(meta_train)
            flat_meta_test.extend(meta_test)

        # Creates the datasets
        if as_tf_dataset:
            training_dataset = tf.data.Dataset.zip((
                tf.data.Dataset.from_tensor_slices((x_agents_train, x_maps_train, x_stats_train)),
                tf.data.Dataset.from_tensor_slices((y_agents_train, y_stats_train))
            ))

            test_dataset = tf.data.Dataset.zip((
                tf.data.Dataset.from_tensor_slices((x_agents_test, x_maps_test, x_stats_test)),
                tf.data.Dataset.from_tensor_slices((y_agents_test, y_stats_test))
            ))
        else:
            training_dataset = (x_agents_train, x_maps_train, x_stats_train), (y_agents_train, y_stats_train)
            test_dataset = (x_agents_test, x_maps_test, x_stats_test), (y_agents_test, y_stats_test)

        return training_dataset, test_dataset, flat_meta_train, flat_meta_test

    def _load_data(self):
        all_agents_ohe = []
        all_maps_ohe = []
        all_stats = []
        all_meta = []

        with open(self.scrapped_comps_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
            for line in lines:
                data = json.loads(line)

                agents_a = [player["agent"] for player in data["team_a"]["players"]]
                agents_b = [player["agent"] for player in data["team_b"]["players"]]

                maps_a = [data["map_name"] for _ in range(5)]
                maps_b = [data["map_name"] for _ in range(5)]

                stats_a = [self._get_player_data(player) for player in data["team_a"]["players"]]
                stats_b = [self._get_player_data(player) for player in data["team_b"]["players"]]

                meta_a = { "match_id": data["match_id"], "game_id": data["game_id"], "team": data["team_a"]["team"], "score": data["team_a"]["score"] }
                meta_b = { "match_id": data["match_id"], "game_id": data["game_id"], "team": data["team_b"]["team"], "score": data["team_b"]["score"] }

                all_agents_ohe.append(agents_a)
                all_agents_ohe.append(agents_b)
                
                all_maps_ohe.append(maps_a)
                all_maps_ohe.append(maps_b)

                all_stats.append(stats_a)
                all_stats.append(stats_b)

                all_meta.append(meta_a)
                all_meta.append(meta_b)

        return np.array(all_agents_ohe), np.array(all_maps_ohe), np.array(all_stats), all_meta

    def _preprocess_data(self, agents: np.ndarray, maps: np.ndarray, stats: np.ndarray):
        orig_agents_shape = agents.shape
        orig_maps_shape = maps.shape
        orig_stats_shape = stats.shape

        # One-hot encodes the agents
        agents = self.agent_encoder.transform(agents.reshape(-1, 1)).toarray()
        agents = agents.reshape(orig_agents_shape[0], orig_agents_shape[1], -1)

        # One-hot encodes the maps
        maps = self.map_encoder.transform(maps.reshape(-1, 1)).toarray()
        maps = maps.reshape(orig_maps_shape[0], orig_maps_shape[1], -1)

        # Normalizes the stats
        stats = self.std_scaler.fit_transform(stats.reshape(-1, stats.shape[-1]))
        stats = stats.reshape(orig_stats_shape)
        return agents, maps, stats

    def _get_player_data(self, player_info: dict[str, dict[str, float]]):
        player_data = []
        for metric in ALL_STATS:
            player_data.append(player_info[metric]["atk"])
            player_data.append(player_info[metric]["def"])

        return player_data
        