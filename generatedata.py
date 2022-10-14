import json
import pickle
import numpy as np

from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.model_selection import train_test_split

def get_agent_data(agent_info):
    return [
        agent_info["acs"],
        agent_info["kills"],
        agent_info["deaths"],
        agent_info["assists"],
        agent_info["adr"],
        agent_info["fb"],
        agent_info["fd"]
    ]

all_agents_ohe = []
all_maps_ohe = []
all_stats = []

with open("data/comps.jsonl", "r", encoding="utf-8") as f:
    lines = f.readlines()
    for line in lines:
        data = json.loads(line)

        stats_a = [get_agent_data(agent) for agent in data["a_team"]]
        stats_b = [get_agent_data(agent) for agent in data["b_team"]]

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

all_agents_ohe = np.array(all_agents_ohe)
all_maps_ohe = np.array(all_maps_ohe)
all_stats = np.array(all_stats)

orig_agents_shape = all_agents_ohe.shape
orig_maps_shape = all_maps_ohe.shape

agents_encoder = OneHotEncoder()
all_agents_ohe = agents_encoder.fit_transform(all_agents_ohe.reshape(-1, 1)).toarray()
all_agents_ohe = all_agents_ohe.reshape(orig_agents_shape[0], orig_agents_shape[1], -1)

maps_encoder = OneHotEncoder()
all_maps_ohe = maps_encoder.fit_transform(all_maps_ohe.reshape(-1, 1)).toarray()
all_maps_ohe = all_maps_ohe.reshape(orig_maps_shape[0], orig_maps_shape[1], -1)

agents_train, agents_test, maps_train, maps_test, stats_train, stats_test = train_test_split(all_agents_ohe, all_maps_ohe, all_stats, test_size=0.2, random_state=42)

orig_train_shape = stats_train.shape
orig_test_shape = stats_test.shape

stats_train = stats_train.reshape(stats_train.shape[0] * stats_train.shape[1], stats_train.shape[2])
stats_test = stats_test.reshape(stats_test.shape[0] * stats_test.shape[1], stats_test.shape[2])

scaler = StandardScaler()
scaler.fit(np.concatenate((stats_train, stats_test), axis=0))

stats_train = scaler.transform(stats_train)
stats_test = scaler.transform(stats_test)

stats_train = stats_train.reshape(orig_train_shape)
stats_test = stats_test.reshape(orig_test_shape)

n_train = agents_train.shape[0] * agents_train.shape[1]
n_test = agents_test.shape[0] * agents_test.shape[1]

X_agents_train = np.zeros((n_train, 4, 19))
X_maps_train = np.zeros((n_train, 8))
X_stats_train = np.zeros((n_train, 4, 7))

X_agents_test = np.zeros((n_test, 4, 19))
X_maps_test = np.zeros((n_test, 8))
X_stats_test = np.zeros((n_test, 4, 7))

y_agents_train = np.zeros((n_train, 19))
y_maps_train = np.zeros((n_train, 8))
y_stats_train = np.zeros((n_train, 7))

y_agents_test = np.zeros((n_test, 19))
y_maps_test = np.zeros((n_test, 8))
y_stats_test = np.zeros((n_test, 7))

for y_i in range(agents_train.shape[1]):
    train_idx_start = y_i * agents_train.shape[0]
    train_idx_end = (y_i + 1) * agents_train.shape[0]

    test_idx_start = y_i * agents_test.shape[0]
    test_idx_end = (y_i + 1) * agents_test.shape[0]

    all_X_i = [j for j in range(agents_train.shape[1]) if j != y_i]

    X_agents_train[train_idx_start : train_idx_end, :, :] = agents_train[:, all_X_i, :]
    X_maps_train[train_idx_start : train_idx_end, :] = maps_train[:, 0, :]
    X_stats_train[train_idx_start : train_idx_end, :, :] = stats_train[:, all_X_i, :]
    X_agents_test[test_idx_start : test_idx_end, :, :] = agents_test[:, all_X_i, :]
    X_maps_test[test_idx_start : test_idx_end, :] = maps_test[:, 0, :]
    X_stats_test[test_idx_start : test_idx_end, :, :] = stats_test[:, all_X_i, :]

    y_agents_train[train_idx_start : train_idx_end, :] = agents_train[:, y_i, :]
    y_maps_train[train_idx_start : train_idx_end, :] = maps_train[:, 0, :]
    y_stats_train[train_idx_start : train_idx_end, :] = stats_train[:, y_i, :]
    y_agents_test[test_idx_start : test_idx_end, :] = agents_test[:, y_i, :]
    y_maps_test[test_idx_start : test_idx_end, :] = maps_test[:, 0, :]
    y_stats_test[test_idx_start : test_idx_end, :] = stats_test[:, y_i, :]

with open("auxmodels/agents_encoder.pkl", "wb") as f:\
    pickle.dump(agents_encoder, f)

with open("auxmodels/maps_encoder.pkl", "wb") as f:
    pickle.dump(maps_encoder, f)

with open("auxmodels/scaler.pkl", "wb") as f:
    pickle.dump(scaler, f)

with open("data/contextualdata/X_agents_train.pkl", "wb") as f:
    pickle.dump(X_agents_train, f)

with open("data/contextualdata/X_maps_train.pkl", "wb") as f:
    pickle.dump(X_maps_train, f)

with open("data/contextualdata/X_stats_train.pkl", "wb") as f:
    pickle.dump(X_stats_train, f)

with open("data/contextualdata/X_agents_test.pkl", "wb") as f:
    pickle.dump(X_agents_test, f)

with open("data/contextualdata/X_maps_test.pkl", "wb") as f:
    pickle.dump(X_maps_test, f)

with open("data/contextualdata/X_stats_test.pkl", "wb") as f:
    pickle.dump(X_stats_test, f)

with open("data/contextualdata/y_agents_train.pkl", "wb") as f:
    pickle.dump(y_agents_train, f)

with open("data/contextualdata/y_maps_train.pkl", "wb") as f:
    pickle.dump(y_maps_train, f)

with open("data/contextualdata/y_stats_train.pkl", "wb") as f:
    pickle.dump(y_stats_train, f)

with open("data/contextualdata/y_agents_test.pkl", "wb") as f:
    pickle.dump(y_agents_test, f)

with open("data/contextualdata/y_maps_test.pkl", "wb") as f:
    pickle.dump(y_maps_test, f)

with open("data/contextualdata/y_stats_test.pkl", "wb") as f:
    pickle.dump(y_stats_test, f)
