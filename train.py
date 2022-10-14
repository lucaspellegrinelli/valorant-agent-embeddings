import pickle
from tensorboard.plugins.hparams import api as hp

from modeloptimizer import ModelOptimizer
from contextualmodel import contextual_autoencoder

with open("data/contextualdata/X_agents_train.pkl", "rb") as f:
    X_agents_train = pickle.load(f)

with open("data/contextualdata/X_maps_train.pkl", "rb") as f:
    X_maps_train = pickle.load(f)

with open("data/contextualdata/X_stats_train.pkl", "rb") as f:
    X_stats_train = pickle.load(f)

with open("data/contextualdata/y_agents_train.pkl", "rb") as f:
    y_agents_train = pickle.load(f)

with open("data/contextualdata/y_maps_train.pkl", "rb") as f:
    y_maps_train = pickle.load(f)

with open("data/contextualdata/y_stats_train.pkl", "rb") as f:
    y_stats_train = pickle.load(f)

with open("data/contextualdata/X_agents_test.pkl", "rb") as f:
    X_agents_test = pickle.load(f)

with open("data/contextualdata/X_maps_test.pkl", "rb") as f:
    X_maps_test = pickle.load(f)

with open("data/contextualdata/X_stats_test.pkl", "rb") as f:
    X_stats_test = pickle.load(f)

with open("data/contextualdata/y_agents_test.pkl", "rb") as f:
    y_agents_test = pickle.load(f)

with open("data/contextualdata/y_maps_test.pkl", "rb") as f:
    y_maps_test = pickle.load(f)

with open("data/contextualdata/y_stats_test.pkl", "rb") as f:
    y_stats_test = pickle.load(f)

hparams = [
    hp.HParam("input_processing_size", hp.IntInterval(32, 256)),
    hp.HParam("output_processing_size", hp.IntInterval(32, 256)),
    hp.HParam("layer_a_size", hp.IntInterval(32, 512)),
    hp.HParam("layer_b_size", hp.IntInterval(16, 256)),
    hp.HParam("latent_size", hp.IntInterval(8, 128)),
    hp.HParam("dropout", hp.RealInterval(0.1, 0.5)),
    hp.HParam("optimizer", hp.Discrete(["adam", "sgd", "rmsprop", "adagrad"])),
    hp.HParam("activation", hp.Discrete(["relu", "tanh", "elu", "selu"]))
]

optimizer = ModelOptimizer(
    factory=contextual_autoencoder,
    hyperparams=hparams,
    losses={ "agent": "categorical_crossentropy", "stat": "mse" },
    metrics={ "agent": "accuracy", "stat": "mse" },
    model_out_dir="models",
    tensorboard_log=True
)

while True:
    X_train = [X_agents_train, X_maps_train, X_stats_train]
    y_train = [y_agents_train, y_stats_train]
    X_test = [X_agents_test, X_maps_test, X_stats_test]
    y_test = [y_agents_test, y_stats_test]
    optimizer.run_iteration(X_train, y_train, X_test, y_test)