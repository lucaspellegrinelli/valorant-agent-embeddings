from typing import Callable, Any

import os
import functools
import pandas as pd
import tensorflow as tf
from tensorboard.plugins.hparams import api as hp

class SaveBestNCheckpoints(tf.keras.callbacks.ModelCheckpoint):
    """Keras Callback that saves the best N checkpoints based on a given metric."""

    def __init__(self, n: int, filepath: str, monitor: str = "val_loss", verbose: int = 0, **kwargs):
        super().__init__(filepath=filepath, monitor=monitor, save_best_only=True, verbose=verbose, **kwargs)
        self.n = n
        self.filepath = filepath
        self._checkpoints = []

    def on_epoch_end(self, epoch, logs=None):
        self.epochs_since_last_save += 1

        if self.save_freq == "epoch":
            monitor_value = logs.get(self.monitor)

            if len(self._checkpoints) < self.n or any(self.monitor_op(monitor_value, cp["value"]) for cp in self._checkpoints):
                filepath = self._get_file_path(epoch, batch=None, logs=logs)

                self._checkpoints.append({ "value": monitor_value, "path": filepath })
                self._checkpoints.sort(key=functools.cmp_to_key(lambda a, b: -1 if self.monitor_op(a["value"], b["value"]) else 1))

                if len(self._checkpoints) > self.n:
                    removed_checkpoint = self._checkpoints.pop(-1)
                    os.remove(removed_checkpoint["path"])

            self._save_model(epoch=epoch, batch=None, logs=logs)

