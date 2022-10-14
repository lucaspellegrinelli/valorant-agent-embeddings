from tensorboard.plugins.hparams import api as hp

from training.datasetfactory import DatasetFactory
from training.modeloptimizer import ModelOptimizer
from training.contextualmodel import contextual_autoencoder

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

dataset_factory = DatasetFactory(scrapped_comps_file="data/comps.jsonl")
training_dataset, test_dataset = dataset_factory.generate_dataset(batch_size=32)

while True:
    optimizer.run_iteration(training_dataset, test_dataset)