import pandas as pd
import seaborn as sns
import tensorflow as tf
import matplotlib.pyplot as plt

from sklearn.decomposition import PCA

from training.datasetfactory import DatasetFactory

model_path = "models/model-1.9646-044-0.6771-0.8939.h5"

dataset_factory = DatasetFactory(scrapped_comps_file="data/comps.jsonl")
test_ds, test_ds, train_meta, test_meta = dataset_factory.generate_dataset(as_tf_dataset=False)
(agents_x, maps_x, stats_x), (agents_y, stats_y) = test_ds

ctx_model = tf.keras.models.load_model(model_path)
encoder_output = ctx_model.get_layer("latent").output
encoder = tf.keras.models.Model(inputs=ctx_model.input, outputs=encoder_output)

pca = PCA(n_components=2)
embeddings = encoder.predict([agents_x, maps_x, stats_x])
components = pca.fit_transform(embeddings)

df = pd.DataFrame(components, columns=["x", "y"])
df["map"] = dataset_factory.map_encoder.inverse_transform(maps_x)
df["agent"] = dataset_factory.agent_encoder.inverse_transform(agents_y)
df = pd.concat([df, pd.DataFrame(test_meta)], axis=1)

count_df = df.groupby("team").size().reset_index(name="count")
popular_teams = count_df[count_df["count"] > 5]["team"].values

df = df[df["team"].isin(popular_teams)]
df["score"] = df["score"].astype(int)

sns.scatterplot(data=df, x="x", y="y", s=5)

selected_teams = ["Team Liquid", "OpTic Gaming", "LOUD", "XSET", "FNATIC", "DRX", "Leviatán", "FunPlus Phoenix"]
# selected_teams = ["Leviatán"]
df = df[df["team"].isin(selected_teams)]
# df = df.groupby(["team", "map"]).mean().reset_index()

df = df[df["map"] == "Fracture"]
print(df.head(15))

sns.scatterplot(data=df, x="x", y="y", hue="team", s=100)
plt.show()