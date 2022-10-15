import os
import functools
import tensorflow as tf

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

            # If it's the best model yet, we need to make room for it
            if self.monitor_op(monitor_value, self.best):

                # If we already have N checkpoints, we delete the worst one to make room for the new one
                if len(self._checkpoints) >= self.n:
                    removed_checkpoint = self._checkpoints.pop(-1)
                    try:
                        os.remove(removed_checkpoint["path"])
                    except FileNotFoundError:
                        pass


                # We add the new checkpoint to the list
                filepath = self._get_file_path(epoch, batch=None, logs=logs)
                self._checkpoints.append({ "value": monitor_value, "path": filepath })
                self._checkpoints.sort(key=functools.cmp_to_key(lambda a, b: -1 if self.monitor_op(a["value"], b["value"]) else 1))

            self._save_model(epoch=epoch, batch=None, logs=logs)