import tensorflow as tf

def contextual_autoencoder(hparams, n_maps, n_agents, n_stats):
    input_maps = tf.keras.layers.Input(shape=(n_maps,))
    maps_x = tf.keras.layers.Dense(hparams["input_processing_size"], activation=hparams["activation"])(input_maps)
    maps_x = tf.keras.layers.BatchNormalization()(maps_x)

    input_agents = tf.keras.layers.Input(shape=(4, n_agents,))
    agents_x = tf.keras.layers.Flatten()(input_agents)
    agents_x = tf.keras.layers.Dense(hparams["input_processing_size"], activation=hparams["activation"])(agents_x)
    agents_x = tf.keras.layers.BatchNormalization()(agents_x)

    input_stats = tf.keras.layers.Input(shape=(4, n_stats,))
    stats_x = tf.keras.layers.Flatten()(input_stats)
    stats_x = tf.keras.layers.Dense(hparams["input_processing_size"], activation=hparams["activation"])(stats_x)
    stats_x = tf.keras.layers.BatchNormalization()(stats_x)

    x = tf.keras.layers.Concatenate()([agents_x, maps_x, stats_x])

    x = tf.keras.layers.Dense(hparams["layer_a_size"], activation=hparams["activation"])(x)
    x = tf.keras.layers.BatchNormalization()(x)
    x = tf.keras.layers.Dropout(0.2)(x)

    x = tf.keras.layers.Dense(hparams["layer_b_size"], activation=hparams["activation"])(x)
    x = tf.keras.layers.BatchNormalization()(x)
    x = tf.keras.layers.Dropout(0.2)(x)

    latent = tf.keras.layers.Dense(hparams["latent_size"], activation=hparams["activation"], name="latent")(x)

    x = tf.keras.layers.Dense(hparams["layer_b_size"], activation=hparams["activation"])(latent)
    x = tf.keras.layers.BatchNormalization()(x)
    x = tf.keras.layers.Dropout(0.2)(x)

    x = tf.keras.layers.Dense(hparams["layer_a_size"], activation=hparams["activation"])(x)
    x = tf.keras.layers.BatchNormalization()(x)
    x = tf.keras.layers.Dropout(0.2)(x)

    agent_output = tf.keras.layers.Dense(hparams["output_processing_size"], activation="softmax")(x)
    agent_output = tf.keras.layers.Dense(n_agents, activation="softmax", name="agent")(agent_output)

    stat_output = tf.keras.layers.Dense(hparams["output_processing_size"], activation="linear")(x)
    stat_output = tf.keras.layers.Dense(n_stats, activation="linear", name="stat")(stat_output)

    model = tf.keras.models.Model(
        inputs=[input_agents, input_maps, input_stats],
        outputs=[agent_output, stat_output]
    )

    return model