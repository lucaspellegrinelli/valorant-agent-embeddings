import pickle
import pandas as pd
import seaborn as sns
import tensorflow as tf
import matplotlib.pyplot as plt

from sklearn.decomposition import PCA

model_path = "models/model-1.3831-037-0.7071-0.4545.h5"

with open("data/contextualdata/X_agents_test.pkl", "rb") as f:
    X_agents = pickle.load(f)

with open("data/contextualdata/X_maps_test.pkl", "rb") as f:
    X_maps = pickle.load(f)

with open("data/contextualdata/X_stats_test.pkl", "rb") as f:
    X_stats = pickle.load(f)

with open("data/contextualdata/y_agents_test.pkl", "rb") as f:
    y_agents = pickle.load(f)

with open("auxmodels/agents_encoder.pkl", "rb") as f:
    agents_encoder = pickle.load(f)

with open("auxmodels/maps_encoder.pkl", "rb") as f:
    maps_encoder = pickle.load(f)

print(X_agents.shape)

ctx_model = tf.keras.models.load_model(model_path)
encoder_output = ctx_model.get_layer("latent").output
encoder = tf.keras.models.Model(inputs=ctx_model.input, outputs=encoder_output)

pca = PCA(n_components=2)
embeddings = encoder.predict([X_agents, X_maps, X_stats])
components = pca.fit_transform(embeddings)

df = pd.DataFrame(components, columns=["x", "y"])
df["map"] = maps_encoder.inverse_transform(X_maps)
df["agent"] = agents_encoder.inverse_transform(y_agents)

# df = df[df["agent"].isin(["Killjoy", "Jett", "Astra"])]

sns.scatterplot(data=df, x="x", y="y", hue="agent")
plt.show()