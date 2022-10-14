import json
import numpy as np
import tensorflow as tf

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder, StandardScaler

class DatasetFactory:
    """Class to load and generate the dataset"""

    AGENT_DATA = ["acs", "kills", "deaths", "assists", "adr", "fb", "fd"]

    def __init__(self, scrapped_comps_file: str):
        self.scrapped_comps_file = scrapped_comps_file

        self.agent_encoder = OneHotEncoder()
        self.map_encoder = OneHotEncoder()
        self.std_scaler = StandardScaler()

    def generate_dataset(self, batch_size: int, test_size: float = 0.2):
        """Generates the dataset"""

        # Loads and preprocesses the data
        agents, maps, stats = self._load_data()
        agents, maps, stats = self._preprocess_data(agents, maps, stats)
        
        # Splits the data into train and test
        agents_train, agents_test, maps_train, maps_test, stats_train, stats_test = train_test_split(agents, maps, stats, test_size=test_size, random_state=42)

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

        # Creates the datasets
        training_dataset = tf.data.Dataset.zip((
            tf.data.Dataset.from_tensor_slices((x_agents_train, x_maps_train, x_stats_train)),
            tf.data.Dataset.from_tensor_slices((y_agents_train, y_stats_train))
        ))

        test_dataset = tf.data.Dataset.zip((
            tf.data.Dataset.from_tensor_slices((x_agents_test, x_maps_test, x_stats_test)),
            tf.data.Dataset.from_tensor_slices((y_agents_test, y_stats_test))
        ))

        return training_dataset.batch(batch_size), test_dataset.batch(batch_size)

    def _load_data(self):
        all_agents_ohe = []
        all_maps_ohe = []
        all_stats = []

        with open(self.scrapped_comps_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
            for line in lines:
                data = json.loads(line)

                stats_a = [self._get_agent_data(agent) for agent in data["a_team"]]
                stats_b = [self._get_agent_data(agent) for agent in data["b_team"]]

                agents_a = [agent["agent"] for agent in data["a_team"]]
                agents_b = [agent["agent"] for agent in data["b_team"]]

                maps_a = [data["map"] for _ in range(5)]
                maps_b = [data["map"] for _ in range(5)]

                all_agents_ohe.append(agents_a)
                all_agents_ohe.append(agents_b)
                
                all_maps_ohe.append(maps_a)
                all_maps_ohe.append(maps_b)

                all_stats.append(stats_a)
                all_stats.append(stats_b)

        return np.array(all_agents_ohe), np.array(all_maps_ohe), np.array(all_stats)

    def _preprocess_data(self, agents: np.ndarray, maps: np.ndarray, stats: np.ndarray):
        orig_agents_shape = agents.shape
        orig_maps_shape = maps.shape
        orig_stats_shape = stats.shape

        # One-hot encodes the agents
        agents = self.agent_encoder.fit_transform(agents.reshape(-1, 1)).toarray()
        agents = agents.reshape(orig_agents_shape[0], orig_agents_shape[1], -1)

        # One-hot encodes the maps
        maps = self.map_encoder.fit_transform(maps.reshape(-1, 1)).toarray()
        maps = maps.reshape(orig_maps_shape[0], orig_maps_shape[1], -1)

        # Normalizes the stats
        stats = self.std_scaler.fit_transform(stats.reshape(-1, stats.shape[-1]))
        stats = stats.reshape(orig_stats_shape)
        return agents, maps, stats

    def _get_agent_data(self, agent_info: dict[str, float]):
        return [ agent_info[metric] for metric in self.AGENT_DATA ]