class ModelOptimizer:
    """Class responsible for optimizing the hyperparameters of a model"""

    def __init__(
        self,
        factory: Callable[[dict[str, Any]], tf.keras.Model],
        hyperparams: list[hp.HParam],
        losses: dict[str, str] | list[str],
        metrics: dict[str, str] | list[str],
        monitor: str = "val_loss",
        n_models: int = 5,
        early_stopping_patience: int = 10,
        reduce_lr_factor: float = 0.2,
        reduce_lr_patience: int = 10,
        tensorboard_log: bool = False,
        tensorboard_log_dir: str = "logs/hparam_tuning",
        model_out_dir: str = "",
        model_out_name: str = None,
        extra_callbacks: list[tf.keras.callbacks.Callback] = None
    ):
        self.model_factory = factory
        self.model_losses = losses
        self.model_metrics = metrics

        self.monitor = monitor
        self.n_models = n_models
        self.early_stopping_patience = early_stopping_patience
        self.reduce_lr_factor = reduce_lr_factor
        self.reduce_lr_patience = reduce_lr_patience
        self.tensorboard_log = tensorboard_log
        self.tensorboard_log_dir = tensorboard_log_dir
        self.model_out_dir = model_out_dir
        self.model_out_name = model_out_name
        self.extra_callbacks = extra_callbacks

        self._hp_metrics = []
        self._hp_params = hyperparams

        self._initialize()

        self._iteration_counter = 0

        self._default_callbacks = [
            SaveBestNCheckpoints(
                self.n_models,
                filepath=self._model_out_path,
                monitor=self.monitor,
                verbose=1
            ),
            tf.keras.callbacks.EarlyStopping(
                monitor=self.monitor,
                patience=self.early_stopping_patience,
                verbose=1
            ),
            tf.keras.callbacks.ReduceLROnPlateau(
                monitor=self.monitor,
                factor=self.reduce_lr_factor,
                patience=self.reduce_lr_patience
            )
        ]

    @property
    def _model_out_path(self) -> str:
        """Returns the path to the model output file"""
        return os.path.join(self.model_out_dir, self.model_out_name)

    def _initialize(self) -> None:
        """Initializes the metric list, file writer and model output name"""
        self._hp_metrics = self._get_hp_metrics()
        if self.tensorboard_log:
            with tf.summary.create_file_writer(self.tensorboard_log_dir).as_default():
                hp.hparams_config(hparams=self._hp_params, metrics=self._hp_metrics)

        if self.model_out_name is None:
            self.model_out_name = self._generate_model_out_name()

    def run_iteration(self, train_dataset: tf.data.Dataset, validation_dataset: tf.data.Dataset, run_name_prefix: str = "iteration") -> None:
        """Runs a single iteration of the hyperparameter optimization"""
        run_name = f"{run_name_prefix}-{self._iteration_counter}"
        run_path = os.path.join(self.tensorboard_log_dir, run_name)

        if self.tensorboard_log:
            with tf.summary.create_file_writer(run_path).as_default():
                # Fitting model with random hyperparameters
                best_metrics = self._fit_random_model(train_dataset, validation_dataset)

                # Logging the best metrics
                for metric in self._hp_metrics:
                    tf.summary.scalar(metric.name, best_metrics[metric.name], step=1)
        else:
            # Fitting model with random hyperparameters
            self._fit_random_model(train_dataset, validation_dataset)

    def _fit_random_model(self, train_dataset: tf.data.Dataset, validation_dataset: tf.data.Dataset) -> pd.Series:
        """Fits a model with random hyperparameters and returns the best metrics"""
        # Generating random hyperparameters
        hparams = self._get_random_hparams()
        hp.hparams(hparams)

        # Fitting model with random hyperparameters
        return self._fit_model(hparams, train_dataset, validation_dataset)

    def _fit_model(self, hparams: dict[hp.HParam, Any], train_dataset: tf.data.Dataset, validation_dataset: tf.data.Dataset) -> pd.Series:
        """Fits the model with the given hyperparameters and returns the best metrics"""
        # Generating hparams
        random_hparams_str = self._convert_hparams_dict(hparams)

        # Creating model with random hparams
        model = self.model_factory(random_hparams_str)

        # Compiling model
        model.compile(
            optimizer=random_hparams_str["optimizer"] if "optimizer" in random_hparams_str else "adam",
            loss=self.model_losses,
            metrics=self.model_metrics
        )

        # Fitting model
        history = model.fit(
            train_dataset,
            validation_data=validation_dataset,
            epochs=999,
            verbose=2,
            callbacks=self._get_callbacks(hparams)
        )

        # Returning the best row in the history
        history_df = pd.DataFrame(history.history)
        return history_df.iloc[-self.early_stopping_patience]

    def _get_callbacks(self, hparams: dict[hp.HParam, Any]) -> list[tf.keras.callbacks.Callback]:
        """Returns a list of callbacks to be used during model training"""
        new_callbacks = []
        if self.tensorboard_log:
            new_callbacks.extend([
                tf.keras.callbacks.TensorBoard(
                    log_dir=self.tensorboard_log_dir
                ),
                hp.KerasCallback(
                    writer=self.tensorboard_log_dir,
                    hparams=hparams
                )
            ])

        if self.extra_callbacks is not None:
            new_callbacks.extend(self.extra_callbacks)

        return self._default_callbacks + new_callbacks

    def _get_hp_metrics(self) -> list[hp.Metric]:
        """Returns a list of all metrics to be monitored in a list of hp.Metric"""
        hpmetrics = []
        if isinstance(self.model_metrics, list):
            for metric in self.model_metrics:
                val_metric = f"val_{metric}"
                hpmetrics.append(hp.Metric(metric, display_name=metric))
                hpmetrics.append(hp.Metric(val_metric, display_name=val_metric))
        else:
            for layer, metric in self.model_metrics.items():
                metric_str = f"{layer}_{metric}"
                val_metric_str = f"val_{layer}_{metric}"
                hpmetrics.append(hp.Metric(metric_str, display_name=metric_str))
                hpmetrics.append(hp.Metric(val_metric_str, display_name=val_metric_str))
        return hpmetrics

    def _get_random_hparams(self) -> dict[hp.HParam, Any]:
        """Returns a dictionary of random hyperparameters"""
        return { hparam: hparam.domain.sample_uniform() for hparam in self._hp_params }

    def _convert_hparams_dict(self, hparams: dict[hp.HParam, Any]) -> dict[str, Any]:
        """Converts a dictionary of hyperparameters from hp.HParam to str"""
        return { hparam.name: value for hparam, value in hparams.items() }

    def _generate_model_out_name(self, model_name_prefix: str = "model") -> str:
        """Generates the template for the model output name"""
        model_name = model_name_prefix + "-{val_loss:.4f}-{epoch:03d}"
        for hp_metric in self._hp_metrics:
            metric_name = hp_metric.as_proto().display_name
            if metric_name.startswith("val_") and metric_name != "val_loss":
                model_name += f"-{{{metric_name}:.4f}}"
        return f"{model_name}.h5"
