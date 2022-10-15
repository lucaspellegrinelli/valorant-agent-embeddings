from tensorboard.plugins.hparams import api as hp

from training.datasetfactory import DatasetFactory
from training.modeloptimizer import ModelOptimizer
from training.contextualmodel import contextual_autoencoder

from utils.consts import ALL_AGENTS, ALL_MAPS, ALL_STATS

hparams = [
    hp.HParam("input_processing_size", hp.Discrete([16, 32, 64])),
    hp.HParam("output_processing_size", hp.Discrete([16, 32, 64])),
    hp.HParam("layer_a_size", hp.Discrete([128, 192, 256])),
    hp.HParam("layer_b_size", hp.Discrete([32, 64, 128])),
    hp.HParam("latent_size", hp.Discrete([16])),
    hp.HParam("dropout", hp.RealInterval(0.1, 0.33)),
    hp.HParam("optimizer", hp.Discrete(["adam", "rmsprop"])),
    hp.HParam("activation", hp.Discrete(["relu"]))
]

def ContextualAutoencoder(hparams):
    return contextual_autoencoder(hparams, len(ALL_MAPS), len(ALL_AGENTS), 2 * len(ALL_STATS))

optimizer = ModelOptimizer(
    factory=ContextualAutoencoder,
    hyperparams=hparams,
    losses={ "agent": "categorical_crossentropy", "stat": "mse" },
    metrics={ "agent": "accuracy", "stat": "mse" },
    model_out_dir="models",
    tensorboard_log=False
)

dataset_factory = DatasetFactory(scrapped_comps_file="data/comps.jsonl")
training_dataset, test_dataset, _, _ = dataset_factory.generate_dataset(as_tf_dataset=True)

while True:
    optimizer.run_iteration(training_dataset, test_dataset, batch_size=32)