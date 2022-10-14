import pandas as pd
import seaborn as sns
import tensorflow as tf
import matplotlib.pyplot as plt

from sklearn.decomposition import PCA

from training.datasetfactory import DatasetFactory

model_path = "models/model-2.1692-042-0.6821-1.0761.h5"

dataset_factory = DatasetFactory(scrapped_comps_file="data/comps.jsonl")
_, ((agents_x, maps_x, stats_x), (agents_y, stats_y)) = dataset_factory.generate_dataset(as_tf_dataset=False)

ctx_model = tf.keras.models.load_model(model_path)
encoder_output = ctx_model.get_layer("latent").output
encoder = tf.keras.models.Model(inputs=ctx_model.input, outputs=encoder_output)

pca = PCA(n_components=2)
embeddings = encoder.predict([agents_x, maps_x, stats_x])
components = pca.fit_transform(embeddings)

df = pd.DataFrame(components, columns=["x", "y"])
df["map"] = dataset_factory.map_encoder.inverse_transform(maps_x)
df["agent"] = dataset_factory.agent_encoder.inverse_transform(agents_y)

df = df[df["agent"].isin(["Viper"])]

sns.scatterplot(data=df, x="x", y="y", hue="map")
plt.show()